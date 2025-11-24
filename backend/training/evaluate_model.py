"""
Performance evaluation of fine-tuned model
"""
import os
import sys
import time
import torch
import statistics
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.local_model import LocalModel
from app.models.model_router import ModelRouter

def measure_inference_latency(model_router: ModelRouter, num_runs: int = 10):
    """Measure inference latency"""
    print("\n" + "=" * 60)
    print("Measuring Inference Latency")
    print("=" * 60)
    
    test_prompt = "<|im_start|>user\nSummarize this research paper about oral health.<|im_end|>\n<|im_start|>assistant\n"
    
    latencies = []
    
    for i in range(num_runs):
        start_time = time.time()
        response = model_router.model.generate(
            test_prompt,
            max_new_tokens=100,
            temperature=0.7
        )
        latency = time.time() - start_time
        latencies.append(latency)
        print(f"Run {i+1}: {latency:.3f} seconds")
    
    avg_latency = statistics.mean(latencies)
    median_latency = statistics.median(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
    
    print(f"\n✓ Average latency: {avg_latency:.3f} seconds")
    print(f"✓ Median latency: {median_latency:.3f} seconds")
    print(f"✓ Min latency: {min_latency:.3f} seconds")
    print(f"✓ Max latency: {max_latency:.3f} seconds")
    print(f"✓ Std deviation: {std_latency:.3f} seconds")
    
    return {
        "average": avg_latency,
        "median": median_latency,
        "min": min_latency,
        "max": max_latency,
        "std": std_latency,
        "all": latencies
    }

def measure_memory_usage():
    """Measure memory usage"""
    print("\n" + "=" * 60)
    print("Measuring Memory Usage")
    print("=" * 60)
    
    if not torch.cuda.is_available():
        print("✗ CUDA not available, cannot measure GPU memory")
        return None
    
    memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
    memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
    memory_max_allocated = torch.cuda.max_memory_allocated() / 1024**3  # GB
    
    print(f"✓ Current allocated: {memory_allocated:.2f} GB")
    print(f"✓ Current reserved: {memory_reserved:.2f} GB")
    print(f"✓ Peak allocated: {memory_max_allocated:.2f} GB")
    
    return {
        "allocated": memory_allocated,
        "reserved": memory_reserved,
        "peak": memory_max_allocated
    }

def measure_throughput(model_router: ModelRouter, duration: int = 30):
    """Measure throughput (requests per second)"""
    print("\n" + "=" * 60)
    print("Measuring Throughput")
    print("=" * 60)
    
    test_prompt = "<|im_start|>user\nExtract keywords from this text.<|im_end|>\n<|im_start|>assistant\n"
    
    requests_completed = 0
    start_time = time.time()
    end_time = start_time + duration
    
    print(f"Running for {duration} seconds...")
    
    while time.time() < end_time:
        try:
            model_router.model.generate(test_prompt, max_new_tokens=50, temperature=0.7)
            requests_completed += 1
        except Exception as e:
            print(f"Error during throughput test: {e}")
            break
    
    elapsed = time.time() - start_time
    throughput = requests_completed / elapsed
    
    print(f"✓ Completed {requests_completed} requests in {elapsed:.2f} seconds")
    print(f"✓ Throughput: {throughput:.2f} requests/second")
    
    return {
        "requests": requests_completed,
        "duration": elapsed,
        "throughput": throughput
    }

def main():
    """Main evaluation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate model performance")
    parser.add_argument("--repo-id", type=str, required=True, help="HuggingFace repository ID")
    parser.add_argument("--token", type=str, default=None, help="HuggingFace token")
    parser.add_argument("--runs", type=int, default=10, help="Number of runs for latency test")
    parser.add_argument("--duration", type=int, default=30, help="Duration for throughput test (seconds)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Model Performance Evaluation")
    print("=" * 60)
    
    # Load model
    model = LocalModel(
        base_model_name="Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path=args.repo_id,
        use_hf_repo=True,
        hf_token=args.token
    )
    
    model_router = ModelRouter(
        base_model_name="Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path=args.repo_id
    )
    model_router.model = model
    
    # Run evaluations
    latency_results = measure_inference_latency(model_router, args.runs)
    memory_results = measure_memory_usage()
    throughput_results = measure_throughput(model_router, args.duration)
    
    # Summary
    print("\n" + "=" * 60)
    print("Performance Summary")
    print("=" * 60)
    print(f"Average Latency: {latency_results['average']:.3f}s")
    if memory_results:
        print(f"Memory Usage: {memory_results['allocated']:.2f} GB")
    print(f"Throughput: {throughput_results['throughput']:.2f} req/s")
    
    # Save results
    results = {
        "latency": latency_results,
        "memory": memory_results,
        "throughput": throughput_results
    }
    
    import json
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✓ Results saved to evaluation_results.json")

if __name__ == "__main__":
    main()

