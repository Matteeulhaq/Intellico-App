"""
Integration tests for Flask API with fine-tuned model
"""
import os
import sys
import json
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_api_health(base_url: str = "http://localhost:2750"):
    """Test API health endpoint"""
    print("\n" + "=" * 60)
    print("Testing API Health")
    print("=" * 60)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ API is healthy")
            return True
        else:
            print(f"✗ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error connecting to API: {e}")
        return False

def test_upload_endpoint(base_url: str = "http://localhost:2750", pdf_path: str = None):
    """Test paper upload endpoint"""
    print("\n" + "=" * 60)
    print("Testing Upload Endpoint")
    print("=" * 60)
    
    if not pdf_path or not os.path.exists(pdf_path):
        print("✗ PDF file not found, skipping upload test")
        return False
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{base_url}/api/upload", files=files, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Upload successful")
            print(f"  Paper ID: {data.get('paper_id')}")
            paper_id = data.get('paper_id')
            return paper_id
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_qa_endpoint(base_url: str, paper_id: str):
    """Test question answering endpoint"""
    print("\n" + "=" * 60)
    print("Testing QA Endpoint")
    print("=" * 60)
    
    question = "What is the main topic of this paper?"
    
    try:
        response = requests.post(
            f"{base_url}/api/qa/{paper_id}",
            json={"question": question},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ QA successful")
            print(f"  Question: {question}")
            print(f"  Answer: {data.get('answer', '')[:200]}...")
            return True
        else:
            print(f"✗ QA failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_flowchart_endpoint(base_url: str, paper_id: str):
    """Test flowchart generation endpoint"""
    print("\n" + "=" * 60)
    print("Testing Flowchart Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{base_url}/api/flowchart/{paper_id}",
            timeout=60
        )
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'svg' in content_type or 'image' in content_type:
                print(f"✓ Flowchart generated successfully")
                print(f"  Content-Type: {content_type}")
                print(f"  Size: {len(response.content)} bytes")
                return True
            else:
                print(f"✗ Unexpected content type: {content_type}")
                return False
        else:
            print(f"✗ Flowchart generation failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_summarize_endpoint(base_url: str, paper_id: str):
    """Test summarization endpoint"""
    print("\n" + "=" * 60)
    print("Testing Summarize Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{base_url}/api/summarize/{paper_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Summarization successful")
            print(f"  Summary: {data.get('summary', '')[:200]}...")
            return True
        else:
            print(f"✗ Summarization failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test API integration")
    parser.add_argument("--base-url", type=str, default="http://localhost:2750", help="Base URL of API")
    parser.add_argument("--pdf", type=str, default=None, help="Path to test PDF file")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("API Integration Testing")
    print("=" * 60)
    
    # Test health
    if not test_api_health(args.base_url):
        print("\n✗ API is not available. Make sure the Flask server is running.")
        sys.exit(1)
    
    # Test upload if PDF provided
    paper_id = None
    if args.pdf:
        paper_id = test_upload_endpoint(args.base_url, args.pdf)
    
    if paper_id:
        # Test other endpoints
        test_qa_endpoint(args.base_url, paper_id)
        test_flowchart_endpoint(args.base_url, paper_id)
        test_summarize_endpoint(args.base_url, paper_id)
    
    print("\n" + "=" * 60)
    print("API Integration Tests Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()

