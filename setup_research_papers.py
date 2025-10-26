#!/usr/bin/env python3
"""
Setup Script for Research Papers Processing
This script helps you set up and process your 42 research papers for model training
"""

import os
import sys
import argparse
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    parser = argparse.ArgumentParser(description="Setup research papers for model training")
    parser.add_argument("--pdf-dir", required=True, help="Directory containing your 42 PDF files")
    parser.add_argument("--storage-path", default="./research_papers", help="Storage path for processed files")
    parser.add_argument("--skip-processing", action="store_true", help="Skip PDF processing, only setup structure")
    parser.add_argument("--train-models", action="store_true", help="Train models after processing")
    
    args = parser.parse_args()
    
    print("🔬 Research Papers Setup for Model Training")
    print("=" * 50)
    
    # Check if PDF directory exists
    if not os.path.exists(args.pdf_dir):
        print(f"❌ Error: PDF directory '{args.pdf_dir}' does not exist")
        sys.exit(1)
    
    # Count PDF files
    pdf_files = [f for f in os.listdir(args.pdf_dir) if f.lower().endswith('.pdf')]
    print(f"📄 Found {len(pdf_files)} PDF files in {args.pdf_dir}")
    
    if len(pdf_files) == 0:
        print("❌ No PDF files found in the directory")
        sys.exit(1)
    
    # Create storage directories
    print("\n📁 Creating storage directories...")
    storage_path = args.storage_path
    research_papers_path = os.path.join(storage_path, "research_papers")
    directories = [
        research_papers_path,
        os.path.join(research_papers_path, "raw_pdfs"),
        os.path.join(research_papers_path, "processed"),
        os.path.join(research_papers_path, "embeddings"),
        os.path.join(research_papers_path, "trained_models")
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✓ Created: {directory}")
    
    if args.skip_processing:
        print("\n⏭️  Skipping PDF processing (--skip-processing flag)")
        return
    
    # Process PDFs
    print(f"\n🔄 Processing {len(pdf_files)} PDF files...")
    
    try:
        from backend.app.batch_processor import BatchProcessor
        
        processor = BatchProcessor(storage_path)
        summary = processor.process_all_papers(args.pdf_dir)
        
        if "error" in summary:
            print(f"❌ Error during processing: {summary['error']}")
            sys.exit(1)
        
        print("✅ PDF processing completed successfully!")
        print(f"   • Processed: {summary['successful_papers']} papers")
        print(f"   • Failed: {summary['failed_papers']} papers")
        print(f"   • Processing time: {summary['processing_time_seconds']:.2f} seconds")
        print(f"   • Total chunks: {summary['total_chunks']}")
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        sys.exit(1)
    
    # Train models if requested
    if args.train_models:
        print("\n🤖 Training models...")
        
        try:
            from backend.app.training_scripts import ResearchPaperTrainer
            
            trainer = ResearchPaperTrainer(storage_path)
            training_results = trainer.train_all_models()
            
            print("✅ Model training completed!")
            
            for model_type, result in training_results["models"].items():
                if "error" in result:
                    print(f"   • {model_type}: ❌ {result['error']}")
                else:
                    print(f"   • {model_type}: ✅ Completed")
            
        except Exception as e:
            print(f"❌ Error during model training: {str(e)}")
    
    # Generate final report
    print("\n📊 Generating final report...")
    
    try:
        from backend.app.batch_processor import BatchProcessor
        
        processor = BatchProcessor(storage_path)
        report = processor.generate_dataset_report()
        
        print("✅ Dataset report generated!")
        print(f"   • Total papers: {report['dataset_info']['total_papers']}")
        print(f"   • Total words: {report['statistics']['total_words']:,}")
        print(f"   • Average words per paper: {report['statistics']['average_words_per_paper']:.0f}")
        
        # Save setup summary
        setup_summary = {
            "setup_completed": datetime.now().isoformat(),
            "pdf_directory": args.pdf_dir,
            "storage_path": storage_path,
            "total_pdfs": len(pdf_files),
            "processing_summary": summary if not args.skip_processing else None,
            "training_results": training_results if args.train_models else None,
            "dataset_report": report
        }
        
        summary_path = os.path.join(research_papers_path, "setup_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(setup_summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Setup summary saved to: {summary_path}")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not generate final report: {str(e)}")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start your application: docker compose up -d --build")
    print("2. Access the API endpoints:")
    print("   • GET /api/papers - List all processed papers")
    print("   • POST /api/search - Semantic search")
    print("   • POST /api/qa/<paper_id> - Ask questions about papers")
    print("   • GET /api/dataset-report - View dataset statistics")

if __name__ == "__main__":
    main()
