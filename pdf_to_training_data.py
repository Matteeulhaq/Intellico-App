#!/usr/bin/env python3
"""
PDF to Training Data Converter
A single file solution to convert PDF research papers into training-ready metadata
"""

import os
import json
import re
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFToTrainingData:
    def __init__(self, pdf_directory: str, output_directory: str = "./training_data"):
        self.pdf_directory = pdf_directory
        self.output_directory = output_directory
        self.processed_papers = []
        
        # Create output directories
        os.makedirs(output_directory, exist_ok=True)
        os.makedirs(f"{output_directory}/processed_papers", exist_ok=True)
        os.makedirs(f"{output_directory}/training_datasets", exist_ok=True)
        os.makedirs(f"{output_directory}/metadata", exist_ok=True)
    
    def extract_text_from_pdf_simple(self, pdf_path: str) -> Dict[str, Any]:
        """
        Simple PDF text extraction without external dependencies
        This is a fallback method that works with basic Python
        """
        try:
            # Try to use PyMuPDF if available
            import fitz
            doc = fitz.open(pdf_path)
            text_content = ""
            metadata = {}
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text_content += page.get_text()
                
                if page_num == 0:
                    metadata = doc.metadata
            
            doc.close()
            
            return {
                "text": text_content,
                "metadata": metadata,
                "page_count": page_count,
                "extraction_method": "pymupdf"
            }
            
        except ImportError:
            # Fallback: try pdfplumber
            try:
                import pdfplumber
                text_content = ""
                metadata = {}
                
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
                    
                    metadata = pdf.metadata or {}
                
                return {
                    "text": text_content,
                    "metadata": metadata,
                    "page_count": len(pdf.pages),
                    "extraction_method": "pdfplumber"
                }
                
            except ImportError:
                # Final fallback: basic file reading (limited functionality)
                logger.warning(f"PDF processing libraries not available. Using basic text extraction for {pdf_path}")
                return {
                    "text": f"[PDF file: {os.path.basename(pdf_path)} - Text extraction requires PyMuPDF or pdfplumber]",
                    "metadata": {"title": os.path.basename(pdf_path)},
                    "page_count": 1,
                    "extraction_method": "basic"
                }
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\']', ' ', text)
        
        # Remove page numbers and headers/footers
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections based on actual headings found in the PDF"""
        sections = {}
        
        # First try to extract using specific patterns for common sections
        sections = self._extract_common_sections(text)
        
        # If we found sections, return them
        if sections:
            return sections
        
        # Fallback: Find all potential section headings using multiple patterns
        heading_patterns = [
            # Numbered headings: "1. Introduction", "2. Methods", etc.
            r'^\s*(\d+(?:\.\d+)*)\s+([^\n]+?)\s*$',
            # Unnumbered headings: "Introduction", "Methods", etc.
            r'^\s*([A-Z][A-Za-z\s]+?)\s*$',
            # Headings with colons: "Introduction:", "Methods:", etc.
            r'^\s*([A-Z][A-Za-z\s]+?)\s*:\s*$',
            # All caps headings: "INTRODUCTION", "METHODS", etc.
            r'^\s*([A-Z][A-Z\s]+?)\s*$',
            # Headings with special formatting
            r'^\s*([A-Z][A-Za-z\s]+?)\s*[-–—]\s*$'
        ]
        
        # Find all potential headings
        headings = []
        for pattern in heading_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                heading_text = match.group(1).strip()
                start_pos = match.start()
                
                # Filter out common false positives
                if self._is_valid_heading(heading_text):
                    headings.append({
                        'text': heading_text,
                        'position': start_pos,
                        'original_match': match.group(0).strip()
                    })
        
        # Remove duplicates and sort by position
        seen_positions = set()
        unique_headings = []
        for heading in headings:
            if heading['position'] not in seen_positions:
                seen_positions.add(heading['position'])
                unique_headings.append(heading)
        
        # Sort by position in text
        unique_headings.sort(key=lambda x: x['position'])
        
        # Extract content for each section
        for i, heading in enumerate(unique_headings):
            section_name = self._normalize_heading(heading['text'])
            start_pos = heading['position']
            
            # Find end position (next heading or end of text)
            if i < len(unique_headings) - 1:
                end_pos = unique_headings[i + 1]['position']
            else:
                end_pos = len(text)
            
            # Extract content
            content = text[start_pos:end_pos].strip()
            
            # Clean up the content
            lines = content.split('\n')
            if lines and len(lines) > 1:
                # Remove the heading line itself
                first_line = lines[0].strip()
                if first_line.lower() in [heading['original_match'].lower(), heading['text'].lower()]:
                    content = '\n'.join(lines[1:]).strip()
            
            # Clean up formatting
            content = re.sub(r'\n+', ' ', content)  # Replace multiple newlines with space
            content = re.sub(r'\s+', ' ', content)  # Replace multiple spaces with single space
            content = content.strip()
            
            # Only keep substantial content
            if content and len(content) > 50:
                sections[section_name] = content
        
        return sections
    
    def _is_valid_heading(self, heading_text: str) -> bool:
        """Check if a text looks like a valid section heading"""
        heading_lower = heading_text.lower().strip()
        
        # Must be at least 3 characters
        if len(heading_text) < 3:
            return False
        
        # Must not be too long (likely not a heading)
        if len(heading_text) > 100:
            return False
        
        # Common false positives to exclude
        false_positives = {
            'page', 'figure', 'table', 'fig', 'tab', 'doi', 'http', 'www',
            'copyright', 'all rights reserved', 'published by', 'journal',
            'volume', 'issue', 'pp', 'pages', 'doi:', 'http:', 'www.',
            'corresponding author', 'email', 'phone', 'fax', 'address',
            'received', 'accepted', 'revised', 'submitted', 'manuscript',
            'keywords', 'author', 'authors', 'affiliation',
            'institution', 'university', 'college', 'department', 'center',
            'laboratory', 'lab', 'research', 'study', 'investigation',
            'analysis', 'evaluation', 'assessment', 'examination', 'funding', 'support', 'grants', 'conflict',
            'disclosure', 'competing', 'interests', 'ethics', 'approval',
            'consent', 'permission', 'license', 'rights', 'reserved'
        }
        
        return heading_lower not in false_positives
    
    def _normalize_heading(self, heading_text: str) -> str:
        """Normalize heading text to standard section names"""
        heading_lower = heading_text.lower().strip()
        
        # Map common variations to standard names
        heading_mappings = {
            'abstract': 'abstract',
            'summary': 'abstract',
            'introduction': 'introduction',
            'background': 'introduction',
            'overview': 'introduction',
            'problem statement': 'introduction',
            'methodology': 'methodology',
            'methods': 'methodology',
            'approach': 'methodology',
            'experimental setup': 'methodology',
            'materials and methods': 'methodology',
            'results': 'results',
            'findings': 'results',
            'outcomes': 'results',
            'data': 'results',
            'experimental results': 'results',
            'discussion': 'discussion',
            'analysis': 'discussion',
            'interpretation': 'discussion',
            'implications': 'discussion',
            'conclusion': 'conclusion',
            'summary': 'conclusion',
            'final remarks': 'conclusion',
            'concluding remarks': 'conclusion',
            'references': 'references',
            'bibliography': 'references',
            'citations': 'references'
        }
        
        # Check for exact matches first
        if heading_lower in heading_mappings:
            return heading_mappings[heading_lower]
        
        # Check for partial matches
        for key, value in heading_mappings.items():
            if key in heading_lower or heading_lower in key:
                return value
        
        # Return original heading if no mapping found
        return heading_text.lower().replace(' ', '_')
    
    def _extract_common_sections(self, text: str) -> Dict[str, str]:
        """Extract common sections using specific patterns"""
        sections = {}
        
        # More robust patterns for common sections that handle various text formats
        section_patterns = {
            "abstract": [
                # Pattern 1: Abstract followed by Background/Introduction
                r'(?i)Abstract\s+(.*?)(?=\s+(?:Background|Introduction|Methods|1\.|Keywords|Key\s+words))',
                # Pattern 2: Abstract with colon
                r'(?i)Abstract\s*:\s*(.*?)(?=\s+(?:Background|Introduction|Methods|1\.|Keywords|Key\s+words))',
                # Pattern 3: Abstract at start of text
                r'(?i)^.*?Abstract\s+(.*?)(?=\s+(?:Background|Introduction|Methods|1\.|Keywords|Key\s+words))',
                # Pattern 4: Abstract with Summary as alternative
                r'(?i)(?:Abstract|Summary)\s+(.*?)(?=\s+(?:Background|Introduction|Methods|1\.|Keywords|Key\s+words))',
                # Pattern 5: More flexible abstract pattern
                r'(?i)Abstract\s+(.*?)(?=\s+(?:Background|Introduction|Methods|Results|Discussion|Conclusion|References|1\.|2\.|3\.|4\.|5\.))'
            ],
            "introduction": [
                # Pattern 1: Introduction followed by Methods
                r'(?i)Introduction\s+(.*?)(?=\s+(?:Methods|Methodology|Results|2\.|Approach|Experimental))',
                # Pattern 2: Background as introduction
                r'(?i)Background\s+(.*?)(?=\s+(?:Methods|Methodology|Results|2\.|Approach|Experimental))',
                # Pattern 3: Introduction with colon
                r'(?i)Introduction\s*:\s*(.*?)(?=\s+(?:Methods|Methodology|Results|2\.|Approach|Experimental))',
                # Pattern 4: Background with colon
                r'(?i)Background\s*:\s*(.*?)(?=\s+(?:Methods|Methodology|Results|2\.|Approach|Experimental))',
                # Pattern 5: More flexible introduction pattern
                r'(?i)(?:Introduction|Background|Overview)\s+(.*?)(?=\s+(?:Methods|Methodology|Results|Discussion|Conclusion|References|2\.|3\.|4\.|5\.))'
            ],
            "methodology": [
                # Pattern 1: Methods followed by Results
                r'(?i)Methods\s+(.*?)(?=\s+(?:Results|Findings|Discussion|3\.|Outcomes|Data))',
                # Pattern 2: Methodology followed by Results
                r'(?i)Methodology\s+(.*?)(?=\s+(?:Results|Findings|Discussion|3\.|Outcomes|Data))',
                # Pattern 3: Methods with colon
                r'(?i)Methods\s*:\s*(.*?)(?=\s+(?:Results|Findings|Discussion|3\.|Outcomes|Data))',
                # Pattern 4: Materials and Methods
                r'(?i)Materials\s+and\s+Methods\s+(.*?)(?=\s+(?:Results|Findings|Discussion|3\.|Outcomes|Data))',
                # Pattern 5: More flexible methods pattern
                r'(?i)(?:Methods|Methodology|Approach|Materials\s+and\s+Methods)\s+(.*?)(?=\s+(?:Results|Findings|Discussion|Conclusion|References|3\.|4\.|5\.))'
            ],
            "results": [
                # Pattern 1: Results followed by Discussion
                r'(?i)Results\s+(.*?)(?=\s+(?:Discussion|Analysis|Conclusion|4\.|Interpretation))',
                # Pattern 2: Findings as results
                r'(?i)Findings\s+(.*?)(?=\s+(?:Discussion|Analysis|Conclusion|4\.|Interpretation))',
                # Pattern 3: Results with colon
                r'(?i)Results\s*:\s*(.*?)(?=\s+(?:Discussion|Analysis|Conclusion|4\.|Interpretation))',
                # Pattern 4: More flexible results pattern
                r'(?i)(?:Results|Findings|Outcomes|Data|Experimental\s+Results)\s+(.*?)(?=\s+(?:Discussion|Analysis|Conclusion|References|4\.|5\.))'
            ],
            "discussion": [
                # Pattern 1: Discussion followed by Conclusion
                r'(?i)Discussion\s+(.*?)(?=\s+(?:Conclusion|Summary|References|5\.|Future\s+Work))',
                # Pattern 2: Analysis as discussion
                r'(?i)Analysis\s+(.*?)(?=\s+(?:Conclusion|Summary|References|5\.|Future\s+Work))',
                # Pattern 3: Discussion with colon
                r'(?i)Discussion\s*:\s*(.*?)(?=\s+(?:Conclusion|Summary|References|5\.|Future\s+Work))',
                # Pattern 4: More flexible discussion pattern
                r'(?i)(?:Discussion|Analysis|Interpretation|Implications)\s+(.*?)(?=\s+(?:Conclusion|Summary|References|5\.))'
            ],
            "conclusion": [
                # Pattern 1: Conclusion followed by References
                r'(?i)Conclusion\s+(.*?)(?=\s+(?:References|Bibliography|Acknowledgments|Appendix))',
                # Pattern 2: Summary as conclusion
                r'(?i)Summary\s+(.*?)(?=\s+(?:References|Bibliography|Acknowledgments|Appendix))',
                # Pattern 3: Conclusion with colon
                r'(?i)Conclusion\s*:\s*(.*?)(?=\s+(?:References|Bibliography|Acknowledgments|Appendix))',
                # Pattern 4: More flexible conclusion pattern
                r'(?i)(?:Conclusion|Summary|Final\s+Remarks|Concluding\s+Remarks)\s+(.*?)(?=\s+(?:References|Bibliography|Acknowledgments|Appendix))'
            ],
            "references": [
                # Pattern 1: References at end of text
                r'(?i)References\s+(.*?)$',
                # Pattern 2: Bibliography as references
                r'(?i)Bibliography\s+(.*?)$',
                # Pattern 3: References with colon
                r'(?i)References\s*:\s*(.*?)$',
                # Pattern 4: References followed by acknowledgments
                r'(?i)References\s+(.*?)(?=\s+(?:Acknowledgments|Acknowledgements|Appendix))',
                # Pattern 5: More flexible references pattern
                r'(?i)(?:References|Bibliography|Citations)\s+(.*?)(?=\s+(?:Acknowledgments|Acknowledgements|Appendix)|$)'
            ]
        }
        
        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    section_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    cleaned_text = self.clean_text(section_text)
                    if cleaned_text and len(cleaned_text) > 50:
                        sections[section_name] = cleaned_text
                        break  # Use first successful match
        
        return sections
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text"""
        # Simple keyword extraction based on frequency and importance
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Common stop words to exclude
        stop_words = {
            'this', 'that', 'with', 'from', 'they', 'been', 'have', 'were', 'said', 'each',
            'which', 'their', 'time', 'will', 'about', 'there', 'could', 'other', 'after',
            'first', 'well', 'also', 'where', 'much', 'some', 'very', 'when', 'here',
            'through', 'being', 'than', 'only', 'over', 'think', 'may', 'say', 'use',
            'many', 'these', 'into', 'more', 'has', 'had', 'but', 'not', 'what', 'all',
            'were', 'when', 'your', 'can', 'said', 'there', 'each', 'which', 'she',
            'do', 'how', 'their', 'if', 'will', 'up', 'other', 'about', 'out', 'many',
            'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like',
            'into', 'him', 'time', 'has', 'two', 'more', 'go', 'no', 'way', 'could',
            'my', 'than', 'first', 'been', 'call', 'who', 'its', 'now', 'find', 'long',
            'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part'
        }
        
        # Count word frequency
        word_count = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_count[word] = word_count.get(word, 0) + 1
        
        # Return top keywords
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:20] if count > 1]
    
    def extract_metadata(self, text: str, filename: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from text"""
        # Extract potential title (first line or before abstract)
        title_match = re.search(r'^([^\n]+)', text)
        title = title_match.group(1).strip() if title_match else filename.replace('.pdf', '')
        
        # Extract potential authors (look for common patterns)
        authors = []
        author_patterns = [
            r'(?i)(?:authors?|by)\s*:?\s*([^\n]+)',
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+\s+et\s+al\.?)'
        ]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, text[:1000])  # Search first 1000 chars
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if len(match.strip()) > 5 and len(match.strip()) < 100:
                    authors.append(match.strip())
        
        # Extract potential publication year
        year_matches = re.findall(r'\b(19|20)\d{2}\b', text)
        publication_year = max(year_matches) if year_matches else None
        
        # Extract potential journal/conference
        journal_patterns = [
            r'(?i)(?:published\s+in|journal|conference)\s*:?\s*([^\n]+)',
            r'(?i)(?:proceedings\s+of|proceedings)\s+([^\n]+)',
            r'(?i)([A-Z][a-z]+\s+(?:Journal|Conference|Proceedings))'
        ]
        
        journal = None
        for pattern in journal_patterns:
            match = re.search(pattern, text[:2000])
            if match:
                journal = match.group(1).strip()
                break
        
        return {
            "title": title,
            "authors": authors[:5],  # Limit to first 5 authors
            "publication_year": publication_year,
            "journal": journal,
            "filename": filename,
            "word_count": len(text.split()),
            "char_count": len(text),
            "keywords": self.extract_keywords(text)
        }
    
    def create_training_datasets(self) -> Dict[str, Any]:
        """Create various training datasets from processed papers"""
        datasets = {
            "classification": {
                "description": "Text classification dataset for section identification",
                "data": []
            },
            "summarization": {
                "description": "Text summarization dataset (full text to abstract)",
                "data": []
            },
            "keyword_extraction": {
                "description": "Keyword extraction dataset",
                "data": []
            },
            "metadata_extraction": {
                "description": "Metadata extraction dataset",
                "data": []
            }
        }
        
        for paper in self.processed_papers:
            if paper.get("status") != "success":
                continue
                
            paper_id = paper["paper_id"]
            sections = paper.get("sections", {})
            full_text = paper.get("full_text", "")
            metadata = paper.get("metadata", {})
            
            # Classification dataset
            for section_name, section_text in sections.items():
                if section_text.strip():
                    datasets["classification"]["data"].append({
                        "text": section_text,
                        "label": section_name,
                        "paper_id": paper_id,
                        "word_count": len(section_text.split())
                    })
            
            # Summarization dataset
            abstract = sections.get("abstract", "")
            if abstract and full_text and len(full_text) > 500:
                datasets["summarization"]["data"].append({
                    "text": full_text[:2000],  # Limit input length
                    "summary": abstract,
                    "paper_id": paper_id
                })
            
            # Keyword extraction dataset
            if metadata.get("keywords"):
                datasets["keyword_extraction"]["data"].append({
                    "text": full_text[:1000],  # First 1000 chars
                    "keywords": metadata["keywords"],
                    "paper_id": paper_id
                })
            
            # Metadata extraction dataset
            datasets["metadata_extraction"]["data"].append({
                "text": full_text[:2000],
                "title": metadata.get("title", ""),
                "authors": metadata.get("authors", []),
                "publication_year": metadata.get("publication_year"),
                "journal": metadata.get("journal", ""),
                "paper_id": paper_id
            })
        
        return datasets
    
    def process_single_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process a single PDF file"""
        filename = os.path.basename(pdf_path)
        paper_id = os.path.splitext(filename)[0]
        
        logger.info(f"Processing: {filename}")
        
        try:
            # Extract text
            extraction_result = self.extract_text_from_pdf_simple(pdf_path)
            
            if "error" in extraction_result:
                return {
                    "paper_id": paper_id,
                    "filename": filename,
                    "status": "error",
                    "error": extraction_result["error"]
                }
            
            # Clean text
            cleaned_text = self.clean_text(extraction_result["text"])
            
            # Extract sections
            sections = self.extract_sections(cleaned_text)
            
            # Extract metadata
            metadata = self.extract_metadata(cleaned_text, filename)
            
            # Create processed document
            processed_doc = {
                "paper_id": paper_id,
                "filename": filename,
                "processed_at": datetime.now().isoformat(),
                "extraction_method": extraction_result["extraction_method"],
                "page_count": extraction_result["page_count"],
                "full_text": cleaned_text,
                "sections": sections,
                "metadata": metadata,
                "word_count": len(cleaned_text.split()),
                "char_count": len(cleaned_text),
                "status": "success"
            }
            
            # Save individual processed paper
            output_path = f"{self.output_directory}/processed_papers/{paper_id}_processed.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_doc, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Processed: {filename} ({processed_doc['word_count']} words)")
            return processed_doc
            
        except Exception as e:
            logger.error(f"❌ Error processing {filename}: {str(e)}")
            return {
                "paper_id": paper_id,
                "filename": filename,
                "status": "error",
                "error": str(e)
            }
    
    def process_all_pdfs(self) -> Dict[str, Any]:
        """Process all PDFs in the directory"""
        logger.info(f"Starting processing of PDFs in: {self.pdf_directory}")
        
        # Get all PDF files
        pdf_files = [f for f in os.listdir(self.pdf_directory) 
                    if f.lower().endswith('.pdf') and not f.endswith(':Zone.Identifier')]
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.pdf_directory, pdf_file)
            result = self.process_single_pdf(pdf_path)
            self.processed_papers.append(result)
        
        # Create training datasets
        logger.info("Creating training datasets...")
        datasets = self.create_training_datasets()
        
        # Save datasets
        for dataset_name, dataset_data in datasets.items():
            dataset_path = f"{self.output_directory}/training_datasets/{dataset_name}_dataset.json"
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {dataset_name} dataset: {len(dataset_data['data'])} samples")
        
        # Generate summary report
        successful_papers = [p for p in self.processed_papers if p.get("status") == "success"]
        failed_papers = [p for p in self.processed_papers if p.get("status") == "error"]
        
        summary = {
            "processing_completed": datetime.now().isoformat(),
            "total_pdfs": len(pdf_files),
            "successful_papers": len(successful_papers),
            "failed_papers": len(failed_papers),
            "total_words": sum(p.get("word_count", 0) for p in successful_papers),
            "datasets_created": list(datasets.keys()),
            "dataset_sizes": {name: len(data["data"]) for name, data in datasets.items()},
            "output_directory": self.output_directory
        }
        
        # Save summary
        summary_path = f"{self.output_directory}/metadata/processing_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Processing completed! Summary saved to: {summary_path}")
        return summary

