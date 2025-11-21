# Model Training Guide

This directory contains scripts for fine-tuning LLM models using QLoRA.

## Setup

1. Install training dependencies:
```bash
cd backend/training
pip install -r requirements.txt
```

## Training

### Basic Usage

Train a model with default settings:
```bash
python train_qlora.py --model google/gemma-2b-it --output-dir ./models/adapters/gemma-2b
```

### Training on Different Models

**For Laptop (RTX 3050 4GB):**
```bash
python train_qlora.py --model google/gemma-2b-it --output-dir ./models/adapters/gemma-2b --epochs 3
```

**For Office PC (RTX 3060 12GB):**
```bash
python train_qlora.py --model mistralai/Mistral-7B-Instruct-v0.2 --output-dir ./models/adapters/mistral-7b --epochs 3
```

or

```bash
python train_qlora.py --model google/gemma-7b-it --output-dir ./models/adapters/gemma-7b --epochs 3
```

## Configuration

Edit `config.py` to adjust:
- LoRA parameters (rank, alpha, dropout)
- Training hyperparameters (learning rate, batch size, epochs)
- Quantization settings

## Data

Training data is automatically loaded from:
- `../../training_data/training_datasets/` - Pre-formatted instruction datasets
- `../../research_papers/research_papers/processed/` - Processed papers (optional)

## Output

Trained adapters are saved to the specified output directory. Use the adapter path in your application configuration.

