"""
Performance evaluation of fine-tuned model
"""
import os
import sys
import time
import torch
import statistics
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.local_model import LocalModel
from app.models.model_router import ModelRouter
from training.data_loader import TrainingDataLoader
from training.config import TrainingConfig
from app.models.prompt_templates import PromptTemplates

def truncate_text(text: str, max_length: int = 2000) -> str:
    """Truncate text to avoid token limits"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "... [truncated]"

def load_evaluation_papers(
    data_loader: TrainingDataLoader,
    num_papers: int = 10,
    tasks: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Load papers from training datasets for evaluation
    
    Args:
        data_loader: TrainingDataLoader instance
        num_papers: Number of papers to sample
        tasks: List of tasks to include (None = all tasks)
    
    Returns:
        List of paper samples with text content and task types
    """
    if tasks is None:
        tasks = ['summarization', 'classification', 'metadata_extraction', 'keyword_extraction']
    
    all_samples = []
    
    # Load samples from each dataset
    if 'summarization' in tasks:
        samples = data_loader.load_summarization_dataset()
        for sample in samples:
            all_samples.append({
                'text': truncate_text(sample['input']),
                'task': 'summarization',
                'paper_id': sample.get('paper_id', ''),
                'ground_truth': sample.get('output', '')
            })
    
    if 'classification' in tasks:
        samples = data_loader.load_classification_dataset()
        for sample in samples:
            all_samples.append({
                'text': truncate_text(sample['input']),
                'task': 'classification',
                'paper_id': sample.get('paper_id', ''),
                'ground_truth': sample.get('output', '')
            })
    
    if 'metadata_extraction' in tasks:
        samples = data_loader.load_metadata_dataset()
        for sample in samples:
            all_samples.append({
                'text': truncate_text(sample['input']),
                'task': 'metadata_extraction',
                'paper_id': sample.get('paper_id', ''),
                'ground_truth': sample.get('output', '')
            })
    
    if 'keyword_extraction' in tasks:
        samples = data_loader.load_keyword_dataset()
        for sample in samples:
            all_samples.append({
                'text': truncate_text(sample['input']),
                'task': 'keyword_extraction',
                'paper_id': sample.get('paper_id', ''),
                'ground_truth': sample.get('output', '')
            })
    
    if not all_samples:
        return []
    
    # Sample papers if we have more than requested
    if len(all_samples) > num_papers:
        all_samples = random.sample(all_samples, num_papers)
    
    return all_samples

