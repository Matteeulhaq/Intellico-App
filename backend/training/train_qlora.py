"""
QLoRA Fine-tuning Script for Gemma/Mistral Models
"""

import os
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import json

from config import TrainingConfig
from data_loader import TrainingDataLoader


def setup_model_and_tokenizer(config: TrainingConfig):
    """Setup model with 4-bit quantization and tokenizer"""

    # Configure 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=config.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype=getattr(torch, config.bnb_4bit_compute_dtype),
        bnb_4bit_use_double_quant=config.bnb_4bit_use_double_quant,
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(config.base_model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

    # Load model with quantization
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_name,
        quantization_config=bnb_config,
        device_map=config.device_map,
        trust_remote_code=True,
    )

    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)

    # Configure LoRA
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=config.target_modules,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)

    # Enable gradient checkpointing
    if config.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    return model, tokenizer


def tokenize_dataset(dataset: Dataset, tokenizer, max_length: int = 2048):
    """Tokenize dataset"""

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
            padding="max_length",
        )

    tokenized = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,
    )
    return tokenized


def train(config: TrainingConfig):
    """Main training function"""

    print(f"Loading training data from {config.training_data_dir}...")
    data_loader = TrainingDataLoader(
        training_data_dir=config.training_data_dir,
        processed_papers_dir=config.processed_papers_dir,
    )

    # Load all datasets
    dataset = data_loader.load_all_datasets()
    print(f"Loaded {len(dataset)} training examples")

    # Split into train/test
    dataset_split = data_loader.train_test_split(dataset, test_size=0.1)
    train_dataset = dataset_split["train"]
    eval_dataset = dataset_split["test"]

    print(f"Train examples: {len(train_dataset)}, Eval examples: {len(eval_dataset)}")

    # Setup model and tokenizer
    print(f"Loading model: {config.base_model_name}")
    model, tokenizer = setup_model_and_tokenizer(config)

    # Tokenize datasets
    print("Tokenizing datasets...")
    train_tokenized = tokenize_dataset(train_dataset, tokenizer)
    eval_tokenized = tokenize_dataset(eval_dataset, tokenizer)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        eval_steps=config.eval_steps,
        eval_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        fp16=config.fp16,
        optim=config.optim,
        report_to="tensorboard",
        logging_dir=f"{config.output_dir}/logs",
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=eval_tokenized,
        data_collator=data_collator,
    )

    # Train
    print("Starting training...")
    trainer.train()

    # Save model
    print(f"Saving model to {config.output_dir}")
    trainer.save_model()
    tokenizer.save_pretrained(config.output_dir)

    # Save training config
    config_dict = {
        "base_model": config.base_model_name,
        "lora_r": config.lora_r,
        "lora_alpha": config.lora_alpha,
        "lora_dropout": config.lora_dropout,
        "target_modules": config.target_modules,
    }
    with open(f"{config.output_dir}/training_config.json", "w") as f:
        json.dump(config_dict, f, indent=2)

    print("Training completed!")


if __name__ == "__main__":
    import argparse

    torch.cuda.empty_cache()

    parser = argparse.ArgumentParser(description="Train model with QLoRA")
    parser.add_argument(
        "--model", type=str, default="google/gemma-2b-it", help="Base model name"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./models/adapters/gemma-2b",
        help="Output directory",
    )
    parser.add_argument(
        "--epochs", type=int, default=3, help="Number of training epochs"
    )

    args = parser.parse_args()

    config = TrainingConfig(
        base_model_name=args.model,
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
    )

    train(config)
