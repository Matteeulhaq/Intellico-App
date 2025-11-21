"""
MongoDB vector storage and retrieval for RAG
"""
from typing import List, Dict, Optional
import numpy as np
from pymongo import MongoClient
from pymongo.collection import Collection
import json

class VectorStore:
    """Store and retrieve vector embeddings in MongoDB"""
    
    def __init__(self, mongo_uri: str, db_name: str = "intellico"):
        """
        Initialize vector store
        
        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
        """
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.chunks_collection: Collection = self.db['chunks']
        self.papers_collection: Collection = self.db['papers']
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary indexes for efficient queries"""
        # Index on paper_id for fast lookups
        self.chunks_collection.create_index("paper_id")
        self.chunks_collection.create_index("chunk_index")
        
        # Index on paper_id for papers collection
        self.papers_collection.create_index("paper_id", unique=True)
    
    def store_paper(self, paper_id: str, metadata: Dict):
        """Store paper metadata"""
        document = {
            'paper_id': paper_id,
            **metadata,
        }
        self.papers_collection.update_one(
            {'paper_id': paper_id},
            {'$set': document},
            upsert=True
        )
    
    def store_chunks(self, paper_id: str, chunks: List[Dict]):
        """
        Store chunks with embeddings in MongoDB
        
        Args:
            paper_id: Unique paper identifier
            chunks: List of chunk dictionaries with 'text' and 'embedding' keys
        """
        # Delete existing chunks for this paper
        self.chunks_collection.delete_many({'paper_id': paper_id})
        
        # Prepare documents for insertion
        documents = []
        for chunk in chunks:
            doc = {
                'paper_id': paper_id,
                'text': chunk['text'],
                'embedding': chunk.get('embedding', []),
                'chunk_index': chunk.get('chunk_index', 0),
                'section': chunk.get('section', ''),
                'char_count': chunk.get('char_count', 0),
                'word_count': chunk.get('word_count', 0),
            }
            documents.append(doc)
        
        # Insert chunks
        if documents:
            self.chunks_collection.insert_many(documents)
            print(f"Stored {len(documents)} chunks for paper {paper_id}")
    
    def retrieve_similar(self, query_embedding: List[float], paper_id: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        """
        Retrieve most similar chunks using cosine similarity
        
        Args:
            query_embedding: Query embedding vector
            paper_id: Optional filter by paper_id
            top_k: Number of top results to return
            
        Returns:
            List of most similar chunks
        """
        query = {}
        if paper_id:
            query['paper_id'] = paper_id
        
        # Get all relevant chunks
        chunks = list(self.chunks_collection.find(query))
        
        if not chunks:
            return []
        
        # Calculate cosine similarity
        query_vec = np.array(query_embedding)
        similarities = []
        
        for chunk in chunks:
            chunk_embedding = np.array(chunk.get('embedding', []))
            if len(chunk_embedding) > 0:
                # Cosine similarity
                similarity = np.dot(query_vec, chunk_embedding) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(chunk_embedding)
                )
                similarities.append((similarity, chunk))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for _, chunk in similarities[:top_k]]
        
        return top_chunks
    
    def get_paper_chunks(self, paper_id: str) -> List[Dict]:
        """Get all chunks for a specific paper"""
        chunks = list(self.chunks_collection.find({'paper_id': paper_id}).sort('chunk_index', 1))
        return chunks
    
    def delete_paper(self, paper_id: str):
        """Delete all chunks and metadata for a paper"""
        self.chunks_collection.delete_many({'paper_id': paper_id})
        self.papers_collection.delete_one({'paper_id': paper_id})

