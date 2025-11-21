"""
Mermaid flowchart rendering
"""
from typing import List
import requests
import base64
from urllib.parse import quote

class MermaidRenderer:
    """Generate and render Mermaid flowcharts"""
    
    def __init__(self, use_api: bool = True):
        """
        Initialize Mermaid renderer
        
        Args:
            use_api: Use mermaid.ink API (free, no key) or local rendering
        """
        self.use_api = use_api
        self.api_url = "https://mermaid.ink/img/"
    
    def keywords_to_mermaid(
        self, 
        keywords: List[str], 
        relationships: List[tuple] = None,
        flowchart_type: str = "flowchart"
    ) -> str:
        """
        Convert keywords/terminologies and relationships to Mermaid syntax
        
        Args:
            keywords: List of keywords/terminologies
            relationships: List of (source_term, target_term) tuples showing conceptual flow
            flowchart_type: Type of flowchart ("graph", "flowchart")
            
        Returns:
            Mermaid diagram code
        """
        if flowchart_type == "flowchart":
            mermaid_code = "flowchart TD\n"
        else:
            mermaid_code = "graph TD\n"
        
        # Create node IDs from keywords (sanitize for Mermaid)
        node_map = {}
        nodes = []
        
        for i, keyword in enumerate(keywords, 1):
            # Clean keyword for node ID and label
            clean_keyword = keyword[:40].replace('"', "'").replace('\n', ' ').strip()
            node_id = f"term{i}"
            node_map[keyword] = node_id
            nodes.append(f'    {node_id}["{clean_keyword}"]')
        
        mermaid_code += "\n".join(nodes) + "\n"
        
        # Add edges based on relationships
        edges = []
        if relationships:
            for from_term, to_term in relationships:
                from_id = node_map.get(from_term)
                to_id = node_map.get(to_term)
                if from_id and to_id:
                    edges.append(f"    {from_id} --> {to_id}")
        else:
            # If no relationships, create sequential flow
            for i in range(len(keywords) - 1):
                edges.append(f"    term{i+1} --> term{i+2}")
        
        if edges:
            mermaid_code += "\n".join(edges)
        
        return mermaid_code
    
    def steps_to_mermaid(self, steps: List[str], flowchart_type: str = "graph") -> str:
        """
        Convert methodology steps to Mermaid syntax (legacy method for backward compatibility)
        
        Args:
            steps: List of methodology steps
            flowchart_type: Type of flowchart ("graph", "flowchart")
            
        Returns:
            Mermaid diagram code
        """
        # Treat steps as keywords with sequential relationships
        relationships = [(steps[i], steps[i+1]) for i in range(len(steps) - 1)]
        return self.keywords_to_mermaid(steps, relationships, flowchart_type)
    
    def render(self, mermaid_code: str, format: str = "svg") -> bytes:
        """
        Render Mermaid code to image
        
        Args:
            mermaid_code: Mermaid diagram code
            format: Output format ("svg", "png")
            
        Returns:
            Image bytes
        """
        if self.use_api:
            # Use mermaid.ink API (free, no authentication)
            encoded = base64.urlsafe_b64encode(mermaid_code.encode()).decode().rstrip('=')
            url = f"{self.api_url}{encoded}.{format}"
            
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"Mermaid API error: {response.status_code}")
        else:
            # Local rendering would require mermaid-cli or similar
            # For now, fallback to API
            self.use_api = True
            return self.render(mermaid_code, format)
    
    def generate_flowchart(
        self, 
        keywords: List[str], 
        relationships: List[tuple] = None,
        output_format: str = "svg"
    ) -> bytes:
        """
        Generate flowchart image from keywords and relationships
        
        Args:
            keywords: List of keywords/terminologies
            relationships: List of (source_term, target_term) tuples
            output_format: Output format ("svg", "png")
            
        Returns:
            Image bytes
        """
        mermaid_code = self.keywords_to_mermaid(keywords, relationships)
        return self.render(mermaid_code, output_format)

