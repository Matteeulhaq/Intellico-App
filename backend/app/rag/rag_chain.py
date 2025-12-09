"""
RAG chain orchestration
"""
from typing import Optional, Dict
from .retriever import Retriever
from .embedder import Embedder
from .vector_store import VectorStore

class RAGChain:
    """Complete RAG pipeline"""
    
    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store
        self.retriever = Retriever(embedder, vector_store)
    
    def query(self, question: str, paper_id: Optional[str] = None, top_k: int = 5) -> Dict:
        """
        Query RAG system
        
        Args:
            question: User question
            paper_id: Optional paper ID to filter
            top_k: Number of chunks to retrieve
            
        Returns:
            Dictionary with context and retrieved chunks
        """
        # Retrieve relevant chunks
        chunks = self.retriever.retrieve(question, paper_id=paper_id, top_k=top_k)
        
        # Format context
        context = self.retriever.format_context(chunks)
        
        return {
            'context': context,
            'chunks': chunks,
            'num_chunks': len(chunks)
        }

