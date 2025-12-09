"""
Retriever for RAG pipeline
"""
from typing import List, Dict, Optional
from .embedder import Embedder
from .vector_store import VectorStore

class Retriever:
    """Retrieve relevant chunks for RAG"""
    
    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store
    
    def retrieve(self, query: str, paper_id: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: Query text
            paper_id: Optional filter by paper_id
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Retrieve similar chunks
        chunks = self.vector_store.retrieve_similar(
            query_embedding.tolist(),
            paper_id=paper_id,
            top_k=top_k
        )
        
        return chunks
    
    def format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks as context string
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Formatted context string
        """
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            section = chunk.get('section', '')
            text = chunk.get('text', '')
            context_parts.append(f"[Chunk {i} - {section}]\n{text}\n")
        
        return "\n".join(context_parts)

