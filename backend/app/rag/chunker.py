"""
PDF text chunking for RAG
"""
from typing import List, Dict
import re

class TextChunker:
    """Chunk text into overlapping segments for RAG"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Split by sentences first for better semantic boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunk_dict = {
                    'text': chunk_text,
                    'chunk_index': len(chunks),
                    'char_count': len(chunk_text),
                    'word_count': len(chunk_text.split())
                }
                if metadata:
                    chunk_dict.update(metadata)
                chunks.append(chunk_dict)
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_dict = {
                'text': chunk_text,
                'chunk_index': len(chunks),
                'char_count': len(chunk_text),
                'word_count': len(chunk_text.split())
            }
            if metadata:
                chunk_dict.update(metadata)
            chunks.append(chunk_dict)
        
        return chunks
    
    def chunk_by_sections(self, sections: Dict[str, str], metadata: Dict = None) -> List[Dict]:
        """
        Chunk text organized by sections
        
        Args:
            sections: Dictionary mapping section names to text
            metadata: Optional metadata
            
        Returns:
            List of chunk dictionaries
        """
        all_chunks = []
        
        for section_name, section_text in sections.items():
            section_metadata = {'section': section_name}
            if metadata:
                section_metadata.update(metadata)
            
            chunks = self.chunk_text(section_text, section_metadata)
            all_chunks.extend(chunks)
        
        return all_chunks

