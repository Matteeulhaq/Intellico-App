"""
MongoDB schema definitions
"""
from typing import Dict, List, Optional
from pymongo import IndexModel

# Collection schemas (for reference/documentation)

PAPERS_SCHEMA = {
    "paper_id": str,  # Unique identifier
    "title": Optional[str],
    "author": Optional[str],
    "word_count": int,
    "page_count": int,
    "uploaded_at": str,  # ISO datetime
    "filename": str,
}

CHUNKS_SCHEMA = {
    "paper_id": str,  # Foreign key to papers
    "chunk_index": int,  # Order within paper
    "text": str,
    "embedding": List[float],  # Vector embedding
    "section": Optional[str],  # Section name (abstract, methodology, etc.)
    "char_count": int,
    "word_count": int,
}

# Index definitions
PAPERS_INDEXES = [
    IndexModel([("paper_id", 1)], unique=True),
    IndexModel([("title", "text")]),  # Text search index
]

CHUNKS_INDEXES = [
    IndexModel([("paper_id", 1)]),
    IndexModel([("chunk_index", 1)]),
    IndexModel([("paper_id", 1), ("chunk_index", 1)]),
]

