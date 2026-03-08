"""
Application configuration
"""
import os
from pathlib import Path

class Config:
    """Application configuration"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        # MongoDB
        self.MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27018/')
        
        # Storage
        self.STORAGE_PATH = os.getenv('STORAGE_PATH', './storage')
        
        # Model settings
        self.BASE_MODEL_NAME = os.getenv('BASE_MODEL_NAME', 'Qwen/Qwen2.5-1.5B-Instruct')
        self.ADAPTER_PATH = os.getenv('ADAPTER_PATH', None)  # Path to fine-tuned adapter (local or HuggingFace repo)
        self.HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN', None)  # Token for private models
        self.USE_HUGGINGFACE_REPO = os.getenv('USE_HUGGINGFACE_REPO', 'false').lower() == 'true'  # If adapter_path is HuggingFace repo
        
        # RAG settings
        self.EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'BAAI/bge-small-en-v1.5')
        self.CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '512'))
        self.CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '50'))
        self.TOP_K_CHUNKS = int(os.getenv('TOP_K_CHUNKS', '5'))
        
        # Flowchart settings
        self.FLOWCHART_RENDERER = os.getenv('FLOWCHART_RENDERER', 'mermaid')  # 'mermaid' or 'graphviz'

        # Guardrail settings
        self.GUARDRAIL_STRICT_MODE = os.getenv('GUARDRAIL_STRICT_MODE', 'true').lower() == 'true'
        self.GUARDRAIL_LOG_REJECTIONS = os.getenv('GUARDRAIL_LOG_REJECTIONS', 'true').lower() == 'true'

