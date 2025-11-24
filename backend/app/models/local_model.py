"""
Local model loader and inference
"""
import os
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig
)
from peft import PeftModel
import json
from typing import Optional, Dict, Any

class LocalModel:
    """Load and run inference with fine-tuned local models"""
    
    def __init__(
        self, 
        base_model_name: str, 
        adapter_path: Optional[str] = None, 
        device: str = "auto",
        hf_token: Optional[str] = None,
        use_hf_repo: bool = False
    ):
        """
        Initialize local model
        
        Args:
            base_model_name: HuggingFace model name (e.g., "google/gemma-2b-it")
            adapter_path: Path to fine-tuned LoRA adapter (local path or HuggingFace repo ID)
            device: Device to use ("auto", "cuda", "cpu")
            hf_token: HuggingFace token for private models
            use_hf_repo: Whether adapter_path is a HuggingFace repository ID
        """
        self.base_model_name = base_model_name
        self.adapter_path = adapter_path
        self.device = device
        self.hf_token = hf_token
        self.use_hf_repo = use_hf_repo
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load model and tokenizer"""
        print(f"Loading base model: {self.base_model_name}")
        
        # Configure quantization for inference
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            quantization_config=bnb_config,
            device_map=self.device,
            trust_remote_code=True,
        )
        
        # Load adapter if provided
        if self.adapter_path:
            if self.use_hf_repo:
                # Load from HuggingFace repository
                print(f"Loading adapter from HuggingFace: {self.adapter_path}")
                from peft import PeftConfig
                self.model = PeftModel.from_pretrained(
                    self.model, 
                    self.adapter_path,
                    token=self.hf_token
                )
            elif os.path.exists(self.adapter_path):
                # Load from local path
                print(f"Loading adapter from local path: {self.adapter_path}")
                self.model = PeftModel.from_pretrained(self.model, self.adapter_path)
            else:
                print(f"Warning: Adapter path not found: {self.adapter_path}")
            
            # Merge adapter for faster inference (optional - can keep separate for flexibility)
            # self.model = self.model.merge_and_unload()
        
        self.model.eval()
        print("Model loaded successfully")
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> str:
        """
        Generate text from prompt
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            do_sample: Whether to use sampling
            
        Returns:
            Generated text
        """
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove prompt from output
        if prompt in generated_text:
            generated_text = generated_text.replace(prompt, "").strip()
        
        return generated_text
    
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from paper text"""
        from .prompt_templates import PromptTemplates
        
        prompt = PromptTemplates.metadata_extraction(text)
        response = self.generate(prompt, max_new_tokens=256, temperature=0.3)
        
        # Try to parse JSON response
        try:
            # Extract JSON from response if wrapped in text
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                metadata = json.loads(json_str)
            else:
                metadata = json.loads(response)
        except:
            # Fallback: return raw response
            metadata = {"raw_response": response}
        
        return metadata
    
    def classify_section(self, text: str) -> str:
        """Classify text section"""
        from .prompt_templates import PromptTemplates
        
        prompt = PromptTemplates.section_classification(text)
        response = self.generate(prompt, max_new_tokens=50, temperature=0.1)
        
        # Clean response
        response = response.strip().lower()
        valid_sections = ["abstract", "introduction", "methodology", "results", "discussion", "conclusion", "references"]
        
        for section in valid_sections:
            if section in response:
                return section
        
        return response