def main():
    """Main function to run the PDF processing"""
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_training_data.py <pdf_directory> [output_directory]")
        print("Example: python pdf_to_training_data.py ./research_papers/raw_pdfs ./training_data")
        sys.exit(1)
    
    pdf_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else "./training_data"
    
    if not os.path.exists(pdf_directory):
        print(f"Error: PDF directory '{pdf_directory}' does not exist")
        sys.exit(1)
    
    # Initialize processor
    processor = PDFToTrainingData(pdf_directory, output_directory)
    
    # Process all PDFs
    summary = processor.process_all_pdfs()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 PROCESSING SUMMARY")
    print("="*60)
    print(f"📁 PDF Directory: {pdf_directory}")
    print(f"📁 Output Directory: {output_directory}")
    print(f"📄 Total PDFs: {summary['total_pdfs']}")
    print(f"✅ Successfully Processed: {summary['successful_papers']}")
    print(f"❌ Failed: {summary['failed_papers']}")
    print(f"📝 Total Words: {summary['total_words']:,}")
    print(f"📊 Datasets Created: {', '.join(summary['datasets_created'])}")
    print("\n📋 Dataset Sizes:")
    for name, size in summary['dataset_sizes'].items():
        print(f"   • {name}: {size} samples")
    
    print(f"\n🎉 All data saved to: {output_directory}")
    print("\n📁 Directory Structure:")
    print(f"   {output_directory}/")
    print(f"   ├── processed_papers/     # Individual processed papers")
    print(f"   ├── training_datasets/    # Ready-to-use training datasets")
    print(f"   └── metadata/            # Processing reports and summaries")

if __name__ == "__main__":
    main()
