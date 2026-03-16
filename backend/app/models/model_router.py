"""
Model router - selects appropriate model for tasks
"""
import os
import torch
from typing import Optional
from .local_model import LocalModel

class ModelRouter:
    """Route requests to appropriate models"""
    
    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path: Optional[str] = None,
        hf_token: Optional[str] = None,
        use_hf_repo: bool = False
    ):
        """
        Initialize model router
        
        Args:
            base_model_name: Base model to use
            adapter_path: Path to fine-tuned adapter (local or HuggingFace repo)
            hf_token: HuggingFace token for private models
            use_hf_repo: Whether adapter_path is a HuggingFace repository ID
        """
        self.model = LocalModel(
            base_model_name, 
            adapter_path,
            hf_token=hf_token,
            use_hf_repo=use_hf_repo
        )
    
    def answer_question(self, question: str, context: Optional[str] = None) -> str:
        """Answer question using model with optional RAG context"""
        from .prompt_templates import PromptTemplates

        prompt = PromptTemplates.question_answering(question, context)
        response = self.model.generate(prompt, max_new_tokens=512, temperature=0.7)

        return response.strip()
    
    def summarize(self, text: str) -> str:
        """Summarize text"""
        from .prompt_templates import PromptTemplates

        # Limit text length
        if len(text) > 2000:
            text = text[:2000] + "..."

        prompt = PromptTemplates.summarization(text)
        response = self.model.generate(prompt, max_new_tokens=256, temperature=0.5)

        return response.strip()
    
    def extract_metadata(self, text: str) -> dict:
        """Extract metadata from text"""
        result = self.model.extract_metadata(text)

        return result
    
    def extract_methodology(self, text: str) -> list:
        """Extract methodology steps from text"""
        from .prompt_templates import PromptTemplates

        # Limit text length
        if len(text) > 3000:
            text = text[:3000] + "..."

        prompt = PromptTemplates.methodology_extraction(text)
        response = self.model.generate(prompt, max_new_tokens=512, temperature=0.3)

        # Parse steps (one per line)
        steps = [step.strip() for step in response.split('\n') if step.strip()]
        return steps
    
    def extract_keyword_relationships(self, text: str) -> str:
        """Extract keywords/terminologies and their relationships from text"""
        from .prompt_templates import PromptTemplates

        # Limit text length to prevent OOM
        if len(text) > 4000:
            text = text[:4000] + "..."

        prompt = PromptTemplates.keyword_relationship_extraction(text)
        response = self.model.generate(prompt, max_new_tokens=1024, temperature=0.3)

        return response

    def summarize_section(self, section_name: str, section_text: str) -> str:
        """Summarize a single section with section-specific prompts"""
        from .prompt_templates import PromptTemplates

        # Reuse existing truncation pattern
        if len(section_text) > 3000:
            section_text = section_text[:3000] + "..."

        prompt = PromptTemplates.section_summarization(section_name, section_text)
        response = self.model.generate(prompt, max_new_tokens=300, temperature=0.3)

        return response.strip()

    def extract_key_findings(self, paper_id: str, rag_chain) -> dict:
        """
        Extract key findings using optimized RAG query with parallel processing
        """
        from concurrent.futures import ThreadPoolExecutor

        # OPTIMIZATION: Combine all queries into single RAG search
        combined_query = "main findings and conclusions methodology approach study design clinical significance implications"

        # Single RAG query with more chunks to get comprehensive context
        result = rag_chain.query(combined_query, paper_id=paper_id, top_k=10)

        # Get comprehensive context
        context = result['context'][:2000]  # Increased context window

        # OPTIMIZATION: Parallel summarization of each aspect
        def summarize_aspect(key_and_query):
            """Helper function for parallel processing"""
            key, query = key_and_query
            # Use targeted prompt for each aspect
            from .prompt_templates import PromptTemplates
            prompt = f"{query}: {context}"
            summary = self.summarize(prompt)
            return key, summary

        queries = {
            'main_findings': "main findings and conclusions",
            'methodology': "methodology approach and study design",
            'clinical_significance': "clinical significance and implications"
        }

        key_findings = {}

        # Use ThreadPoolExecutor for parallel summarization (3x faster)
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all summarization tasks
            futures = [executor.submit(summarize_aspect, (k, v)) for k, v in queries.items()]

            # Collect results as they complete
            for future in futures:
                key, summary = future.result()
                key_findings[key] = summary

        # Clear cache once at the end instead of after each query
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return key_findings

    def generate_comprehensive_summary(
        self,
        section_summaries: dict,
        key_findings: dict
    ) -> str:
        """Generate final comprehensive summary from all components"""
        from .prompt_templates import PromptTemplates

        prompt = PromptTemplates.comprehensive_synthesis(
            section_summaries,
            key_findings
        )

        # Generate longer comprehensive summary
        response = self.model.generate(
            prompt,
            max_new_tokens=1500,
            temperature=0.4
        )

        return response.strip()

