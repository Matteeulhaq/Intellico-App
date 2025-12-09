"""
Test basic model loading and inference from HuggingFace
"""
import os
import sys
import time
import torch
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.local_model import LocalModel
from app.config import Config
from transformers import BitsAndBytesConfig

def test_model_loading(hf_repo_id: str, hf_token: str = None):
    """
    Test loading model from HuggingFace
    
    Args:
        hf_repo_id: HuggingFace repository ID (e.g., "username/model-name")
        hf_token: HuggingFace token (optional, for private models)
    """
    print("=" * 60)
    print("Testing Model Loading from HuggingFace")
    print("=" * 60)
    
    base_model = "Qwen/Qwen2.5-1.5B-Instruct"
    
    print(f"\n1. Loading base model: {base_model}")
    print(f"2. Loading fine-tuned adapter from: {hf_repo_id}")
    
    # Check memory usage BEFORE loading
    initial_memory_allocated = 0
    initial_memory_reserved = 0
    if torch.cuda.is_available():
        print("\nGPU Memory - Before loading:")
        initial_memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
        initial_memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
        print(f"  Allocated: {initial_memory_allocated:.2f} GB")
        print(f"  Reserved: {initial_memory_reserved:.2f} GB")
    
    # Configure 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    
    # Configure max_memory limits (RTX 3050 with 16GB RAM)
    max_memory = {
        0: "4000MB",   # GPU VRAM
        "cpu": "8000MB"
    }
    
    try:
        start_time = time.time()
        
        model = LocalModel(
            base_model_name=base_model,
            adapter_path=hf_repo_id,
            use_hf_repo=True,
            hf_token=hf_token,
            quantization_config=bnb_config,
            max_memory=max_memory
        )
        
        load_time = time.time() - start_time
        print(f"\n✓ Model loaded successfully in {load_time:.2f} seconds")
        
        # Check memory usage AFTER loading
        if torch.cuda.is_available():
            print("\nGPU Memory - After loading:")
            memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
            print(f"  Allocated: {memory_allocated:.2f} GB")
            print(f"  Reserved: {memory_reserved:.2f} GB")
            memory_increase = memory_allocated - initial_memory_allocated
            print(f"  Memory increase: {memory_increase:.2f} GB")
        
        return model
        
    except Exception as e:
        print(f"\n✗ Error loading model: {e}")
        
        # Print memory context on error
        if torch.cuda.is_available():
            print("\nGPU Memory - At error time:")
            memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
            print(f"  Allocated: {memory_allocated:.2f} GB")
            print(f"  Reserved: {memory_reserved:.2f} GB")
        
        import traceback
        traceback.print_exc()
        return None

def test_basic_inference(model: LocalModel):
    """Test basic text generation"""
    print("\n" + "=" * 60)
    print("Testing Basic Inference")
    print("=" * 60)
    
    test_prompt = "<|im_start|>user\nHello, how are you?<|im_end|>\n<|im_start|>assistant\n"
    
    try:
        start_time = time.time()
        response = model.generate(
            test_prompt,
            max_new_tokens=50,
            temperature=0.7
        )
        inference_time = time.time() - start_time
        
        print(f"✓ Inference completed in {inference_time:.2f} seconds")
        print(f"✓ Response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during inference: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test model loading from HuggingFace")
    parser.add_argument("--repo-id", type=str, default=os.getenv("ADAPTER_PATH"), help="HuggingFace repository ID (or set ADAPTER_PATH env var)")
    parser.add_argument("--token", type=str, default=os.getenv("HUGGINGFACE_TOKEN"), help="HuggingFace token (or set HUGGINGFACE_TOKEN env var)")
    
    args = parser.parse_args()
    
    if not args.repo_id:
        print("Error: --repo-id is required or set ADAPTER_PATH environment variable")
        sys.exit(1)
    
    # Test model loading
    model = test_model_loading(args.repo_id, args.token)
    
    if model:
        # Test basic inference
        test_basic_inference(model)
        print("\n" + "=" * 60)
        print("✓ All basic tests passed!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Model loading failed!")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()

