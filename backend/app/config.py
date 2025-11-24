"""
Application configuration
"""
import os
from pathlib import Path

class Config:
    """Application configuration"""
    
    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    
    # Storage
    STORAGE_PATH = os.getenv('STORAGE_PATH', './storage')
    
    # Model settings
    BASE_MODEL_NAME = os.getenv('BASE_MODEL_NAME', 'Qwen/Qwen2.5-1.5B-Instruct')
    ADAPTER_PATH = os.getenv('ADAPTER_PATH', None)  # Path to fine-tuned adapter (local or HuggingFace repo)
    HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN', None)  # Token for private models
    USE_HUGGINGFACE_REPO = os.getenv('USE_HUGGINGFACE_REPO', 'false').lower() == 'true'  # If adapter_path is HuggingFace repo
    
    # RAG settings
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'BAAI/bge-small-en-v1.5')
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '512'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '50'))
    TOP_K_CHUNKS = int(os.getenv('TOP_K_CHUNKS', '5'))
    
    # Flowchart settings
    FLOWCHART_RENDERER = os.getenv('FLOWCHART_RENDERER', 'mermaid')  # 'mermaid' or 'graphviz'

