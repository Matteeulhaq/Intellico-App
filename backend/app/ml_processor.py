"""
Machine Learning Processor for Research Papers
Handles embeddings, vector storage, and model training
"""

import os
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import torch
from transformers import AutoTokenizer, AutoModel
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLProcessor:
    def __init__(self, storage_path: str = "/app/storage"):
        self.storage_path = storage_path
        self.research_papers_path = os.path.join(storage_path, "research_papers")
        self.processed_path = os.path.join(self.research_papers_path, "processed")
        self.embeddings_path = os.path.join(self.research_papers_path, "embeddings")
        
        # Create directories
        os.makedirs(self.embeddings_path, exist_ok=True)
        
        # Initialize models
        self.sentence_model = None
        self.tokenizer = None
        self.bert_model = None
        self.vectorizer = None
        self.faiss_index = None
        
        # Initialize ChromaDB
        self.chroma_client = None
        self.collection = None
        
    def initialize_models(self):
        """Initialize ML models for text processing"""
        try:
            logger.info("Initializing ML models...")
            
            # Sentence Transformer for embeddings
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # BERT model for advanced text processing
            self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
            self.bert_model = AutoModel.from_pretrained('bert-base-uncased')
            
            # TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Initialize ChromaDB
            self.chroma_client = chromadb.Client(Settings(
                persist_directory=self.embeddings_path,
                anonymized_telemetry=False
            ))
            
            # Create or get collection
            try:
                self.collection = self.chroma_client.get_collection("research_papers")
            except:
                self.collection = self.chroma_client.create_collection(
                    name="research_papers",
                    metadata={"description": "Research papers embeddings"}
                )
            
            logger.info("ML models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            raise
    
    def generate_embeddings(self, texts: List[str], method: str = "sentence_transformer") -> np.ndarray:
        """
        Generate embeddings for texts using different methods
        """
        if method == "sentence_transformer":
            return self.sentence_model.encode(texts)
        elif method == "bert":
            embeddings = []
            for text in texts:
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self.bert_model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                    embeddings.append(embedding)
            return np.array(embeddings)
        elif method == "tfidf":
            return self.vectorizer.fit_transform(texts).toarray()
        else:
            raise ValueError(f"Unknown embedding method: {method}")
    
    def process_paper_embeddings(self, processed_papers: List[Dict]) -> Dict[str, any]:
        """
        Generate embeddings for all processed papers
        """
        if not self.sentence_model:
            self.initialize_models()
        
        embeddings_data = {
            "papers": [],
            "embeddings": [],
            "metadata": [],
            "created_at": datetime.now().isoformat()
        }
        
        for paper in processed_papers:
            if paper.get("status") == "error":
                continue
                
            paper_id = paper["paper_id"]
            
            # Extract text chunks for embedding
            text_chunks = self._create_text_chunks(paper)
            
            # Generate embeddings for each chunk
            chunk_embeddings = []
            for i, chunk in enumerate(text_chunks):
                chunk_text = chunk["text"]  # Extract text from chunk dict
                embedding = self.generate_embeddings([chunk_text])[0]
                chunk_embeddings.append(embedding)
                
                # Store in ChromaDB
                self.collection.add(
                    embeddings=[embedding.tolist()],
                    documents=[chunk_text],
                    metadatas=[{
                        "paper_id": paper_id,
                        "chunk_id": i,
                        "section": chunk.get("section", "unknown"),
                        "word_count": len(chunk_text.split())
                    }],
                    ids=[f"{paper_id}_chunk_{i}"]
                )
            
            # Store paper-level data
            embeddings_data["papers"].append({
                "paper_id": paper_id,
                "title": paper.get("metadata", {}).get("title", ""),
                "chunk_count": len(text_chunks),
                "total_words": paper.get("word_count", 0)
            })
            
            embeddings_data["embeddings"].extend([embedding.tolist() for embedding in chunk_embeddings])
            embeddings_data["metadata"].extend([
                {
                    "paper_id": paper_id,
                    "chunk_id": i,
                    "section": chunk.get("section", "unknown")
                } for i, chunk in enumerate(text_chunks)
            ])
        
        # Save embeddings data
        embeddings_file = os.path.join(self.embeddings_path, "embeddings_data.json")
        with open(embeddings_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings_data, f, indent=2, ensure_ascii=False)
        
        # Create FAISS index for fast similarity search
        if embeddings_data["embeddings"]:
            self._create_faiss_index(embeddings_data["embeddings"])
        
        logger.info(f"Processed embeddings for {len(embeddings_data['papers'])} papers")
        return embeddings_data
    
    def _create_text_chunks(self, paper: Dict, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """
        Create text chunks from paper for better embedding quality
        """
        chunks = []
        
        # Process each section separately
        sections = paper.get("sections", {})
        full_text = paper.get("full_text", "")
        
        for section_name, section_text in sections.items():
            if not section_text.strip():
                continue
                
            # Split section into chunks
            words = section_text.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                chunk_text = " ".join(chunk_words)
                
                if len(chunk_text.strip()) > 50:  # Only include substantial chunks
                    chunks.append({
                        "text": chunk_text,
                        "section": section_name,
                        "paper_id": paper["paper_id"]
                    })
        
        # If no sections found, chunk the full text
        if not chunks and full_text:
            words = full_text.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                chunk_text = " ".join(chunk_words)
                
                if len(chunk_text.strip()) > 50:
                    chunks.append({
                        "text": chunk_text,
                        "section": "full_text",
                        "paper_id": paper["paper_id"]
                    })
        
        return chunks
    
    def _create_faiss_index(self, embeddings: List[np.ndarray]):
        """
        Create FAISS index for fast similarity search
        """
        if not embeddings:
            return
        
        embeddings_array = np.array(embeddings).astype('float32')
        dimension = embeddings_array.shape[1]
        
        # Create FAISS index
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.faiss_index.add(embeddings_array)
        
        # Save index
        index_path = os.path.join(self.embeddings_path, "faiss_index.bin")
        faiss.write_index(self.faiss_index, index_path)
        
        logger.info(f"Created FAISS index with {len(embeddings)} vectors")
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Perform semantic search using embeddings
        """
        if not self.sentence_model:
            self.initialize_models()
        
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        # Format results
        search_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            search_results.append({
                "rank": i + 1,
                "text": doc,
                "paper_id": metadata["paper_id"],
                "section": metadata["section"],
                "similarity_score": 1 - distance,  # Convert distance to similarity
                "metadata": metadata
            })
        
        return search_results
    
    def train_custom_model(self, processed_papers: List[Dict], model_type: str = "classification") -> Dict[str, any]:
        """
        Train custom models on the research papers
        """
        logger.info(f"Training {model_type} model on {len(processed_papers)} papers")
        
        # Extract training data
        training_data = self._prepare_training_data(processed_papers, model_type)
        
        if model_type == "classification":
            return self._train_classification_model(training_data)
        elif model_type == "summarization":
            return self._train_summarization_model(training_data)
        elif model_type == "question_answering":
            return self._train_qa_model(training_data)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _prepare_training_data(self, papers: List[Dict], model_type: str) -> Dict:
        """
        Prepare training data based on model type
        """
        data = {
            "texts": [],
            "labels": [],
            "metadata": []
        }
        
        for paper in papers:
            if paper.get("status") == "error":
                continue
            
            # Extract different types of data based on model type
            if model_type == "classification":
                # Use sections as labels
                for section_name, section_text in paper.get("sections", {}).items():
                    if section_text.strip():
                        data["texts"].append(section_text)
                        data["labels"].append(section_name)
                        data["metadata"].append({
                            "paper_id": paper["paper_id"],
                            "section": section_name
                        })
            
            elif model_type in ["summarization", "question_answering"]:
                # Use full text and abstracts
                full_text = paper.get("full_text", "")
                abstract = paper.get("sections", {}).get("abstract", "")
                
                if full_text and abstract:
                    data["texts"].append(full_text)
                    data["labels"].append(abstract)  # Abstract as summary
                    data["metadata"].append({
                        "paper_id": paper["paper_id"],
                        "type": "full_text_to_abstract"
                    })
        
        return data
    
    def _train_classification_model(self, training_data: Dict) -> Dict[str, any]:
        """
        Train a text classification model
        """
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import classification_report, accuracy_score
        
        # Generate features
        X = self.vectorizer.fit_transform(training_data["texts"])
        y = training_data["labels"]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Save model
        model_path = os.path.join(self.embeddings_path, "classification_model.pkl")
        import joblib
        joblib.dump(model, model_path)
        
        return {
            "model_type": "classification",
            "accuracy": accuracy,
            "classification_report": report,
            "model_path": model_path,
            "feature_count": X.shape[1],
            "training_samples": len(training_data["texts"])
        }
    
    def _train_summarization_model(self, training_data: Dict) -> Dict[str, any]:
        """
        Train a text summarization model (placeholder for now)
        """
        # This would typically involve fine-tuning a transformer model
        # For now, we'll return a placeholder
        return {
            "model_type": "summarization",
            "status": "placeholder",
            "message": "Summarization model training requires more complex setup with transformers"
        }
    
    def _train_qa_model(self, training_data: Dict) -> Dict[str, any]:
        """
        Train a question-answering model (placeholder for now)
        """
        # This would typically involve fine-tuning a BERT-based QA model
        return {
            "model_type": "question_answering",
            "status": "placeholder",
            "message": "QA model training requires more complex setup with transformers"
        }

# Example usage
if __name__ == "__main__":
    ml_processor = MLProcessor()
    # Example: ml_processor.initialize_models()
