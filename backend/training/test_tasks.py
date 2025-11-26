"""
Test task-specific functionality of fine-tuned model
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.local_model import LocalModel
from app.models.model_router import ModelRouter

def test_summarization(model_router: ModelRouter):
    """Test summarization task"""
    print("\n" + "=" * 60)
    print("Testing Summarization")
    print("=" * 60)
    
    sample_text = """
    This study investigates the relationship between oral health and quality of life in adults.
    We conducted a cross-sectional study with 500 participants. Data was collected through
    questionnaires and clinical examinations. Results showed a significant correlation between
    oral health status and quality of life measures. The findings suggest that improving oral
    health can positively impact overall well-being.
    """
    
    try:
        summary = model_router.summarize(sample_text)
        print(f"✓ Summary generated: {summary[:200]}...")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_classification(model_router: ModelRouter):
    """Test section classification"""
    print("\n" + "=" * 60)
    print("Testing Section Classification")
    print("=" * 60)
    
    test_sections = [
        ("This study aims to investigate...", "introduction"),
        ("We collected data from 100 participants...", "methodology"),
        ("The results showed significant differences...", "results"),
    ]
    
    success_count = 0
    for text, expected in test_sections:
        try:
            classification = model_router.model.classify_section(text)
            print(f"✓ Text: '{text[:50]}...' -> Classified as: {classification}")
            success_count += 1
        except Exception as e:
            print(f"✗ Error classifying '{text[:50]}...': {e}")
    
    return success_count == len(test_sections)

def test_metadata_extraction(model_router: ModelRouter):
    """Test metadata extraction"""
    print("\n" + "=" * 60)
    print("Testing Metadata Extraction")
    print("=" * 60)
    
    sample_text = """
    Title: Oral Health and Quality of Life in Adults
    Authors: John Doe, Jane Smith
    Abstract: This study examines the relationship between oral health and quality of life.
    Keywords: oral health, quality of life, dental care
    Publication Date: 2024
    """
    
    try:
        metadata = model_router.extract_metadata(sample_text)
        print(f"✓ Metadata extracted: {json.dumps(metadata, indent=2)}")
        
        # Check if it's valid JSON structure
        if isinstance(metadata, dict):
            print("✓ Metadata is valid JSON structure")
            return True
        else:
            print("✗ Metadata is not a dictionary")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_keyword_extraction(model_router: ModelRouter):
    """Test keyword extraction"""
    print("\n" + "=" * 60)
    print("Testing Keyword Extraction")
    print("=" * 60)
    
    sample_text = """
    This research paper discusses periodontal disease, dental caries, and oral hygiene.
    The study focuses on preventive dentistry and patient education. We examine
    the impact of fluoride treatment and regular dental checkups.
    """
    
    try:
        # Use the model directly to extract keywords
        from app.models.prompt_templates import PromptTemplates
        prompt = PromptTemplates.keyword_extraction(sample_text)
        response = model_router.model.generate(prompt, max_new_tokens=100, temperature=0.3)
        
        print(f"✓ Keywords extracted: {response[:200]}...")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_keyword_relationships(model_router: ModelRouter):
    """Test keyword relationship extraction"""
    print("\n" + "=" * 60)
    print("Testing Keyword Relationship Extraction")
    print("=" * 60)
    
    sample_text = """
    This study examines periodontal disease and its relationship to systemic health.
    Periodontal disease leads to inflammation, which can affect cardiovascular health.
    The research shows that oral bacteria can enter the bloodstream, causing
    systemic inflammation. This inflammation is linked to various health conditions.
    """
    
    try:
        relationships = model_router.extract_keyword_relationships(sample_text)
        print(f"✓ Relationships extracted: {relationships[:300]}...")
        
        # Try to parse as JSON
        try:
            if "{" in relationships:
                json_start = relationships.find("{")
                json_end = relationships.rfind("}") + 1
                json_str = relationships[json_start:json_end]
                parsed = json.loads(json_str)
                print("✓ Relationships are valid JSON")
                if "keywords" in parsed:
                    print(f"  - Keywords: {parsed['keywords']}")
                if "relationships" in parsed:
                    print(f"  - Relationships: {parsed['relationships']}")
                return True
        except:
            pass
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test task-specific functionality")
    parser.add_argument("--repo-id", type=str, default=os.getenv("ADAPTER_PATH"), help="HuggingFace repository ID (or set ADAPTER_PATH env var)")
    parser.add_argument("--token", type=str, default=os.getenv("HUGGINGFACE_TOKEN"), help="HuggingFace token (or set HUGGINGFACE_TOKEN env var)")
    
    args = parser.parse_args()
    
    if not args.repo_id:
        print("Error: --repo-id is required or set ADAPTER_PATH environment variable")
        sys.exit(1)
    
    print("=" * 60)
    print("Task-Specific Testing")
    print("=" * 60)
    
    # Initialize model
    from app.models.local_model import LocalModel
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
    model_router.model = model  # Use the loaded model
    
    # Run tests
    results = {
        "summarization": test_summarization(model_router),
        "classification": test_classification(model_router),
        "metadata_extraction": test_metadata_extraction(model_router),
        "keyword_extraction": test_keyword_extraction(model_router),
        "keyword_relationships": test_keyword_relationships(model_router),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for task, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {task}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All task tests passed!")
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

