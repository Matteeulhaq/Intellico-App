from flask import Blueprint, request, jsonify, current_app
import os
import json
from datetime import datetime
from .pdf_processor import PDFProcessor
from .ml_processor import MLProcessor
from .batch_processor import BatchProcessor

# Initialize processors
pdf_processor = PDFProcessor()
ml_processor = MLProcessor()
batch_processor = BatchProcessor()

def register_routes(app):
    api = Blueprint("api", __name__, url_prefix="/api")
    
    @api.route("/upload", methods=["POST"])
    def upload():
        """Upload and process a single PDF file"""
        f = request.files.get("file")
        if not f:
            return jsonify({"error": "no file"}), 400
        
        try:
            # Save uploaded file
            filename = f.filename
            file_path = os.path.join(pdf_processor.raw_pdfs_path, filename)
            f.save(file_path)
            
            # Process the PDF
            result = pdf_processor.process_pdf(file_path)
            
            if result.get("status") == "error":
                return jsonify({"error": result.get("error", "Processing failed")}), 500
            
            return jsonify({
                "message": "File processed successfully",
                "paper_id": result["paper_id"],
                "word_count": result["word_count"],
                "sections": list(result["sections"].keys())
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/batch-process", methods=["POST"])
    def batch_process():
        """Process multiple PDFs in batch"""
        try:
            data = request.get_json() or {}
            pdf_directory = data.get("pdf_directory")
            
            if not pdf_directory:
                return jsonify({"error": "pdf_directory is required"}), 400
            
            if not os.path.exists(pdf_directory):
                return jsonify({"error": "PDF directory does not exist"}), 400
            
            # Process all papers
            summary = batch_processor.process_all_papers(pdf_directory)
            
            if "error" in summary:
                return jsonify({"error": summary["error"]}), 500
            
            return jsonify({
                "message": "Batch processing completed",
                "summary": summary
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/search", methods=["POST"])
    def semantic_search():
        """Perform semantic search across processed papers"""
        try:
            data = request.get_json() or {}
            query = data.get("query")
            top_k = data.get("top_k", 5)
            
            if not query:
                return jsonify({"error": "query is required"}), 400
            
            # Initialize ML processor if not already done
            if not ml_processor.sentence_model:
                ml_processor.initialize_models()
            
            results = ml_processor.semantic_search(query, top_k)
            
            return jsonify({
                "query": query,
                "results": results,
                "total_results": len(results)
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/papers", methods=["GET"])
    def list_papers():
        """List all processed papers"""
        try:
            processed_files = [f for f in os.listdir(pdf_processor.processed_path) 
                             if f.endswith('_processed.json')]
            
            papers = []
            for file in processed_files:
                file_path = os.path.join(pdf_processor.processed_path, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    paper_data = json.load(f)
                
                papers.append({
                    "paper_id": paper_data.get("paper_id"),
                    "filename": paper_data.get("filename"),
                    "word_count": paper_data.get("word_count", 0),
                    "page_count": paper_data.get("page_count", 0),
                    "sections": list(paper_data.get("sections", {}).keys()),
                    "processed_at": paper_data.get("processed_at")
                })
            
            return jsonify({
                "papers": papers,
                "total_count": len(papers)
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/paper/<paper_id>", methods=["GET"])
    def get_paper(paper_id):
        """Get detailed information about a specific paper"""
        try:
            file_path = os.path.join(pdf_processor.processed_path, f"{paper_id}_processed.json")
            
            if not os.path.exists(file_path):
                return jsonify({"error": "Paper not found"}), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
            
            return jsonify(paper_data), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/flowchart/<paper_id>", methods=["GET"])
    def flowchart(paper_id):
        """Generate flowchart for a paper"""
        try:
            # Get paper data
            file_path = os.path.join(pdf_processor.processed_path, f"{paper_id}_processed.json")
            
            if not os.path.exists(file_path):
                return jsonify({"error": "Paper not found"}), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
            
            # Generate flowchart based on sections
            flowchart_data = {
                "paper_id": paper_id,
                "title": paper_data.get("metadata", {}).get("title", "Untitled"),
                "sections": list(paper_data.get("sections", {}).keys()),
                "flowchart": {
                    "nodes": [
                        {"id": section, "label": section.title(), "type": "section"}
                        for section in paper_data.get("sections", {}).keys()
                    ],
                    "edges": []
                }
            }
            
            return jsonify(flowchart_data), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/qa/<paper_id>", methods=["POST"])
    def qa(paper_id):
        """Answer questions about a specific paper"""
        try:
            payload = request.get_json() or {}
            question = payload.get("question")
            
            if not question:
                return jsonify({"error": "question required"}), 400
            
            # Get paper data
            file_path = os.path.join(pdf_processor.processed_path, f"{paper_id}_processed.json")
            
            if not os.path.exists(file_path):
                return jsonify({"error": "Paper not found"}), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
            
            # Simple keyword-based answer (can be enhanced with ML models)
            answer = answer_question_simple(question, paper_data)
            
            return jsonify({
                "paper_id": paper_id,
                "question": question,
                "answer": answer
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/dataset-report", methods=["GET"])
    def dataset_report():
        """Generate comprehensive dataset report"""
        try:
            report = batch_processor.generate_dataset_report()
            return jsonify(report), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    app.register_blueprint(api)

def answer_question_simple(question: str, paper_data: dict) -> str:
    """Simple keyword-based question answering"""
    question_lower = question.lower()
    sections = paper_data.get("sections", {})
    
    # Check for common question types
    if any(word in question_lower for word in ["what", "define", "definition"]):
        # Look in introduction or abstract
        for section in ["introduction", "abstract"]:
            if section in sections and sections[section]:
                return f"Based on the {section}: {sections[section][:500]}..."
    
    elif any(word in question_lower for word in ["how", "method", "approach"]):
        # Look in methodology
        if "methodology" in sections and sections["methodology"]:
            return f"Methodology: {sections['methodology'][:500]}..."
    
    elif any(word in question_lower for word in ["result", "finding", "outcome"]):
        # Look in results
        if "results" in sections and sections["results"]:
            return f"Results: {sections['results'][:500]}..."
    
    # Default: search in full text
    full_text = paper_data.get("full_text", "")
    if full_text:
        # Simple keyword matching
        words = question_lower.split()
        relevant_parts = []
        sentences = full_text.split('.')
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in words):
                relevant_parts.append(sentence.strip())
        
        if relevant_parts:
            return f"Relevant information: {' '.join(relevant_parts[:3])}..."
    
    return "I couldn't find specific information to answer your question. Please try rephrasing or asking about specific sections of the paper."
