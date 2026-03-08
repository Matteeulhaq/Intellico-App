from flask import Blueprint, request, jsonify, current_app, send_file
import os
import uuid
from io import BytesIO
from .config import Config
from .pdf_processor import PDFProcessor
from .paper_analyzer import PaperAnalyzer
from .guardrails.domain_guardrail import DentistryGuardrail
from typing import Optional, Dict

# Initialize components
config = Config()
pdf_processor = PDFProcessor(storage_path=config.STORAGE_PATH)
paper_analyzer = PaperAnalyzer(
    mongo_uri=config.MONGO_URI,
    base_model_name=config.BASE_MODEL_NAME,
    adapter_path=config.ADAPTER_PATH
)

# Initialize guardrail
domain_guardrail = DentistryGuardrail(strict_mode=config.GUARDRAIL_STRICT_MODE)

def register_routes(app):
    api = Blueprint("api", __name__, url_prefix="/api")
    
    @api.route("/upload", methods=["POST"])
    def upload():
        """Upload and process PDF file"""
        try:
            f = request.files.get("file")
            if not f:
                return jsonify({"error": "no file"}), 400

            # Generate paper ID
            paper_id = str(uuid.uuid4())

            # Process PDF
            paper_data = pdf_processor.process_pdf(f, paper_id)

            # LAYER 1: Validate paper content is dentistry-related
            is_allowed, rejection_reason = domain_guardrail.check_input(
                paper_data['full_text'][:1000]  # Check first 1000 chars
            )
            if not is_allowed:
                return jsonify({
                    "error": "Uploaded paper does not appear to be related to dentistry or oral health",
                    "blocked": True
                }), 400

            # Index paper for RAG
            paper_analyzer.index_paper(paper_data)

            # Extract metadata using model
            metadata = paper_analyzer.extract_metadata(paper_data['full_text'])
            paper_data['extracted_metadata'] = metadata

            return jsonify({
                "paper_id": paper_id,
                "status": "success",
                "data": {
                    "filename": paper_data['filename'],
                    "word_count": paper_data['word_count'],
                    "page_count": paper_data['page_count'],
                    "sections": list(paper_data['sections'].keys()),
                    "metadata": metadata
                }
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/flowchart/<paper_id>", methods=["GET"])
    def flowchart(paper_id):
        """Generate flowchart for a paper"""
        import torch
        try:
            # LAYER 1: Validate paper is dental-related before processing
            chunks = paper_analyzer.vector_store.get_paper_chunks(paper_id)
            if not chunks:
                return jsonify({"error": "paper not found"}), 404

            first_chunk_text = chunks[0].get('text', '')
            is_allowed, rejection_reason = domain_guardrail.check_input(first_chunk_text)
            if not is_allowed:
                return jsonify({
                    "error": "Flowcharts can only be generated for dentistry-related papers",
                    "blocked": True
                }), 400

            # Clear GPU cache before generation
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Generate flowchart image
            flowchart_image = paper_analyzer.generate_flowchart(paper_id)

            # Clear GPU cache after generation
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Return as SVG
            return send_file(
                BytesIO(flowchart_image),
                mimetype='image/svg+xml',
                as_attachment=False,
                download_name=f'{paper_id}_flowchart.svg'
            )

        except Exception as e:
            # Clear GPU cache on error
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return jsonify({"error": str(e)}), 500
    
    @api.route("/qa/<paper_id>", methods=["POST"])
    def qa(paper_id):
        """Answer question about a paper"""
        try:
            payload = request.get_json() or {}
            question = payload.get("question")

            if not question:
                return jsonify({"error": "question required"}), 400

            # LAYER 1: Pre-filter check
            is_allowed, rejection_reason = domain_guardrail.check_input(question)
            if not is_allowed:
                return jsonify({
                    "paper_id": paper_id,
                    "question": question,
                    "answer": rejection_reason,
                    "blocked": True
                }), 200

            # Answer question using RAG + model
            result = paper_analyzer.answer_question(question, paper_id=paper_id)

            # LAYER 3: Post-processing validation
            is_valid, final_answer = domain_guardrail.check_response(result['answer'])
            if not is_valid:
                return jsonify({
                    "paper_id": paper_id,
                    "question": question,
                    "answer": final_answer,
                    "blocked": True
                }), 200

            return jsonify({
                "paper_id": paper_id,
                "question": question,
                "answer": final_answer,
                "num_chunks_used": result['num_chunks']
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/summarize/<paper_id>", methods=["GET"])
    def summarize(paper_id):
        """Get summary of a paper"""
        try:
            # Get paper chunks
            chunks = paper_analyzer.vector_store.get_paper_chunks(paper_id)

            if not chunks:
                return jsonify({"error": "paper not found"}), 404

            # LAYER 1: Validate paper is dental (already validated at upload, but double-check)
            first_chunk_text = chunks[0].get('text', '')
            is_allowed, _ = domain_guardrail.check_input(first_chunk_text)
            if not is_allowed:
                return jsonify({
                    "error": "This paper does not appear to be related to dentistry",
                    "blocked": True
                }), 400

            # Get abstract or first few chunks
            abstract_text = ""
            for chunk in chunks:
                if chunk.get('section', '').lower() == 'abstract':
                    abstract_text = chunk.get('text', '')
                    break

            if not abstract_text:
                # Use first chunk
                abstract_text = chunks[0].get('text', '')[:1000]

            # Generate summary
            summary = paper_analyzer.model_router.summarize(abstract_text)

            # LAYER 3: Validate summary is dental-related
            is_valid, final_summary = domain_guardrail.check_response(summary)
            if not is_valid:
                final_summary = "Sorry, this summary could not be generated as the content is not related to dentistry."

            return jsonify({
                "paper_id": paper_id,
                "summary": final_summary
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    app.register_blueprint(api)
