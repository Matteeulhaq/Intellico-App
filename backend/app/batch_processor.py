"""
Batch Processing Script for Research Papers
Handles bulk processing of 42 research papers for model training
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict
import argparse

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_processor import PDFProcessor
from ml_processor import MLProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self, storage_path: str = "/app/storage"):
        self.storage_path = storage_path
        self.pdf_processor = PDFProcessor(storage_path)
        self.ml_processor = MLProcessor(storage_path)
        
        # Paths
        self.research_papers_path = os.path.join(storage_path, "research_papers")
        self.raw_pdfs_path = os.path.join(self.research_papers_path, "raw_pdfs")
        self.processed_path = os.path.join(self.research_papers_path, "processed")
        self.embeddings_path = os.path.join(self.research_papers_path, "embeddings")
        
        # Create directories
        os.makedirs(self.raw_pdfs_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)
        os.makedirs(self.embeddings_path, exist_ok=True)
    
    def copy_pdfs_to_storage(self, source_directory: str) -> List[str]:
        """
        Copy PDFs from source directory to storage
        """
        import shutil
        
        copied_files = []
        pdf_files = [f for f in os.listdir(source_directory) if f.lower().endswith('.pdf')]
        
        logger.info(f"Found {len(pdf_files)} PDF files in {source_directory}")
        
        for pdf_file in pdf_files:
            source_path = os.path.join(source_directory, pdf_file)
            dest_path = os.path.join(self.raw_pdfs_path, pdf_file)
            
            try:
                shutil.copy2(source_path, dest_path)
                copied_files.append(dest_path)
                logger.info(f"Copied: {pdf_file}")
            except Exception as e:
                logger.error(f"Error copying {pdf_file}: {str(e)}")
        
        logger.info(f"Successfully copied {len(copied_files)} PDF files")
        return copied_files
    
    def process_all_papers(self, pdf_directory: str = None) -> Dict[str, any]:
        """
        Complete pipeline for processing all research papers
        """
        start_time = datetime.now()
        logger.info("Starting batch processing of research papers")
        
        # Step 1: Copy PDFs if source directory provided
        if pdf_directory and os.path.exists(pdf_directory):
            self.copy_pdfs_to_storage(pdf_directory)
        
        # Step 2: Process PDFs
        logger.info("Step 1: Processing PDFs...")
        pdf_files = [f for f in os.listdir(self.raw_pdfs_path) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            logger.error("No PDF files found in raw_pdfs directory")
            return {"error": "No PDF files found"}
        
        processed_papers = self.pdf_processor.batch_process_pdfs(self.raw_pdfs_path)
        
        # Step 3: Initialize ML models
        logger.info("Step 2: Initializing ML models...")
        try:
            self.ml_processor.initialize_models()
        except Exception as e:
            logger.error(f"Error initializing ML models: {str(e)}")
            return {"error": f"ML model initialization failed: {str(e)}"}
        
        # Step 4: Generate embeddings
        logger.info("Step 3: Generating embeddings...")
        try:
            embeddings_data = self.ml_processor.process_paper_embeddings(processed_papers)
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return {"error": f"Embedding generation failed: {str(e)}"}
        
        # Step 5: Train models
        logger.info("Step 4: Training models...")
        training_results = {}
        
        try:
            # Train classification model
            classification_result = self.ml_processor.train_custom_model(
                processed_papers, "classification"
            )
            training_results["classification"] = classification_result
            
        except Exception as e:
            logger.error(f"Error training classification model: {str(e)}")
            training_results["classification"] = {"error": str(e)}
        
        # Step 6: Generate summary report
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        summary = {
            "processing_started": start_time.isoformat(),
            "processing_completed": end_time.isoformat(),
            "processing_time_seconds": processing_time,
            "total_pdfs": len(pdf_files),
            "successful_papers": len([p for p in processed_papers if p.get("status") != "error"]),
            "failed_papers": len([p for p in processed_papers if p.get("status") == "error"]),
            "total_chunks": len(embeddings_data.get("embeddings", [])),
            "training_results": training_results,
            "storage_paths": {
                "raw_pdfs": self.raw_pdfs_path,
                "processed": self.processed_path,
                "embeddings": self.embeddings_path
            }
        }
        
        # Save summary
        summary_path = os.path.join(self.research_papers_path, "processing_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Batch processing completed in {processing_time:.2f} seconds")
        logger.info(f"Summary saved to: {summary_path}")
        
        return summary
    
    def test_semantic_search(self, query: str = "machine learning applications") -> List[Dict]:
        """
        Test semantic search functionality
        """
        logger.info(f"Testing semantic search with query: '{query}'")
        
        try:
            results = self.ml_processor.semantic_search(query, top_k=5)
            logger.info(f"Found {len(results)} results")
            
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}: {result['paper_id']} - {result['section']} (score: {result['similarity_score']:.3f})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []
    
    def generate_dataset_report(self) -> Dict[str, any]:
        """
        Generate a comprehensive report about the processed dataset
        """
        processed_files = [f for f in os.listdir(self.processed_path) if f.endswith('_processed.json')]
        
        report = {
            "dataset_info": {
                "total_papers": len(processed_files),
                "processed_at": datetime.now().isoformat()
            },
            "papers": [],
            "statistics": {
                "total_words": 0,
                "total_chars": 0,
                "sections_found": {},
                "average_words_per_paper": 0
            }
        }
        
        for file in processed_files:
            file_path = os.path.join(self.processed_path, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    paper_data = json.load(f)
                
                report["papers"].append({
                    "paper_id": paper_data.get("paper_id"),
                    "filename": paper_data.get("filename"),
                    "word_count": paper_data.get("word_count", 0),
                    "char_count": paper_data.get("char_count", 0),
                    "page_count": paper_data.get("page_count", 0),
                    "sections": list(paper_data.get("sections", {}).keys())
                })
                
                # Update statistics
                report["statistics"]["total_words"] += paper_data.get("word_count", 0)
                report["statistics"]["total_chars"] += paper_data.get("char_count", 0)
                
                # Count sections
                for section in paper_data.get("sections", {}).keys():
                    report["statistics"]["sections_found"][section] = report["statistics"]["sections_found"].get(section, 0) + 1
                
            except Exception as e:
                logger.error(f"Error reading {file}: {str(e)}")
        
        # Calculate averages
        if report["papers"]:
            report["statistics"]["average_words_per_paper"] = report["statistics"]["total_words"] / len(report["papers"])
        
        # Save report
        report_path = os.path.join(self.research_papers_path, "dataset_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Dataset report saved to: {report_path}")
        return report

def main():
    parser = argparse.ArgumentParser(description="Batch process research papers for model training")
    parser.add_argument("--pdf-dir", help="Directory containing PDF files to process")
    parser.add_argument("--storage-path", default="/app/storage", help="Storage path for processed files")
    parser.add_argument("--test-search", help="Test semantic search with given query")
    parser.add_argument("--generate-report", action="store_true", help="Generate dataset report")
    
    args = parser.parse_args()
    
    # Initialize batch processor
    processor = BatchProcessor(args.storage_path)
    
    if args.test_search:
        # Test semantic search
        results = processor.test_semantic_search(args.test_search)
        print(f"Search results: {json.dumps(results, indent=2)}")
    
    elif args.generate_report:
        # Generate dataset report
        report = processor.generate_dataset_report()
        print(f"Dataset report: {json.dumps(report, indent=2)}")
    
    else:
        # Process all papers
        if not args.pdf_dir:
            print("Error: --pdf-dir is required for processing")
            sys.exit(1)
        
        if not os.path.exists(args.pdf_dir):
            print(f"Error: PDF directory {args.pdf_dir} does not exist")
            sys.exit(1)
        
        summary = processor.process_all_papers(args.pdf_dir)
        print(f"Processing summary: {json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    main()
