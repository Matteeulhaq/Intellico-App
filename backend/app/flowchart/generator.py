"""
Main flowchart generation logic
"""
from typing import List, Optional, Dict, Tuple
from .keyword_relationship_extractor import KeywordRelationshipExtractor
from .mermaid_renderer import MermaidRenderer
from .graphviz_renderer import GraphvizRenderer

class FlowchartGenerator:
    """Generate flowcharts showing keyword/terminology relationships from research papers"""
    
    def __init__(self, keyword_extractor: KeywordRelationshipExtractor, renderer_type: str = "mermaid"):
        """
        Initialize flowchart generator
        
        Args:
            keyword_extractor: Extractor for keywords and relationships
            renderer_type: "mermaid" or "graphviz"
        """
        self.extractor = keyword_extractor
        
        if renderer_type == "mermaid":
            self.renderer = MermaidRenderer(use_api=True)
        else:
            self.renderer = GraphvizRenderer(format="svg")
        
        self.renderer_type = renderer_type
    
    def generate(
        self,
        paper_text: str,
        sections: Optional[Dict[str, str]] = None,
        output_format: str = "svg"
    ) -> bytes:
        """
        Generate flowchart from paper showing keyword/terminology relationships
        
        Args:
            paper_text: Full paper text
            sections: Optional dictionary of sections (abstract, introduction, etc.)
            output_format: Output format ("svg", "png")
            
        Returns:
            Flowchart image bytes showing concept flow
        """
        # Extract keywords and relationships
        keywords, relationships = self.extractor.extract_keywords_and_relationships(
            paper_text, 
            sections=sections
        )
        
        if not keywords:
            # Fallback: create a simple flowchart
            keywords = ["Key terms could not be extracted from this paper"]
            relationships = []
        
        # Build concept flow (ordered terms)
        concept_flow = self.extractor.build_concept_flow(keywords, relationships)
        
        # Generate flowchart
        if self.renderer_type == "mermaid":
            return self.renderer.generate_flowchart(
                concept_flow, 
                relationships=relationships,
                output_format=output_format
            )
        else:
            return self.renderer.generate_flowchart(
                concept_flow,
                relationships=relationships
            )

    def generate_mermaid_code(
        self,
        paper_text: str,
        sections: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate Mermaid code from paper showing keyword/terminology relationships
        
        Args:
            paper_text: Full paper text
            sections: Optional dictionary of sections (abstract, introduction, etc.)
            
        Returns:
            Mermaid diagram code as string
        """
        # Extract keywords and relationships
        keywords, relationships = self.extractor.extract_keywords_and_relationships(
            paper_text, 
            sections=sections
        )
        
        if not keywords:
            # Fallback: create a simple flowchart
            keywords = ["Key terms could not be extracted from this paper"]
            relationships = []
        
        # Build concept flow (ordered terms)
        concept_flow = self.extractor.build_concept_flow(keywords, relationships)
        
        # Generate mermaid code (without rendering)
        if self.renderer_type == "mermaid":
            return self.renderer.keywords_to_mermaid(
                concept_flow, 
                relationships=relationships
            )
        else:
            # For graphviz, return empty for now
            return ""

