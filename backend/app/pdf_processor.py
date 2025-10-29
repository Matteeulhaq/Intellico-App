"""
PDF Processing Module for Research Papers
Handles extraction, preprocessing, and text cleaning of research papers
"""

import fitz  # PyMuPDF
import pdfplumber
import re
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, storage_path: str = "/app/storage"):
        self.storage_path = storage_path
        self.research_papers_path = os.path.join(storage_path, "research_papers")
        self.raw_pdfs_path = os.path.join(self.research_papers_path, "raw_pdfs")
        self.processed_path = os.path.join(self.research_papers_path, "processed")
        
        # Create directories if they don't exist
        os.makedirs(self.raw_pdfs_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract text from PDF using multiple methods for better accuracy
        """
        try:
            # Method 1: PyMuPDF for general text extraction
            doc = fitz.open(pdf_path)
            text_content = ""
            metadata = {}
            page_count = len(doc)  # Store page count before closing document
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text_content += page.get_text()
                
                # Extract metadata from first page
                if page_num == 0:
                    metadata = doc.metadata
            
            doc.close()
            
            # Method 2: pdfplumber for better table and structured content
            structured_content = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        structured_content.append(page_text)
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            structured_content.append("TABLE: " + str(table))
            
            # Combine both methods
            combined_text = text_content + "\n\n" + "\n".join(structured_content)
            
            return {
                "text": combined_text,
                "metadata": metadata,
                "page_count": page_count,
                "extraction_method": "combined"
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return {"text": "", "metadata": {}, "page_count": 0, "error": str(e)}
    
    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess extracted text
        """
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
        """
        Extract common research paper sections
        """
        sections = {
            "abstract": "",
            "introduction": "",
            "methodology": "",
            "results": "",
            "discussion": "",
            "conclusion": "",
            "references": ""
        }
        
        # Common section headers
        section_patterns = {
            "abstract": r"(?i)(abstract|summary)\s*:?\s*(.*?)(?=\n\s*(?:introduction|1\.|introduction|background))",
            "introduction": r"(?i)(introduction|background|overview)\s*:?\s*(.*?)(?=\n\s*(?:methodology|methods|2\.|approach))",
            "methodology": r"(?i)(methodology|methods|approach|experimental\s+setup)\s*:?\s*(.*?)(?=\n\s*(?:results|findings|3\.|outcomes))",
            "results": r"(?i)(results|findings|outcomes|data)\s*:?\s*(.*?)(?=\n\s*(?:discussion|analysis|4\.|conclusion))",
            "discussion": r"(?i)(discussion|analysis|interpretation)\s*:?\s*(.*?)(?=\n\s*(?:conclusion|summary|5\.|references))",
            "conclusion": r"(?i)(conclusion|summary|final\s+remarks)\s*:?\s*(.*?)(?=\n\s*(?:references|bibliography|acknowledgments))",
            "references": r"(?i)(references|bibliography|citations)\s*:?\s*(.*?)$"
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                sections[section_name] = self.clean_text(match.group(2) if len(match.groups()) > 1 else match.group(0))
        
        return sections
    
    def process_pdf(self, pdf_path: str, paper_id: str = None) -> Dict[str, any]:
        """
        Complete PDF processing pipeline
        """
        if not paper_id:
            paper_id = os.path.splitext(os.path.basename(pdf_path))[0]
        
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract text
        extraction_result = self.extract_text_from_pdf(pdf_path)
        
        if "error" in extraction_result:
            return {"paper_id": paper_id, "status": "error", "error": extraction_result["error"]}
        
        # Clean text
        cleaned_text = self.clean_text(extraction_result["text"])
        
        # Extract sections
        sections = self.extract_sections(cleaned_text)
        
        # Create processed document
        processed_doc = {
            "paper_id": paper_id,
            "filename": os.path.basename(pdf_path),
            "processed_at": datetime.now().isoformat(),
            "metadata": extraction_result["metadata"],
            "page_count": extraction_result["page_count"],
            "full_text": cleaned_text,
            "sections": sections,
            "word_count": len(cleaned_text.split()),
            "char_count": len(cleaned_text)
        }
        
        # Save processed document
        output_path = os.path.join(self.processed_path, f"{paper_id}_processed.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_doc, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processed document saved to: {output_path}")
        
        return processed_doc
    
    def batch_process_pdfs(self, pdf_directory: str) -> List[Dict[str, any]]:
        """
        Process all PDFs in a directory
        """
        results = []
        pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_directory, pdf_file)
            paper_id = os.path.splitext(pdf_file)[0]
            
            try:
                result = self.process_pdf(pdf_path, paper_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}")
                results.append({
                    "paper_id": paper_id,
                    "status": "error",
                    "error": str(e)
                })
        
        # Save batch processing summary
        summary_path = os.path.join(self.processed_path, "batch_processing_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                "processed_at": datetime.now().isoformat(),
                "total_files": len(pdf_files),
                "successful": len([r for r in results if r.get("status") != "error"]),
                "failed": len([r for r in results if r.get("status") == "error"]),
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        return results

# Example usage
if __name__ == "__main__":
    processor = PDFProcessor()
    # Example: processor.batch_process_pdfs("/path/to/your/pdfs")
