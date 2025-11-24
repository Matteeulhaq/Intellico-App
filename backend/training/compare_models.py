"""
Compare fine-tuned model with base model
"""
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.local_model import LocalModel
from app.models.model_router import ModelRouter

def compare_responses(base_model: ModelRouter, fine_tuned_model: ModelRouter, prompt: str):
    """Compare responses from base and fine-tuned models"""
    print(f"\nPrompt: {prompt[:100]}...")
    print("-" * 60)
    
    # Base model response
    start = time.time()
    base_response = base_model.model.generate(prompt, max_new_tokens=200, temperature=0.7)
    base_time = time.time() - start
    
    # Fine-tuned model response
    start = time.time()
    ft_response = fine_tuned_model.model.generate(prompt, max_new_tokens=200, temperature=0.7)
    ft_time = time.time() - start
    
    print(f"Base Model ({base_time:.2f}s):")
    print(f"  {base_response[:200]}...")
    print(f"\nFine-Tuned Model ({ft_time:.2f}s):")
    print(f"  {ft_response[:200]}...")
    
    return {
        "base": {"response": base_response, "time": base_time},
        "fine_tuned": {"response": ft_response, "time": ft_time}
    }

def main():
    """Main comparison function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare base and fine-tuned models")
    parser.add_argument("--repo-id", type=str, required=True, help="HuggingFace repository ID")
    parser.add_argument("--token", type=str, default=None, help="HuggingFace token")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Model Comparison: Base vs Fine-Tuned")
    print("=" * 60)
    
    # Load base model
    print("\n1. Loading base model...")
    base_model = LocalModel(
        base_model_name="Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path=None
    )
    base_router = ModelRouter("Qwen/Qwen2.5-1.5B-Instruct", None)
    base_router.model = base_model
    
    # Load fine-tuned model
    print("\n2. Loading fine-tuned model...")
    ft_model = LocalModel(
        base_model_name="Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path=args.repo_id,
        use_hf_repo=True,
        hf_token=args.token
    )
    ft_router = ModelRouter("Qwen/Qwen2.5-1.5B-Instruct", args.repo_id)
    ft_router.model = ft_model
    
    # Test prompts
    test_prompts = [
        "<|im_start|>user\nSummarize this research paper about dental health.<|im_end|>\n<|im_start|>assistant\n",
        "<|im_start|>user\nExtract metadata from this paper: Title, Authors, Keywords.<|im_end|>\n<|im_start|>assistant\n",
        "<|im_start|>user\nClassify this section: We conducted a study with 100 participants...<|im_end|>\n<|im_start|>assistant\n",
    ]
    
    print("\n" + "=" * 60)
    print("Comparing Responses")
    print("=" * 60)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nTest {i}:")
        compare_responses(base_router, ft_router, prompt)
    
    print("\n" + "=" * 60)
    print("Comparison Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()

