#!/usr/bin/env python3
"""
Test Script for Research Papers Setup
This script tests the setup and processing pipeline
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def create_test_pdf():
    """Create a simple test PDF for testing purposes"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a temporary PDF file
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "test_paper.pdf")
        
        c = canvas.Canvas(pdf_path, pagesize=letter)
        
        # Add content
        c.drawString(100, 750, "Test Research Paper")
        c.drawString(100, 730, "Abstract: This is a test abstract for machine learning applications.")
        c.drawString(100, 710, "Introduction: This paper discusses various machine learning techniques.")
        c.drawString(100, 690, "Methodology: We used deep learning approaches for our experiments.")
        c.drawString(100, 670, "Results: Our results show significant improvements in accuracy.")
        c.drawString(100, 650, "Conclusion: Machine learning shows great promise in this domain.")
        
        c.save()
        return pdf_path, temp_dir
        
    except ImportError:
        print("⚠️  reportlab not installed. Creating a dummy text file instead.")
        temp_dir = tempfile.mkdtemp()
        txt_path = os.path.join(temp_dir, "test_paper.txt")
        
        with open(txt_path, 'w') as f:
            f.write("""
Test Research Paper

Abstract: This is a test abstract for machine learning applications in healthcare.

Introduction: This paper discusses various machine learning techniques and their applications in medical research.

Methodology: We used deep learning approaches including convolutional neural networks and recurrent neural networks for our experiments.

Results: Our results show significant improvements in accuracy compared to traditional methods.

Discussion: The findings suggest that machine learning approaches are highly effective for medical diagnosis.

Conclusion: Machine learning shows great promise in healthcare applications and should be further investigated.
""")
        
        return txt_path, temp_dir

def test_pdf_processing():
    """Test PDF processing functionality"""
    print("🧪 Testing PDF Processing...")
    
    try:
        from backend.app.pdf_processor import PDFProcessor
        
        # Create test PDF
        pdf_path, temp_dir = create_test_pdf()
        
        # Initialize processor
        processor = PDFProcessor()
        
        # Process the test PDF
        result = processor.process_pdf(pdf_path, "test_paper")
        
        if result.get("status") == "error":
            print(f"❌ PDF processing failed: {result.get('error')}")
            return False
        
        print("✅ PDF processing test passed!")
        print(f"   • Paper ID: {result['paper_id']}")
        print(f"   • Word count: {result['word_count']}")
        print(f"   • Sections found: {list(result['sections'].keys())}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        return True
        
    except Exception as e:
        print(f"❌ PDF processing test failed: {str(e)}")
        return False

def test_ml_processing():
    """Test ML processing functionality"""
    print("\n🧪 Testing ML Processing...")
    
    try:
        from backend.app.ml_processor import MLProcessor
        
        # Initialize ML processor
        ml_processor = MLProcessor()
        
        # Test model initialization (this might take time on first run)
        print("   • Initializing models...")
        ml_processor.initialize_models()
        
        # Test embedding generation
        test_texts = [
            "This is a test sentence about machine learning.",
            "Another test sentence about artificial intelligence."
        ]
        
        print("   • Testing embedding generation...")
        embeddings = ml_processor.generate_embeddings(test_texts)
        
        print(f"✅ ML processing test passed!")
        print(f"   • Generated embeddings shape: {embeddings.shape}")
        print(f"   • Models initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ ML processing test failed: {str(e)}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🧪 Testing API Endpoints...")
    
    try:
        from backend.app.services import register_routes
        from flask import Flask
        
        # Create test Flask app
        app = Flask(__name__)
        register_routes(app)
        
        # Test with test client
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("   • Health endpoint: ✅")
            else:
                print("   • Health endpoint: ❌")
                return False
            
            # Test papers endpoint
            response = client.get('/api/papers')
            if response.status_code == 200:
                print("   • Papers endpoint: ✅")
            else:
                print("   • Papers endpoint: ❌")
                return False
        
        print("✅ API endpoints test passed!")
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {str(e)}")
        return False

def main():
    print("🔬 Research Papers Setup Test")
    print("=" * 40)
    
    # Check if backend modules exist
    backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'app')
    required_modules = [
        'pdf_processor.py',
        'ml_processor.py', 
        'batch_processor.py',
        'training_scripts.py',
        'services.py'
    ]
    
    print("📁 Checking required modules...")
    for module in required_modules:
        module_path = os.path.join(backend_path, module)
        if os.path.exists(module_path):
            print(f"   ✓ {module}")
        else:
            print(f"   ❌ {module} - Missing!")
            return False
    
    # Run tests
    tests = [
        test_pdf_processing,
        test_ml_processing,
        test_api_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Place your 42 PDF files in a directory")
        print("2. Run: python setup_research_papers.py --pdf-dir /path/to/your/pdfs")
        print("3. Start the application: docker compose up -d --build")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("Make sure all dependencies are installed:")
        print("pip install -r backend/requirements.txt")

if __name__ == "__main__":
    main()
