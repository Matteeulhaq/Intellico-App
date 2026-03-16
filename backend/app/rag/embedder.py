"""
Embedding generation for RAG
"""
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

class Embedder:
    """Generate embeddings for text chunks"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize embedder
        
        Args:
            model_name: HuggingFace model name for embeddings
                Options: 
                - "BAAI/bge-small-en-v1.5" (fast, good quality)
                - "BAAI/bge-base-en-v1.5" (better quality, slower)
                - "sentence-transformers/all-MiniLM-L6-v2" (very fast)
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
    
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text
        
        Args:
            text: Single text string or list of texts
            
        Returns:
            Numpy array of embeddings (shape: (n, dim) for list, (dim,) for single)
        """
        if isinstance(text, str):
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding
        else:
            embeddings = self.model.encode(text, normalize_embeddings=True, show_progress_bar=True)
            return embeddings
    
    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Generate embeddings for a list of text chunks (optimized batch processing)

        Args:
            chunks: List of chunk dictionaries with 'text' key

        Returns:
            List of chunks with added 'embedding' key
        """
        texts = [chunk['text'] for chunk in chunks]

        # Batch processing with optimized settings
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=8,  # Process 8 chunks at a time for better GPU utilization
            device='cuda' if self.model.device.type == 'cuda' else 'cpu'
        )

        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i].tolist()

        return chunks

