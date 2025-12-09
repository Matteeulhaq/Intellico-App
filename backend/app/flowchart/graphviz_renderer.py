"""
Graphviz flowchart rendering
"""
from typing import List
from graphviz import Digraph
import os

class GraphvizRenderer:
    """Generate and render Graphviz flowcharts"""
    
    def __init__(self, format: str = "svg"):
        """
        Initialize Graphviz renderer
        
        Args:
            format: Output format ("svg", "png", "pdf")
        """
        self.format = format
    
    def keywords_to_dot(
        self, 
        keywords: List[str], 
        relationships: List[tuple] = None
    ) -> Digraph:
        """
        Convert keywords/terminologies and relationships to Graphviz DOT format
        
        Args:
            keywords: List of keywords/terminologies
            relationships: List of (source_term, target_term) tuples showing conceptual flow
            
        Returns:
            Graphviz Digraph object
        """
        dot = Digraph(comment='Concept Flowchart', format=self.format)
        dot.attr(rankdir='TD')  # Top to bottom
        dot.attr('node', shape='box', style='rounded')
        
        # Create node map
        node_map = {}
        
        # Create nodes
        for i, keyword in enumerate(keywords, 1):
            # Clean keyword text
            clean_keyword = keyword[:50].replace('\n', ' ').strip()
            node_id = f"term{i}"
            node_map[keyword] = node_id
            dot.node(node_id, clean_keyword)
        
        # Create edges based on relationships
        if relationships:
            for from_term, to_term in relationships:
                from_id = node_map.get(from_term)
                to_id = node_map.get(to_term)
                if from_id and to_id:
                    dot.edge(from_id, to_id)
        else:
            # If no relationships, create sequential flow
            for i in range(len(keywords) - 1):
                dot.edge(f"term{i+1}", f"term{i+2}")
        
        return dot
    
    def steps_to_dot(self, steps: List[str]) -> Digraph:
        """
        Convert methodology steps to Graphviz DOT format (legacy method for backward compatibility)
        
        Args:
            steps: List of methodology steps
            
        Returns:
            Graphviz Digraph object
        """
        # Treat steps as keywords with sequential relationships
        relationships = [(steps[i], steps[i+1]) for i in range(len(steps) - 1)]
        return self.keywords_to_dot(steps, relationships)
    
    def render(self, dot: Digraph, output_path: str = None) -> bytes:
        """
        Render Graphviz diagram to image
        
        Args:
            dot: Graphviz Digraph object
            output_path: Optional path to save file
            
        Returns:
            Image bytes
        """
        # Render to bytes
        dot_bytes = dot.pipe(format=self.format)
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(dot_bytes)
        
        return dot_bytes
    
    def generate_flowchart(
        self, 
        keywords: List[str], 
        relationships: List[tuple] = None,
        output_path: str = None
    ) -> bytes:
        """
        Generate flowchart image from keywords and relationships
        
        Args:
            keywords: List of keywords/terminologies
            relationships: List of (source_term, target_term) tuples
            output_path: Optional path to save file
            
        Returns:
            Image bytes
        """
        dot = self.keywords_to_dot(keywords, relationships)
        return self.render(dot, output_path)

