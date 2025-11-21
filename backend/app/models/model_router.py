"""
Model router - selects appropriate model for tasks
"""
import os
from typing import Optional
from .local_model import LocalModel

class ModelRouter:
    """Route requests to appropriate models"""
    
    def __init__(
        self,
        base_model_name: str = "google/gemma-2b-it",
        adapter_path: Optional[str] = None
    ):
        """
        Initialize model router
        
        Args:
            base_model_name: Base model to use
            adapter_path: Path to fine-tuned adapter
        """
        self.model = LocalModel(base_model_name, adapter_path)
    
    def answer_question(self, question: str, context: Optional[str] = None) -> str:
        """Answer question using model with optional RAG context"""
        from .prompt_templates import PromptTemplates
        
        prompt = PromptTemplates.question_answering(question, context)
        response = self.model.generate(prompt, max_new_tokens=512, temperature=0.7)
        return response.strip()
    
    def summarize(self, text: str) -> str:
        """Summarize text"""
        from .prompt_templates import PromptTemplates
        
        prompt = PromptTemplates.summarization(text)
        response = self.model.generate(prompt, max_new_tokens=256, temperature=0.5)
        return response.strip()
    
    def extract_metadata(self, text: str) -> dict:
        """Extract metadata from text"""
        return self.model.extract_metadata(text)
    
    def extract_methodology(self, text: str) -> list:
        """Extract methodology steps from text"""
        from .prompt_templates import PromptTemplates
        
        prompt = PromptTemplates.methodology_extraction(text)
        response = self.model.generate(prompt, max_new_tokens=512, temperature=0.3)
        
        # Parse steps (one per line)
        steps = [step.strip() for step in response.split('\n') if step.strip()]
        return steps
    
    def extract_keyword_relationships(self, text: str) -> str:
        """Extract keywords/terminologies and their relationships from text"""
        from .prompt_templates import PromptTemplates
        
        prompt = PromptTemplates.keyword_relationship_extraction(text)
        response = self.model.generate(prompt, max_new_tokens=1024, temperature=0.3)
        return response

