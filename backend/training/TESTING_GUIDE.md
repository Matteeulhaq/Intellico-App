# Testing Guide for Fine-Tuned Gemma 2B Model

This guide provides step-by-step instructions for testing your fine-tuned Gemma 2B model uploaded to HuggingFace.

## Prerequisites

1. Fine-tuned model uploaded to HuggingFace (repository ID)
2. HuggingFace token (if model is private)
3. Python environment with all dependencies installed
4. GPU available (recommended) or CPU

## Step 1: Configure Environment

1. Set your HuggingFace repository ID:
   ```bash
   export HUGGINGFACE_REPO_ID="your-username/your-model-name"
   ```

2. If your model is private, set your HuggingFace token:
   ```bash
   export HUGGINGFACE_TOKEN="your-hf-token"
   ```

   Or add to `.env` file:
   ```
   HUGGINGFACE_REPO_ID=your-username/your-model-name
   HUGGINGFACE_TOKEN=your-hf-token
   USE_HUGGINGFACE_REPO=true
   ```

## Step 2: Test Basic Model Loading

Test that the model loads correctly from HuggingFace:

```bash
cd backend/training
python test_model.py --repo-id your-username/your-model-name --token your-hf-token
```

**Expected Output:**
- ✓ Model loaded successfully
- ✓ GPU Memory information
- ✓ Basic inference test passes

**Troubleshooting:**
- If model fails to load, check:
  - Repository ID is correct
  - Token has access to the repository
  - Internet connection is available
  - Sufficient GPU memory

## Step 3: Test Task-Specific Functionality

Test each trained task:

```bash
python test_tasks.py --repo-id your-username/your-model-name --token your-hf-token
```

**Tests Performed:**
- ✓ Summarization
- ✓ Section Classification
- ✓ Metadata Extraction
- ✓ Keyword Extraction
- ✓ Keyword Relationship Extraction

**Expected Output:**
- All tasks should produce valid outputs
- JSON structures should be parseable
- Responses should be relevant to input

## Step 4: Performance Evaluation

Measure model performance:

```bash
python evaluate_model.py --repo-id your-username/your-model-name --token your-hf-token --runs 10 --duration 30
```

**Metrics Measured:**
- Inference latency (average, median, min, max)
- Memory usage (GPU VRAM)
- Throughput (requests per second)

**Expected Results:**
- Average latency: < 5 seconds per request
- Memory usage: Fits in available VRAM
- Throughput: > 0.2 requests/second

Results are saved to `evaluation_results.json`.

## Step 5: Compare with Base Model

Compare fine-tuned model with base Gemma 2B:

```bash
python compare_models.py --repo-id your-username/your-model-name --token your-hf-token
```

**Comparison:**
- Response quality differences
- Task-specific improvements
- Performance differences

## Step 6: Test API Integration

1. **Start the Flask server:**
   ```bash
   cd backend
   export ADAPTER_PATH=your-username/your-model-name
   export USE_HUGGINGFACE_REPO=true
   export HUGGINGFACE_TOKEN=your-hf-token
   python -m app.main
   ```

2. **In another terminal, run API tests:**
   ```bash
   cd backend/tests
   python test_api_integration.py --base-url http://localhost:2750 --pdf path/to/test.pdf
   ```

**Endpoints Tested:**
- `/health` - API health check
- `/api/upload` - Paper upload and indexing
- `/api/qa/<paper_id>` - Question answering
- `/api/flowchart/<paper_id>` - Flowchart generation
- `/api/summarize/<paper_id>` - Paper summarization

## Step 7: Manual Testing

### Test Upload Endpoint
```bash
curl -X POST http://localhost:2750/api/upload \
  -F "file=@path/to/paper.pdf"
```

### Test Question Answering
```bash
curl -X POST http://localhost:2750/api/qa/<paper_id> \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main methodology?"}'
```

### Test Flowchart Generation
```bash
curl http://localhost:2750/api/flowchart/<paper_id> \
  -o flowchart.svg
```

### Test Summarization
```bash
curl http://localhost:2750/api/summarize/<paper_id>
```

## Troubleshooting

### Model Loading Issues

**Error: "Model not found"**
- Verify repository ID is correct
- Check if model is public or you have access token

**Error: "Out of memory"**
- Reduce batch size
- Use CPU instead of GPU
- Close other applications using GPU

### API Issues

**Error: "Model not loaded"**
- Check environment variables are set
- Verify model loads in test scripts first
- Check Flask server logs

**Error: "Timeout"**
- Increase timeout values
- Check if model is responding
- Verify GPU is available

### Performance Issues

**Slow inference:**
- Check GPU utilization
- Verify quantization is enabled
- Consider using smaller max_new_tokens

**High memory usage:**
- Verify 4-bit quantization is enabled
- Check for memory leaks
- Restart server if needed

## Success Criteria

All tests should pass:
- ✓ Model loads from HuggingFace
- ✓ All tasks produce valid outputs
- ✓ API endpoints respond correctly
- ✓ Inference speed is acceptable (< 5s)
- ✓ Memory usage is within limits

## Next Steps

After successful testing:
1. Deploy model to production
2. Monitor performance metrics
3. Collect user feedback
4. Iterate on improvements

