"""
Main paper analysis orchestrator
"""
import os
from typing import Dict, Optional
from .rag.rag_chain import RAGChain
from .rag.embedder import Embedder
from .rag.vector_store import VectorStore
from .rag.chunker import TextChunker
from .models.model_router import ModelRouter
from .flowchart.generator import FlowchartGenerator
from .flowchart.keyword_relationship_extractor import KeywordRelationshipExtractor

class PaperAnalyzer:
    """Orchestrate all analysis components"""
    
    def __init__(
        self,
        mongo_uri: str,
        base_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path: Optional[str] = None
    ):
        """
        Initialize paper analyzer
        
        Args:
            mongo_uri: MongoDB connection URI
            base_model_name: Base model name
            adapter_path: Path to fine-tuned adapter
        """
        # Initialize components
        self.embedder = Embedder()
        self.vector_store = VectorStore(mongo_uri)
        self.chunker = TextChunker(chunk_size=512, chunk_overlap=50)
        self.rag_chain = RAGChain(self.embedder, self.vector_store)
        # Check if adapter_path is a HuggingFace repo
        use_hf_repo = os.getenv('USE_HUGGINGFACE_REPO', 'false').lower() == 'true'
        hf_token = os.getenv('HUGGINGFACE_TOKEN', None)
        
        self.model_router = ModelRouter(
            base_model_name, 
            adapter_path,
            hf_token=hf_token,
            use_hf_repo=use_hf_repo
        )
        
        # Flowchart components
        keyword_extractor = KeywordRelationshipExtractor(self.model_router)
        self.flowchart_generator = FlowchartGenerator(keyword_extractor, renderer_type="mermaid")
    
    def index_paper(self, paper_data: Dict):
        """
        Index a paper for RAG
        
        Args:
            paper_data: Dictionary with paper_id, full_text, sections, etc.
        """
        paper_id = paper_data['paper_id']
        
        # Store paper metadata
        self.vector_store.store_paper(paper_id, {
            'title': paper_data.get('metadata', {}).get('title', ''),
            'author': paper_data.get('metadata', {}).get('author', ''),
            'word_count': paper_data.get('word_count', 0),
            'page_count': paper_data.get('page_count', 0),
        })
        
        # Chunk text
        chunks = self.chunker.chunk_by_sections(
            paper_data.get('sections', {}),
            metadata={'paper_id': paper_id}
        )
        
        # Generate embeddings
        chunks_with_embeddings = self.embedder.embed_chunks(chunks)
        
        # Store chunks
        self.vector_store.store_chunks(paper_id, chunks_with_embeddings)
        
        print(f"Indexed paper {paper_id} with {len(chunks_with_embeddings)} chunks")
    
    def answer_question(self, question: str, paper_id: Optional[str] = None) -> Dict:
        """
        Answer question using RAG + model
        
        Args:
            question: User question
            paper_id: Optional paper ID to filter
            
        Returns:
            Dictionary with answer and context
        """
        # Retrieve relevant context
        rag_result = self.rag_chain.query(question, paper_id=paper_id, top_k=5)
        
        # Generate answer using model
        answer = self.model_router.answer_question(question, rag_result['context'])
        
        return {
            'answer': answer,
            'context': rag_result['context'],
            'num_chunks': rag_result['num_chunks']
        }
    
    def generate_flowchart(self, paper_id: str) -> bytes:
        """
        Generate flowchart for a paper showing keyword/terminology relationships
        
        Args:
            paper_id: Paper identifier
            
        Returns:
            Flowchart image bytes (SVG) showing concept flow
        """
        # Get paper chunks
        chunks = self.vector_store.get_paper_chunks(paper_id)
        
        # Reconstruct sections from chunks
        sections = {}
        full_text_parts = []
        
        for chunk in chunks:
            section_name = chunk.get('section', 'content')
            text = chunk.get('text', '')
            
            if section_name not in sections:
                sections[section_name] = text
            else:
                sections[section_name] += "\n" + text
            
            full_text_parts.append(text)
        
        # Combine full text
        full_text = "\n\n".join(full_text_parts)
        
        # Generate flowchart with keyword relationships
        flowchart_image = self.flowchart_generator.generate(
            full_text,
            sections=sections if sections else None,
            output_format="svg"
        )
        
        return flowchart_image
    
    def extract_metadata(self, paper_text: str) -> Dict:
        """Extract metadata from paper text"""
        return self.model_router.extract_metadata(paper_text)

