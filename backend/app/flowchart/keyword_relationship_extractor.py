"""
Extract keywords/terminologies and their relationships using fine-tuned model
"""
from typing import List, Dict, Tuple
import json
import re
import torch
from ..models.model_router import ModelRouter

class KeywordRelationshipExtractor:
    """Extract keywords/terminologies and their conceptual relationships from research papers"""
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self.max_text_length = 4000  # Limit text length to prevent OOM
    
    def extract_keywords_and_relationships(
        self, 
        paper_text: str, 
        sections: Dict[str, str] = None
    ) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Extract keywords/terminologies and their relationships from paper
        
        Args:
            paper_text: Full paper text
            sections: Optional dictionary of sections (abstract, introduction, etc.)
            
        Returns:
            Tuple of (keywords_list, relationships_list)
            relationships_list contains tuples of (source_term, target_term)
        """
        try:
            # Use full text or combine sections
            text_to_use = paper_text
            if sections:
                # Prioritize abstract and introduction for key terms
                priority_sections = ['abstract', 'introduction', 'methodology', 'results']
                combined_text = []
                for section in priority_sections:
                    if section in sections:
                        combined_text.append(sections[section])
                if combined_text:
                    text_to_use = '\n\n'.join(combined_text)
            
            # Limit text length to prevent OOM
            if len(text_to_use) > self.max_text_length:
                text_to_use = text_to_use[:self.max_text_length] + "..."
            
            # Extract keywords and relationships using model
            result = self.model_router.extract_keyword_relationships(text_to_use)
            
            # Parse result
            keywords, relationships = self._parse_relationships(result)
            
            # Clear GPU cache after processing
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return keywords, relationships
        except Exception as e:
            # Clear GPU cache on error
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise e
    
    def _parse_relationships(self, model_output: str) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Parse model output to extract keywords and relationships
        
        Expected format:
        - JSON: {"keywords": [...], "relationships": [{"from": "...", "to": "..."}, ...]}
        - Text: keywords on lines, relationships as "term1 -> term2"
        """
        keywords = []
        relationships = []
        
        # Try to parse as JSON first
        try:
            # Extract JSON if wrapped in text
            json_match = re.search(r'\{[^{}]*"keywords"[^{}]*\}', model_output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                keywords = data.get('keywords', [])
                rels = data.get('relationships', [])
                for rel in rels:
                    if isinstance(rel, dict):
                        relationships.append((rel.get('from', ''), rel.get('to', '')))
                    elif isinstance(rel, str) and '->' in rel:
                        parts = rel.split('->')
                        if len(parts) == 2:
                            relationships.append((parts[0].strip(), parts[1].strip()))
        except:
            pass
        
        # If JSON parsing failed, try text parsing
        if not keywords and not relationships:
            lines = model_output.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for relationship (term1 -> term2 or term1 → term2)
                if '->' in line or '→' in line:
                    parts = re.split(r'[-→>]+', line, maxsplit=1)
                    if len(parts) == 2:
                        from_term = parts[0].strip()
                        to_term = parts[1].strip()
                        if from_term and to_term:
                            relationships.append((from_term, to_term))
                            # Add terms to keywords if not already present
                            if from_term not in keywords:
                                keywords.append(from_term)
                            if to_term not in keywords:
                                keywords.append(to_term)
                # Check for keyword list (comma-separated or line-separated)
                elif ',' in line:
                    terms = [t.strip() for t in line.split(',')]
                    keywords.extend([t for t in terms if t and len(t) > 2])
                elif len(line) > 3 and line[0].isupper():
                    # Potential keyword (starts with capital, reasonable length)
                    keywords.append(line)
        
        # Clean and deduplicate keywords
        keywords = list(set([k.strip() for k in keywords if k.strip() and len(k.strip()) > 2]))
        
        # Clean relationships
        cleaned_relationships = []
        for from_term, to_term in relationships:
            from_term = from_term.strip()
            to_term = to_term.strip()
            if from_term and to_term and from_term != to_term:
                cleaned_relationships.append((from_term, to_term))
        
        return keywords, cleaned_relationships
    
    def build_concept_flow(self, keywords: List[str], relationships: List[Tuple[str, str]]) -> List[str]:
        """
        Build ordered concept flow from keywords and relationships
        
        Args:
            keywords: List of keywords/terminologies
            relationships: List of (source, target) tuples
            
        Returns:
            Ordered list of terms showing the flow
        """
        if not relationships:
            # If no relationships, return keywords in order they appear
            return keywords[:10]  # Limit to top 10
        
        # Build graph
        graph = {}
        in_degree = {term: 0 for term in keywords}
        
        # Initialize graph
        for term in keywords:
            graph[term] = []
        
        # Add edges
        for from_term, to_term in relationships:
            if from_term in graph and to_term in graph:
                graph[from_term].append(to_term)
                if to_term in in_degree:
                    in_degree[to_term] += 1
        
        # Topological sort to find flow (terms with no incoming edges first)
        ordered_terms = []
        queue = [term for term, degree in in_degree.items() if degree == 0]
        
        while queue:
            term = queue.pop(0)
            ordered_terms.append(term)
            
            for neighbor in graph.get(term, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Add remaining terms
        for term in keywords:
            if term not in ordered_terms:
                ordered_terms.append(term)
        
        return ordered_terms[:15]  # Limit to top 15 terms

