"""
Prompt templates for different tasks
"""
from typing import Dict, Optional

class PromptTemplates:
    """Prompt templates for fine-tuned models"""
    
    @staticmethod
    def format_instruction(instruction: str, input_text: str) -> str:
        """Format instruction following prompt for Qwen (ChatML format)"""
        return f"""<|im_start|>user
{instruction}

{input_text}<|im_end|>
<|im_start|>assistant
"""
    
    @staticmethod
    def question_answering(question: str, context: Optional[str] = None) -> str:
        """Template for question answering with RAG context"""
        if context:
            prompt = f"""<|im_start|>user
Answer the following question based on the provided context from a research paper. Provide a direct, concise answer based only on information explicitly stated in the context. Do not infer or speculate.

Context:
{context}

Question: {question}<|im_end|>
<|im_start|>assistant
"""
        else:
            prompt = f"""<|im_start|>user
Answer the following question directly and concisely: {question}<|im_end|>
<|im_start|>assistant
"""
        return prompt
    
    @staticmethod
    def summarization(text: str) -> str:
        """Template for text summarization"""
        return PromptTemplates.format_instruction(
            "Summarize the following research paper text:",
            text
        )
    
    @staticmethod
    def metadata_extraction(text: str) -> str:
        """Template for metadata extraction"""
        return PromptTemplates.format_instruction(
            "Extract metadata from the following research paper text. Return a JSON object with: title, authors, abstract, keywords, publication_date.",
            text
        )
    
    @staticmethod
    def section_classification(text: str) -> str:
        """Template for section classification"""
        return PromptTemplates.format_instruction(
            "Classify the following text section from a research paper. Choose from: abstract, introduction, methodology, results, discussion, conclusion, references.",
            text
        )
    
    @staticmethod
    def keyword_extraction(text: str) -> str:
        """Template for keyword extraction"""
        return PromptTemplates.format_instruction(
            "Extract key terms and keywords from the following research paper text. Return a comma-separated list of keywords.",
            text
        )
    
    @staticmethod
    def methodology_extraction(text: str) -> str:
        """Template for extracting methodology/workflow steps"""
        return PromptTemplates.format_instruction(
            "Extract the methodology and workflow steps from the following research paper text. List each step in order, one per line.",
            text
        )
    
    @staticmethod
    def keyword_relationship_extraction(text: str) -> str:
        """Template for extracting keywords/terminologies and their conceptual relationships"""
        return PromptTemplates.format_instruction(
            """Extract key terms, keywords, and terminologies from the following research paper text, along with their conceptual relationships. 
Identify which terms/concepts lead to or originate from other terms. 

Return a JSON object with:
- "keywords": list of key terms/terminologies found in the paper
- "relationships": list of objects with "from" and "to" fields showing conceptual flow (e.g., {"from": "Term A", "to": "Term B"} means Term A leads to or is the origin of Term B)

Focus on:
- Technical terms and domain-specific terminology
- Concepts that build upon or derive from other concepts
- The conceptual evolution: which terms lead to which other terms""",
            text
        )