def measure_inference_latency(
    model_router: ModelRouter,
    paper_samples: Optional[List[Dict[str, Any]]] = None,
    num_runs: int = 10
):
    """Measure inference latency using real paper samples"""
    print("\n" + "=" * 60)
    print("Measuring Inference Latency")
    print("=" * 60)
    
    # Use placeholder if no papers available
    if not paper_samples:
        print("⚠ No paper samples available, using placeholder prompt")
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
    else:
        print(f"Using {len(paper_samples)} real paper samples")
        latencies = []
        per_task_latencies = {}
        
        # Cycle through papers for num_runs
        for i in range(num_runs):
            sample = paper_samples[i % len(paper_samples)]
            task = sample['task']
            
            # Create appropriate prompt based on task
            if task == 'summarization':
                prompt = PromptTemplates.summarization(sample['text'])
                max_tokens = 200
            elif task == 'classification':
                prompt = PromptTemplates.section_classification(sample['text'])
                max_tokens = 50
            elif task == 'metadata_extraction':
                prompt = PromptTemplates.metadata_extraction(sample['text'])
                max_tokens = 256
            elif task == 'keyword_extraction':
                prompt = PromptTemplates.keyword_extraction(sample['text'])
                max_tokens = 100
            else:
                prompt = PromptTemplates.summarization(sample['text'])
                max_tokens = 100
            
            start_time = time.time()
            response = model_router.model.generate(
                prompt,
                max_new_tokens=max_tokens,
                temperature=0.7
            )
            latency = time.time() - start_time
            latencies.append(latency)
            
            # Track per-task latencies
            if task not in per_task_latencies:
                per_task_latencies[task] = []
            per_task_latencies[task].append(latency)
            
            print(f"Run {i+1} ({task}): {latency:.3f} seconds")
    
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
    
    # Calculate per-task statistics
    per_task_stats = {}
    for task, task_lats in per_task_latencies.items():
        if task_lats:
            per_task_stats[task] = {
                "average": statistics.mean(task_lats),
                "median": statistics.median(task_lats),
                "min": min(task_lats),
                "max": max(task_lats),
                "std": statistics.stdev(task_lats) if len(task_lats) > 1 else 0,
                "count": len(task_lats)
            }
            print(f"\n  {task.capitalize()}: avg={per_task_stats[task]['average']:.3f}s, count={per_task_stats[task]['count']}")
    
    return {
        "average": avg_latency,
        "median": median_latency,
        "min": min_latency,
        "max": max_latency,
        "std": std_latency,
        "all": latencies,
        "per_task": per_task_stats
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

def measure_throughput(
    model_router: ModelRouter,
    paper_samples: Optional[List[Dict[str, Any]]] = None,
    duration: int = 30
):
    """Measure throughput (requests per second) using real paper samples"""
    print("\n" + "=" * 60)
    print("Measuring Throughput")
    print("=" * 60)
    
    # Use placeholder if no papers available
    if not paper_samples:
        print("⚠ No paper samples available, using placeholder prompt")
        test_prompt = "<|im_start|>user\nExtract keywords from this text.<|im_end|>\n<|im_start|>assistant\n"
        paper_pool = [{'prompt': test_prompt, 'task': 'placeholder'}]
    else:
        print(f"Using {len(paper_samples)} real paper samples")
        # Create prompt pool
        paper_pool = []
        for sample in paper_samples:
            task = sample['task']
            if task == 'summarization':
                prompt = PromptTemplates.summarization(sample['text'])
                max_tokens = 200
            elif task == 'classification':
                prompt = PromptTemplates.section_classification(sample['text'])
                max_tokens = 50
            elif task == 'metadata_extraction':
                prompt = PromptTemplates.metadata_extraction(sample['text'])
                max_tokens = 256
            elif task == 'keyword_extraction':
                prompt = PromptTemplates.keyword_extraction(sample['text'])
                max_tokens = 100
            else:
                prompt = PromptTemplates.keyword_extraction(sample['text'])
                max_tokens = 100
            
            paper_pool.append({
                'prompt': prompt,
                'task': task,
                'max_tokens': max_tokens
            })
    
    requests_completed = 0
    task_counts = {}
    start_time = time.time()
    end_time = start_time + duration
    
    print(f"Running for {duration} seconds...")
    
    pool_index = 0
    while time.time() < end_time:
        try:
            # Rotate through paper pool
            paper_item = paper_pool[pool_index % len(paper_pool)]
            pool_index += 1
            
            model_router.model.generate(
                paper_item['prompt'],
                max_new_tokens=paper_item['max_tokens'],
                temperature=0.7
            )
            requests_completed += 1
            
            # Track task distribution
            task = paper_item['task']
            task_counts[task] = task_counts.get(task, 0) + 1
        except Exception as e:
            print(f"Error during throughput test: {e}")
            break
    
    elapsed = time.time() - start_time
    throughput = requests_completed / elapsed
    
    print(f"✓ Completed {requests_completed} requests in {elapsed:.2f} seconds")
    print(f"✓ Throughput: {throughput:.2f} requests/second")
    if task_counts:
        print(f"✓ Task distribution: {task_counts}")
    
    return {
        "requests": requests_completed,
        "duration": elapsed,
        "throughput": throughput,
        "task_distribution": task_counts
    }

def evaluate_task_performance(
    model_router: ModelRouter,
    paper_samples: List[Dict[str, Any]],
    task: str
) -> Dict[str, Any]:
    """
    Evaluate performance for a specific task
    
    Args:
        model_router: ModelRouter instance
        paper_samples: List of paper samples
        task: Task name to evaluate
    
    Returns:
        Dictionary with task-specific performance metrics
    """
    task_samples = [s for s in paper_samples if s['task'] == task]
    
    if not task_samples:
        return None
    
    print(f"\nEvaluating {task} task ({len(task_samples)} samples)...")
    
    latencies = []
    for sample in task_samples:
        # Create appropriate prompt
        if task == 'summarization':
            prompt = PromptTemplates.summarization(sample['text'])
            max_tokens = 200
        elif task == 'classification':
            prompt = PromptTemplates.section_classification(sample['text'])
            max_tokens = 50
        elif task == 'metadata_extraction':
            prompt = PromptTemplates.metadata_extraction(sample['text'])
            max_tokens = 256
        elif task == 'keyword_extraction':
            prompt = PromptTemplates.keyword_extraction(sample['text'])
            max_tokens = 100
        else:
            continue
        
        start_time = time.time()
        try:
            response = model_router.model.generate(
                prompt,
                max_new_tokens=max_tokens,
                temperature=0.7
            )
            latency = time.time() - start_time
            latencies.append(latency)
        except Exception as e:
            print(f"  Error processing sample: {e}")
            continue
    
    if not latencies:
        return None
    
    return {
        "task": task,
        "samples_tested": len(latencies),
        "average_latency": statistics.mean(latencies),
        "median_latency": statistics.median(latencies),
        "min_latency": min(latencies),
        "max_latency": max(latencies),
        "std_latency": statistics.stdev(latencies) if len(latencies) > 1 else 0
    }

def main():
    """Main evaluation function"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Evaluate model performance")
    parser.add_argument("--repo-id", type=str, default=os.getenv("ADAPTER_PATH"), help="HuggingFace repository ID (or set ADAPTER_PATH env var)")
    parser.add_argument("--token", type=str, default=os.getenv("HUGGINGFACE_TOKEN"), help="HuggingFace token (or set HUGGINGFACE_TOKEN env var)")
    parser.add_argument("--runs", type=int, default=int(os.getenv("EVAL_RUNS", "10")), help="Number of runs for latency test (or set EVAL_RUNS env var)")
    parser.add_argument("--duration", type=int, default=int(os.getenv("EVAL_DURATION", "30")), help="Duration for throughput test in seconds (or set EVAL_DURATION env var)")
    parser.add_argument("--data-dir", type=str, default=os.getenv("TRAINING_DATA_DIR"), help="Path to training data directory (or set TRAINING_DATA_DIR env var)")
    parser.add_argument("--num-papers", type=int, default=int(os.getenv("EVAL_NUM_PAPERS", "10")), help="Number of papers to use for evaluation (or set EVAL_NUM_PAPERS env var)")
    parser.add_argument("--tasks", type=str, default=os.getenv("EVAL_TASKS"), help="Comma-separated list of tasks to evaluate (or set EVAL_TASKS env var)")
    
    args = parser.parse_args()
    
    if not args.repo_id:
        print("Error: --repo-id is required or set ADAPTER_PATH environment variable")
        sys.exit(1)
    
    print("=" * 60)
    print("Model Performance Evaluation")
    print("=" * 60)
    
    # Parse tasks
    tasks = None
    if args.tasks:
        tasks = [t.strip() for t in args.tasks.split(',')]
        valid_tasks = ['summarization', 'classification', 'metadata_extraction', 'keyword_extraction']
        tasks = [t for t in tasks if t in valid_tasks]
        if not tasks:
            print("⚠ No valid tasks specified, using all tasks")
            tasks = None
    
    # Load papers from training datasets
    config = TrainingConfig()
    data_dir = args.data_dir if args.data_dir else config.training_data_dir
    
    print(f"\nLoading papers from: {data_dir}")
    data_loader = TrainingDataLoader(
        training_data_dir=data_dir,
        processed_papers_dir=config.processed_papers_dir
    )
    
    paper_samples = load_evaluation_papers(
        data_loader,
        num_papers=args.num_papers,
        tasks=tasks
    )
    
    if paper_samples:
        print(f"✓ Loaded {len(paper_samples)} paper samples")
        # Show task distribution
        task_dist = {}
        for sample in paper_samples:
            task = sample['task']
            task_dist[task] = task_dist.get(task, 0) + 1
        print(f"  Task distribution: {task_dist}")
    else:
        print("⚠ No paper samples loaded, will use placeholder prompts")
    
    # Load model
    print("\nLoading model...")
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
    print("✓ Model loaded")
    
    # Run evaluations
    latency_results = measure_inference_latency(model_router, paper_samples, args.runs)
    memory_results = measure_memory_usage()
    throughput_results = measure_throughput(model_router, paper_samples, args.duration)
    
    # Task-specific evaluation
    task_results = {}
    unique_tasks = set()
    if paper_samples:
        unique_tasks = set(s['task'] for s in paper_samples)
        for task in unique_tasks:
            task_perf = evaluate_task_performance(model_router, paper_samples, task)
            if task_perf:
                task_results[task] = task_perf
    
    # Summary
    print("\n" + "=" * 60)
    print("Performance Summary")
    print("=" * 60)
    print(f"Average Latency: {latency_results['average']:.3f}s")
    if memory_results:
        print(f"Memory Usage: {memory_results['allocated']:.2f} GB")
    print(f"Throughput: {throughput_results['throughput']:.2f} req/s")
    
    if task_results:
        print("\nPer-Task Performance:")
        for task, perf in task_results.items():
            print(f"  {task}: avg={perf['average_latency']:.3f}s (n={perf['samples_tested']})")
    
    # Save results
    results = {
        "latency": latency_results,
        "memory": memory_results,
        "throughput": throughput_results,
        "task_specific": task_results,
        "evaluation_config": {
            "num_papers": len(paper_samples) if paper_samples else 0,
            "tasks_evaluated": list(unique_tasks) if paper_samples else [],
            "paper_ids": list(set(s['paper_id'] for s in paper_samples if s.get('paper_id'))) if paper_samples else []
        }
    }
    
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✓ Results saved to evaluation_results.json")

if __name__ == "__main__":
    main()

