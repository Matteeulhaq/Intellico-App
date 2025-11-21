"""
PDF processing and text extraction
"""
import os
import json
from typing import Dict, Optional
import pdfplumber
import PyPDF2
from pathlib import Path

class PDFProcessor:
    """Process PDF files and extract text"""
    
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def extract_text(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        text_content = []
        metadata = {}
        
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(pdf_path) as pdf:
                metadata = {
                    'page_count': len(pdf.pages),
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                }
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_content.append({
                            'page': page_num,
                            'text': text
                        })
        except Exception as e:
            print(f"pdfplumber failed, trying PyPDF2: {e}")
            # Fallback to PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = {
                    'page_count': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                    'author': pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                }
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_content.append({
                            'page': page_num,
                            'text': text
                        })
        
        # Combine all text
        full_text = '\n\n'.join([page['text'] for page in text_content])
        
        return {
            'full_text': full_text,
            'pages': text_content,
            'metadata': metadata,
            'word_count': len(full_text.split()),
            'char_count': len(full_text)
        }
    
    def identify_sections(self, text: str) -> Dict[str, str]:
        """
        Identify paper sections (basic implementation)
        
        Args:
            text: Full paper text
            
        Returns:
            Dictionary mapping section names to text
        """
        sections = {}
        
        # Common section headers
        section_patterns = {
            'abstract': r'(?i)(?:^|\n)\s*(?:abstract|summary)\s*(?:\n|:)',
            'introduction': r'(?i)(?:^|\n)\s*(?:introduction|background)\s*(?:\n|:)',
            'methodology': r'(?i)(?:^|\n)\s*(?:methodology|methods|materials?\s+and\s+methods?)\s*(?:\n|:)',
            'results': r'(?i)(?:^|\n)\s*(?:results?|findings?)\s*(?:\n|:)',
            'discussion': r'(?i)(?:^|\n)\s*(?:discussion|analysis)\s*(?:\n|:)',
            'conclusion': r'(?i)(?:^|\n)\s*(?:conclusion|conclusions?)\s*(?:\n|:)',
            'references': r'(?i)(?:^|\n)\s*(?:references?|bibliography)\s*(?:\n|:)',
        }
        
        import re
        section_positions = []
        
        for section_name, pattern in section_patterns.items():
            matches = list(re.finditer(pattern, text))
            if matches:
                section_positions.append((section_name, matches[0].start()))
        
        # Sort by position
        section_positions.sort(key=lambda x: x[1])
        
        # Extract sections
        for i, (section_name, start_pos) in enumerate(section_positions):
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][1]
                sections[section_name] = text[start_pos:end_pos].strip()
            else:
                sections[section_name] = text[start_pos:].strip()
        
        # If no sections found, return full text as content
        if not sections:
            sections['content'] = text
        
        return sections
    
    def process_pdf(self, pdf_file, paper_id: str) -> Dict:
        """
        Process uploaded PDF file
        
        Args:
            pdf_file: Uploaded file object
            paper_id: Unique paper identifier
            
        Returns:
            Dictionary with processed paper data
        """
        # Save uploaded file
        pdf_path = self.storage_path / f"{paper_id}.pdf"
        pdf_file.save(str(pdf_path))
        
        # Extract text
        extracted = self.extract_text(str(pdf_path))
        
        # Identify sections
        sections = self.identify_sections(extracted['full_text'])
        
        return {
            'paper_id': paper_id,
            'filename': pdf_file.filename,
            'pdf_path': str(pdf_path),
            'full_text': extracted['full_text'],
            'sections': sections,
            'metadata': extracted['metadata'],
            'word_count': extracted['word_count'],
            'char_count': extracted['char_count'],
            'page_count': extracted['metadata'].get('page_count', 0)
        }

