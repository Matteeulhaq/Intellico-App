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
    
    base_model = "google/gemma-2b-it"
    
    print(f"\n1. Loading base model: {base_model}")
    print(f"2. Loading fine-tuned adapter from: {hf_repo_id}")
    
    try:
        start_time = time.time()
        
        model = LocalModel(
            base_model_name=base_model,
            adapter_path=hf_repo_id,
            use_hf_repo=True,
            hf_token=hf_token
        )
        
        load_time = time.time() - start_time
        print(f"✓ Model loaded successfully in {load_time:.2f} seconds")
        
        # Check memory usage
        if torch.cuda.is_available():
            memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
            print(f"✓ GPU Memory - Allocated: {memory_allocated:.2f} GB, Reserved: {memory_reserved:.2f} GB")
        
        return model
        
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_basic_inference(model: LocalModel):
    """Test basic text generation"""
    print("\n" + "=" * 60)
    print("Testing Basic Inference")
    print("=" * 60)
    
    test_prompt = "<start_of_turn>user\nHello, how are you?<end_of_turn>\n<start_of_turn>model\n"
    
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
    parser.add_argument("--repo-id", type=str, required=True, help="HuggingFace repository ID")
    parser.add_argument("--token", type=str, default=None, help="HuggingFace token (for private models)")
    
    args = parser.parse_args()
    
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

