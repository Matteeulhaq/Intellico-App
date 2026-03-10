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
        base_instruction = """
You are a dental research assistant helping users understand DENTAL RESEARCH PAPERS.
- Answer questions about the research paper provided in the context
- The paper has been validated as being related to dentistry or oral health
- Provide direct, concise answers based only on information in the context
- For questions about study design, methodology, statistics, or results - answer based on the paper
- If the question is completely unrelated to the paper or dentistry, respond with: "Sorry I cannot help you with that"
- Do not provide medical advice beyond what's in the research paper
"""

        if context:
            prompt = f"""<|im_start|>user
{base_instruction}

Context from dental research paper:
{context}

Question: {question}<|im_end|>
<|im_start|>assistant
"""
        else:
            prompt = f"""<|im_start|>user
{base_instruction}

Question: {question}<|im_end|>
<|im_start|>assistant
"""
        return prompt
    
    @staticmethod
    def summarization(text: str) -> str:
        """Template for text summarization"""
        instruction = """
You are a dental research assistant. Summarize the following DENTAL RESEARCH PAPER text.
- ONLY summarize if the content is related to dentistry or oral health
- If the content is not about dentistry, respond with: "Sorry I cannot help you with that"
- Focus on key findings, methodology, and conclusions related to dental science
"""
        return PromptTemplates.format_instruction(instruction, text)
    
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
        instruction = """
You are a dental research assistant. Extract the methodology and workflow steps from the following DENTAL RESEARCH PAPER text.
- ONLY extract if the content is related to dentistry or oral health
- If the content is not about dentistry, respond with: "Sorry I cannot help you with that"
- List each step in order, one per line, focusing on dental research procedures
"""
        return PromptTemplates.format_instruction(instruction, text)
    
    @staticmethod
    def keyword_relationship_extraction(text: str) -> str:
        """Template for extracting keywords/terminologies and their conceptual relationships"""
        instruction = """
You are a dental research assistant. Extract key terms, keywords, and terminologies from the following DENTAL RESEARCH PAPER text, along with their conceptual relationships.
- ONLY extract if the content is related to dentistry or oral health
- If the content is not about dentistry, respond with: "Sorry I cannot help you with that"
- Identify which terms/concepts lead to or originate from other terms

Return a JSON object with:
- "keywords": list of key terms/terminologies found in the paper
- "relationships": list of objects with "from" and "to" fields showing conceptual flow (e.g., {"from": "Term A", "to": "Term B"} means Term A leads to or is the origin of Term B)

Focus on:
- DENTAL and ORAL HEALTH technical terms and domain-specific terminology
- Concepts that build upon or derive from other concepts
- The conceptual evolution: which terms lead to which other terms
"""
        return PromptTemplates.format_instruction(instruction, text)

    @staticmethod
    def section_summarization(section_name: str, text: str) -> str:
        """Template for summarizing a specific section"""
        instruction = f"""
You are a dental research assistant. Summarize the {section_name.upper()} section of this DENTAL RESEARCH PAPER.
- Focus on key information specific to {section_name} section
- ONLY summarize if the content is related to dentistry or oral health
- If the content is not about dentistry, respond with: "Sorry I cannot help you with that"
- Be concise but capture the main points (2-4 sentences)
"""
        return PromptTemplates.format_instruction(instruction, text)

    @staticmethod
    def comprehensive_synthesis(section_summaries: dict, key_findings: dict) -> str:
        """Template for synthesizing comprehensive summary"""
        instruction = """
You are a dental research assistant. Create a comprehensive summary of a DENTAL RESEARCH PAPER by synthesizing the following section summaries and key findings.

Your summary should include:
1. **Study Overview**: Brief description of the research purpose and approach (2-3 sentences)
2. **Methodology**: Key methods and study design (2-3 sentences)
3. **Main Findings**: Primary results and statistical outcomes (3-4 sentences)
4. **Clinical Implications**: Practical significance for dental practice (2-3 sentences)
5. **Conclusions**: Main conclusions and future directions (2-3 sentences)

- ONLY summarize if the content is related to dentistry or oral health
- If the content is not about dentistry, respond with: "Sorry I cannot help you with that"
- Be concise but comprehensive
- Use clear, professional language suitable for dental professionals
"""

        # Format section summaries
        sections_text = "\n\n".join([
            f"## {section.title()}\n{summary}"
            for section, summary in section_summaries.items()
        ])

        # Format key findings
        findings_text = "\n\n".join([
            f"## {query.replace('_', ' ').title()}\n{finding}"
            for query, finding in key_findings.items()
        ])

        combined_context = f"""SECTION SUMMARIES:
{sections_text}

KEY FINDINGS:
{findings_text}
"""

        return PromptTemplates.format_instruction(instruction, combined_context)

