"""
Training configuration for QLoRA fine-tuning
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TrainingConfig:
    """Configuration for model training"""

    # Model settings
    base_model_name: str = (
        "Qwen/Qwen2.5-1.5B-Instruct"  # SLM optimized for RAG with fine-tuning
    )
    output_dir: str = "./models/adapters"

    # QLoRA settings
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: Optional[list] = None  # Auto-detect for Qwen/Gemma/Mistral

    # Quantization
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True

    # Training hyperparameters
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    warmup_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500

    # Memory optimization
    gradient_checkpointing: bool = True
    fp16: bool = True
    optim: str = "paged_adamw_8bit"

    # Data paths
    training_data_dir: str = "../../training_data/training_datasets"
    processed_papers_dir: str = "../../research_papers/research_papers/processed"

    # Device
    device_map: str = "auto"  # Will auto-detect GPU

    def __post_init__(self):
        """Set target modules based on model"""
        if self.target_modules is None:
            if "qwen" in self.base_model_name.lower():
                # Qwen models use same target modules as Gemma/Mistral
                self.target_modules = [
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ]
            elif "gemma" in self.base_model_name.lower():
                self.target_modules = [
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ]
            elif "mistral" in self.base_model_name.lower():
                self.target_modules = [
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ]
            else:
                # Default for most transformer models
                self.target_modules = ["q_proj", "v_proj"]
