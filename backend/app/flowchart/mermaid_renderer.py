"""
Mermaid flowchart rendering
"""
from typing import List
import requests
import base64
import re
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
        self.api_url_img = "https://mermaid.ink/img/"  # For PNG/JPEG
        self.api_url_svg = "https://mermaid.ink/svg/"  # For SVG
    
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
        # Validate and filter keywords
        if not keywords:
            return "flowchart TD\n    empty[\"No keywords found\"]\n"
        
        # Filter out empty or invalid keywords
        valid_keywords = []
        for keyword in keywords:
            if keyword and isinstance(keyword, str):
                cleaned = keyword.strip()
                if cleaned and len(cleaned) > 0:
                    valid_keywords.append(cleaned)
        
        if not valid_keywords:
            return "flowchart TD\n    empty[\"No valid keywords found\"]\n"
        
        # Limit to prevent overly large diagrams
        valid_keywords = valid_keywords[:20]
        
        if flowchart_type == "flowchart":
            mermaid_code = "flowchart TD\n"
        else:
            mermaid_code = "graph TD\n"
        
        # Create node IDs from keywords (sanitize for Mermaid)
        node_map = {}
        nodes = []
        
        for i, keyword in enumerate(valid_keywords, 1):
            # Sanitize keyword for Mermaid node label
            # Remove or replace characters that break Mermaid syntax
            clean_keyword = keyword[:50]  # Limit length
            # Replace problematic characters
            clean_keyword = clean_keyword.replace('\n', ' ').replace('\r', ' ')
            clean_keyword = clean_keyword.replace('"', "'")  # Replace double quotes
            clean_keyword = clean_keyword.replace('`', "'")  # Replace backticks
            clean_keyword = clean_keyword.replace('{', '(').replace('}', ')')  # Replace braces
            clean_keyword = clean_keyword.replace('[', '(').replace(']', ')')  # Replace brackets in labels
            clean_keyword = re.sub(r'[<>]', '', clean_keyword)  # Remove angle brackets
            clean_keyword = clean_keyword.strip()
            
            # Skip if empty after cleaning
            if not clean_keyword:
                continue
            
            node_id = f"term{i}"
            node_map[keyword] = node_id
            # Use parentheses for node labels to avoid quote issues
            nodes.append(f'    {node_id}("{clean_keyword}")')
        
        if not nodes:
            return "flowchart TD\n    empty[\"No valid keywords after sanitization\"]\n"
        
        mermaid_code += "\n".join(nodes) + "\n"
        
        # Add edges based on relationships
        edges = []
        if relationships:
            for from_term, to_term in relationships:
                from_id = node_map.get(from_term)
                to_id = node_map.get(to_term)
                # Only add edge if both nodes exist
                if from_id and to_id and from_id != to_id:
                    edges.append(f"    {from_id} --> {to_id}")
        else:
            # If no relationships, create sequential flow
            for i in range(len(nodes) - 1):
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
        # Validate mermaid code
        if not mermaid_code or not mermaid_code.strip():
            raise ValueError("Empty Mermaid code provided")
        
        # Log the mermaid code for debugging
        print(f"Generated Mermaid code:\n{mermaid_code}\n")
        
        if self.use_api:
            # Use mermaid.ink API (free, no authentication)
            encoded = base64.urlsafe_b64encode(mermaid_code.encode()).decode().rstrip('=')
            
            # Use correct endpoint based on format
            if format.lower() == "svg":
                url = f"{self.api_url_svg}{encoded}"
            else:
                url = f"{self.api_url_img}{encoded}.{format}"
            
            print(f"Requesting from: {url[:100]}...")  # Log first 100 chars of URL
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Check if response is an error image (JPEG/PNG error message)
                content_type = response.headers.get('Content-Type', '')
                if format.lower() == "svg" and 'image' in content_type.lower() and 'svg' not in content_type.lower():
                    # Got an image but expected SVG - likely an error image
                    print(f"Warning: Got image ({content_type}) instead of SVG. Mermaid code may have syntax errors.")
                    print(f"Mermaid code was:\n{mermaid_code}")
                    raise ValueError(f"Mermaid syntax error - API returned error image. Check the generated Mermaid code.")
                
                return response.content
            else:
                error_msg = f"Mermaid API error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text[:200]}"
                print(f"Error: {error_msg}")
                print(f"Mermaid code was:\n{mermaid_code}")
                raise Exception(error_msg)
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


