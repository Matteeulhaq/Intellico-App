"""
MongoDB vector storage and retrieval for RAG
"""
from typing import List, Dict, Optional
import numpy as np
from pymongo import MongoClient
from pymongo.collection import Collection
from bson.binary import Binary
import json
import datetime
import hashlib

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
        self.summaries_collection: Collection = self.db['summaries']

        # Initialize flowcharts collection for caching
        try:
            self.flowcharts_collection: Collection = self.db['flowcharts']
            self.flowcharts_collection.create_index("paper_id", unique=True)
            print("Flowcharts collection initialized for caching")
        except Exception as e:
            print(f"Error initializing flowcharts collection: {e}")

        # Initialize QA cache collection
        try:
            self.qa_cache_collection: Collection = self.db['qa_cache']
            self.qa_cache_collection.create_index([("paper_id", 1), ("question_hash", 1)])
            print("QA cache collection initialized")
        except Exception as e:
            print(f"Error initializing QA cache collection: {e}")

        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary indexes for efficient queries"""
        # Index on paper_id for fast lookups
        self.chunks_collection.create_index("paper_id")
        self.chunks_collection.create_index("chunk_index")

        # Index on paper_id for papers collection
        self.papers_collection.create_index("paper_id", unique=True)

        # Index on paper_id for summaries collection (cache lookups)
        try:
            self.summaries_collection.create_index("paper_id", unique=True)
            print("Summaries collection initialized for caching")
        except Exception as e:
            print(f"Error initializing summaries collection: {e}")
    
    def store_paper(self, paper_id: str, metadata: Dict):
        """
        Store paper metadata with validation and error handling

        Args:
            paper_id: Unique paper identifier
            metadata: Paper metadata to store

        Raises:
            ValueError: If paper_id is missing
            RuntimeError: If save operation fails
        """
        import logging
        logger = logging.getLogger(__name__)

        if not paper_id:
            raise ValueError("paper_id is required")

        if not metadata:
            logger.warning(f"Empty metadata for {paper_id}")
            metadata = {}

        document = {
            'paper_id': paper_id,
            **metadata,
        }

        try:
            result = self.papers_collection.update_one(
                {'paper_id': paper_id},
                {'$set': document},
                upsert=True
            )

            # Verify the save worked
            saved_doc = self.papers_collection.find_one({'paper_id': paper_id})
            if not saved_doc:
                raise RuntimeError(f"Failed to save paper {paper_id} to database")

            logger.info(f"Successfully stored paper {paper_id} (upserted: {result.upserted_id})")
            return result.upserted_id

        except Exception as e:
            logger.error(f"Database error storing {paper_id}: {e}")
            raise
    
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
        Retrieve most similar chunks using optimized cosine similarity

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

        # OPTIMIZATION: Only fetch necessary fields (projection) and limit to recent chunks
        chunks = list(self.chunks_collection.find(
            query,
            {'embedding': 1, 'text': 1, 'section': 1, 'chunk_index': 1, 'paper_id': 1}  # Only fetch needed fields
        ).sort('chunk_index', -1).limit(100))  # Limit to last 100 chunks for performance

        if not chunks:
            return []

        # OPTIMIZATION: Convert to numpy array for batch processing (much faster)
        query_vec = np.array(query_embedding)

        # Batch process embeddings
        chunk_embeddings = np.array([c.get('embedding', []) for c in chunks])

        # OPTIMIZATION: Calculate all similarities at once using vectorized operations
        # Handle zero-length embeddings
        valid_mask = np.array([len(c.get('embedding', [])) > 0 for c in chunks])

        if not np.any(valid_mask):
            return []

        # Calculate similarities for all chunks at once
        norms = np.linalg.norm(chunk_embeddings, axis=1)
        query_norm = np.linalg.norm(query_vec)

        # Avoid division by zero
        similarities = np.zeros(len(chunks))
        valid_indices = np.where(valid_mask)[0]

        for i in valid_indices:
            if norms[i] > 0 and query_norm > 0:
                similarities[i] = np.dot(query_vec, chunk_embeddings[i]) / (norms[i] * query_norm)

        # Get top-k indices
        top_k_indices = np.argsort(similarities)[::-1][:top_k]

        # Return top chunks
        top_chunks = [chunks[i] for i in top_k_indices if similarities[i] > 0]

        return top_chunks
    
    def get_paper_chunks(self, paper_id: str) -> List[Dict]:
        """Get all chunks for a specific paper"""
        chunks = list(self.chunks_collection.find({'paper_id': paper_id}).sort('chunk_index', 1))
        return chunks
    
    def delete_paper(self, paper_id: str):
        """Delete all chunks and metadata for a paper"""
        self.chunks_collection.delete_many({'paper_id': paper_id})
        self.papers_collection.delete_one({'paper_id': paper_id})

    def store_summary(self, paper_id: str, summary_data: dict) -> str:
        """Store generated summary in MongoDB cache"""
        summary_document = {
            'paper_id': paper_id,
            'summary': summary_data.get('summary'),
            'section_summaries': summary_data.get('section_summaries', {}),
            'key_findings': summary_data.get('key_findings', {}),
            'metadata': summary_data.get('metadata', {}),
            'cache_stats': {
                'times_accessed': 1,
                'first_accessed': datetime.datetime.utcnow(),
                'last_accessed': datetime.datetime.utcnow()
            }
        }

        result = self.summaries_collection.insert_one(summary_document)
        print(f"Summary cached for {paper_id}")
        return str(result.inserted_id)

    def get_summary(self, paper_id: str) -> Optional[dict]:
        """Retrieve cached summary by paper_id"""
        summary = self.summaries_collection.find_one({'paper_id': paper_id})

        if summary:
            # Update cache statistics
            self.summaries_collection.update_one(
                {'_id': summary['_id']},
                {
                    '$inc': {'cache_stats.times_accessed': 1},
                    '$set': {'cache_stats.last_accessed': datetime.datetime.utcnow()}
                }
            )
            print(f"Cache hit for {paper_id} (accessed {summary['cache_stats']['times_accessed']} times)")
            return summary

        print(f"Cache miss for {paper_id}")
        return None

    def delete_summary(self, paper_id: str) -> bool:
        """Delete cached summary (for cache invalidation)"""
        result = self.summaries_collection.delete_one({'paper_id': paper_id})
        if result.deleted_count > 0:
            print(f"Cache invalidated for {paper_id}")
            # Also invalidate related caches
            self.delete_flowchart(paper_id)
            self.delete_qa_all(paper_id)
            return True
        return False

    def get_cache_stats(self) -> dict:
        """Get cache performance statistics"""
        total_cached = self.summaries_collection.count_documents({})

        # Calculate average access count
        pipeline = [
            {"$group": {"_id": None, "avg_accesses": {"$avg": "$cache_stats.times_accessed"}}}
        ]
        result = list(self.summaries_collection.aggregate(pipeline))
        avg_accesses = result[0]['avg_accesses'] if result else 0

        # Calculate total time saved
        pipeline = [
            {"$group": {"_id": None, "total_time_saved": {"$sum": "$metadata.processing_time_ms"}}}
        ]
        result = list(self.summaries_collection.aggregate(pipeline))
        total_time_saved = result[0]['total_time_saved'] if result else 0

        return {
            "total_cached_summaries": total_cached,
            "average_access_count": round(avg_accesses, 2),
            "total_processing_time_saved_ms": total_time_saved,
            "total_processing_time_saved_minutes": round(total_time_saved / 60000, 2)
        }

    # Flowchart caching methods
    def store_flowchart(self, paper_id: str, svg_data: bytes, mermaid_code: str, metadata: dict) -> str:
        """Store generated flowchart in MongoDB cache"""
        flowchart_document = {
            'paper_id': paper_id,
            'svg_data': Binary(svg_data),
            'mermaid_code': mermaid_code,
            'keywords_extracted': metadata.get('keywords_extracted', 0),
            'relationships_extracted': metadata.get('relationships_extracted', 0),
            'metadata': {
                'generated_at': datetime.datetime.utcnow(),
                'processing_time_ms': metadata.get('processing_time_ms', 0),
                'file_size_bytes': len(svg_data)
            },
            'cache_stats': {
                'times_accessed': 1,
                'first_accessed': datetime.datetime.utcnow(),
                'last_accessed': datetime.datetime.utcnow()
            }
        }

        # Upsert to handle re-uploads
        result = self.flowcharts_collection.update_one(
            {'paper_id': paper_id},
            {'$set': flowchart_document},
            upsert=True
        )
        print(f"Flowchart cached for {paper_id}")
        return str(result.upserted_id)

    def get_flowchart(self, paper_id: str) -> Optional[dict]:
        """Retrieve cached flowchart by paper_id"""
        flowchart = self.flowcharts_collection.find_one({'paper_id': paper_id})

        if flowchart:
            # Update cache statistics
            self.flowcharts_collection.update_one(
                {'_id': flowchart['_id']},
                {
                    '$inc': {'cache_stats.times_accessed': 1},
                    '$set': {'cache_stats.last_accessed': datetime.datetime.utcnow()}
                }
            )
            print(f"Flowchart cache hit for {paper_id} (accessed {flowchart['cache_stats']['times_accessed']} times)")
            return flowchart

        print(f"Flowchart cache miss for {paper_id}")
        return None

    def delete_flowchart(self, paper_id: str) -> bool:
        """Delete cached flowchart (for cache invalidation)"""
        result = self.flowcharts_collection.delete_one({'paper_id': paper_id})
        if result.deleted_count > 0:
            print(f"Flowchart cache invalidated for {paper_id}")
            return True
        return False

    # Q&A caching methods
    def store_qa(self, paper_id: str, question: str, answer: str, num_chunks: int, processing_time: int) -> str:
        """Store Q&A pair in MongoDB cache"""
        # Create hash of question for cache key
        question_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()

        qa_document = {
            'paper_id': paper_id,
            'question_hash': question_hash,
            'question': question,
            'answer': answer,
            'num_chunks_used': num_chunks,
            'metadata': {
                'generated_at': datetime.datetime.utcnow(),
                'processing_time_ms': processing_time
            },
            'cache_stats': {
                'times_accessed': 1,
                'first_accessed': datetime.datetime.utcnow(),
                'last_accessed': datetime.datetime.utcnow()
            }
        }

        result = self.qa_cache_collection.update_one(
            {'paper_id': paper_id, 'question_hash': question_hash},
            {'$set': qa_document},
            upsert=True
        )
        print(f"Q&A cached for {paper_id}")
        return str(result.upserted_id)

    def get_qa(self, paper_id: str, question: str) -> Optional[dict]:
        """Retrieve cached Q&A by paper_id and question"""
        question_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()

        qa = self.qa_cache_collection.find_one({
            'paper_id': paper_id,
            'question_hash': question_hash
        })

        if qa:
            # Update cache statistics
            self.qa_cache_collection.update_one(
                {'_id': qa['_id']},
                {
                    '$inc': {'cache_stats.times_accessed': 1},
                    '$set': {'cache_stats.last_accessed': datetime.datetime.utcnow()}
                }
            )
            print(f"Q&A cache hit for {paper_id} (accessed {qa['cache_stats']['times_accessed']} times)")
            return qa

        print(f"Q&A cache miss for {paper_id}")
        return None

    def delete_qa_all(self, paper_id: str) -> int:
        """Delete all cached Q&A for a paper (for cache invalidation)"""
        result = self.qa_cache_collection.delete_many({'paper_id': paper_id})
        if result.deleted_count > 0:
            print(f"Q&A cache invalidated for {paper_id} ({result.deleted_count} entries)")
        return result.deleted_count

