# Quick Start Testing Guide

## Quick Test Commands

Replace `your-username/your-model-name` with your actual HuggingFace repository ID.

### 1. Basic Model Loading Test
```bash
cd backend/training
python test_model.py --repo-id your-username/your-model-name --token YOUR_HF_TOKEN
```

### 2. Task-Specific Tests
```bash
python test_tasks.py --repo-id your-username/your-model-name --token YOUR_HF_TOKEN
```

### 3. Performance Evaluation
```bash
python evaluate_model.py --repo-id your-username/your-model-name --token YOUR_HF_TOKEN
```

### 4. Compare with Base Model
```bash
python compare_models.py --repo-id your-username/your-model-name --token YOUR_HF_TOKEN
```

### 5. API Integration Test
```bash
# Terminal 1: Start server
cd backend
export ADAPTER_PATH=your-username/your-model-name
export USE_HUGGINGFACE_REPO=true
export HUGGINGFACE_TOKEN=YOUR_HF_TOKEN
python -m app.main

# Terminal 2: Run tests
cd backend/tests
python test_api_integration.py --base-url http://localhost:2750 --pdf path/to/test.pdf
```

## Environment Variables

Add to `.env` file:
```
ADAPTER_PATH=your-username/your-model-name
USE_HUGGINGFACE_REPO=true
HUGGINGFACE_TOKEN=your-hf-token
BASE_MODEL_NAME=google/gemma-2b-it
```

## Expected Results

- ✓ Model loads successfully
- ✓ All tasks produce valid outputs
- ✓ API endpoints respond correctly
- ✓ Inference latency < 5 seconds
- ✓ Memory usage fits in VRAM

For detailed instructions, see `TESTING_GUIDE.md`.

