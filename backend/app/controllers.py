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
    
    @api.route("/status/<paper_id>", methods=["GET"])
    def status(paper_id):
        """Check processing status of uploaded paper"""
        try:
            # Check if paper exists and is fully processed
            chunks = paper_analyzer.vector_store.get_paper_chunks(paper_id)

            if not chunks:
                return jsonify({
                    "paper_id": paper_id,
                    "status": "processing",
                    "message": "Paper is still being processed"
                }), 202

            # Paper is fully processed
            return jsonify({
                "paper_id": paper_id,
                "status": "ready",
                "message": "Paper is fully processed and ready for summarization",
                "chunks_count": len(chunks)
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/paper/<paper_id>", methods=["GET"])
    def get_paper(paper_id):
        """Get complete paper data including extracted metadata"""
        try:
            # Get paper from database
            paper = paper_analyzer.vector_store.papers_collection.find_one({'paper_id': paper_id})

            if not paper:
                return jsonify({"error": "paper not found"}), 404

            # Convert ObjectId to string
            paper['_id'] = str(paper['_id'])

            # Return complete paper data
            return jsonify({
                "paper_id": paper.get('paper_id'),
                "filename": paper.get('filename'),
                "extracted_metadata": paper.get('extracted_metadata', {}),
                "metadata_extracted": paper.get('metadata_extracted', False),
                "metadata_extracted_at": paper.get('metadata_extracted_at'),
                "processing_error": paper.get('processing_error')
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/upload", methods=["POST"])
    def upload():
        """Upload and process PDF file"""
        import threading

        def process_paper_background(paper_id, paper_data):
            """Process paper in background thread with comprehensive logging"""
            import datetime
            import logging
            import traceback
            logger = logging.getLogger(__name__)

            try:
                logger.info(f"🚀 Background processing started for {paper_id}")
                print(f"🚀 Background processing started for {paper_id}")

                # Invalidate existing cache if paper is re-uploaded
                logger.info(f"🗑️ Clearing cache for {paper_id}")
                print(f"🗑️ Clearing cache for {paper_id}")
                paper_analyzer.vector_store.delete_summary(paper_id)

                # Index paper for RAG (slow operation)
                logger.info(f"📚 Starting paper indexing for {paper_id}")
                print(f"📚 Starting paper indexing for {paper_id}")
                paper_analyzer.index_paper(paper_data)
                logger.info(f"✅ Paper indexing complete for {paper_id}")
                print(f"✅ Paper indexing complete for {paper_id}")

                # Extract metadata using model (slow operation)
                logger.info(f"🔍 Starting metadata extraction for {paper_id}")
                print(f"🔍 Starting metadata extraction for {paper_id}")

                text_length = len(paper_data.get('full_text', ''))
                logger.info(f"📄 Paper text length: {text_length} characters")
                print(f"📄 Paper text length: {text_length} characters")

                metadata = paper_analyzer.extract_metadata(paper_data['full_text'])

                logger.info(f"✅ Metadata extracted: {list(metadata.keys()) if metadata else 'EMPTY'}")
                print(f"✅ Metadata extracted: {list(metadata.keys()) if metadata else 'EMPTY'}")

                if metadata:
                    keywords = metadata.get('keywords', [])
                    authors = metadata.get('authors', '')
                    logger.info(f"📝 Keywords found: {len(keywords)} keywords - {keywords[:5] if keywords else 'NONE'}")
                    logger.info(f"👤 Authors: {authors if authors else 'NONE'}")
                    print(f"📝 Keywords found: {len(keywords)} keywords - {keywords[:5] if keywords else 'NONE'}")
                    print(f"👤 Authors: {authors if authors else 'NONE'}")
                else:
                    logger.warning("⚠️ Metadata extraction returned empty/None")
                    print("⚠️ Metadata extraction returned empty/None")

                # Update paper with metadata in memory
                paper_data['extracted_metadata'] = metadata

                # FIX: Save extracted metadata to database
                logger.info(f"💾 Saving metadata to database for {paper_id}")
                print(f"💾 Saving metadata to database for {paper_id}")

                paper_analyzer.vector_store.store_paper(paper_id, {
                    'extracted_metadata': metadata,
                    'metadata_extracted': True,
                    'metadata_extracted_at': datetime.datetime.utcnow()
                })

                logger.info(f"✅ Metadata saved to database for {paper_id}")
                print(f"✅ Metadata saved to database for {paper_id}")

                # Verify save worked
                saved_paper = paper_analyzer.vector_store.papers_collection.find_one({'paper_id': paper_id})
                if saved_paper and saved_paper.get('extracted_metadata'):
                    saved_keywords = saved_paper['extracted_metadata'].get('keywords', [])
                    logger.info(f"✅ VERIFIED: Metadata found in database for {paper_id}")
                    logger.info(f"✅ VERIFIED: {len(saved_keywords)} keywords in database")
                    print(f"✅ VERIFIED: Metadata found in database for {paper_id}")
                    print(f"✅ VERIFIED: {len(saved_keywords)} keywords in database")
                else:
                    logger.error(f"❌ ERROR: Metadata NOT found in database for {paper_id}")
                    print(f"❌ ERROR: Metadata NOT found in database for {paper_id}")

                print(f"✅ Background processing complete for {paper_id}")
                print(f"✅ Extracted metadata saved: {len(metadata.get('keywords', []))} keywords")
                logger.info(f"✅ Background processing complete for {paper_id}")

            except Exception as e:
                logger.error(f"❌ ERROR in background processing for {paper_id}: {e}")
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                print(f"❌ ERROR in background processing for {paper_id}: {e}")
                print(f"❌ Traceback: {traceback.format_exc()}")

                # Save error status to database
                try:
                    logger.info(f"💾 Saving error status to database for {paper_id}")
                    paper_analyzer.vector_store.store_paper(paper_id, {
                        'processing_error': str(e),
                        'error_traceback': traceback.format_exc(),
                        'metadata_extracted': False,
                        'error_at': datetime.datetime.utcnow()
                    })
                    logger.info(f"✅ Error status saved to database for {paper_id}")
                except Exception as db_error:
                    logger.error(f"❌ Could not save error to database: {db_error}")
                    print(f"❌ Could not save error to database: {db_error}")

        try:
            f = request.files.get("file")
            if not f:
                return jsonify({"error": "no file"}), 400

            # Generate paper ID
            paper_id = str(uuid.uuid4())

            # Process PDF (fast operation - < 30 seconds)
            paper_data = pdf_processor.process_pdf(f, paper_id)

            # LAYER 1: Validate paper content is dentistry-related (fast)
            is_allowed, rejection_reason = domain_guardrail.check_input(
                paper_data['full_text'][:1000]  # Check first 1000 chars
            )
            if not is_allowed:
                return jsonify({
                    "error": "Uploaded paper does not appear to be related to dentistry or oral health",
                    "blocked": True
                }), 400

            # Start background processing for slow operations
            thread = threading.Thread(
                target=process_paper_background,
                args=(paper_id, paper_data)
            )
            thread.daemon = True
            thread.start()

            # Return immediately with basic info
            return jsonify({
                "paper_id": paper_id,
                "status": "processing",
                "message": "Paper uploaded successfully. Processing in background. Summarization will be available in 2-3 minutes.",
                "data": {
                    "filename": paper_data['filename'],
                    "word_count": paper_data['word_count'],
                    "page_count": paper_data['page_count'],
                    "sections": list(paper_data['sections'].keys()),
                    "processing_status": "background"
                }
            }), 202  # 202 = Accepted (processing in background)

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/flowchart/<paper_id>", methods=["GET"])
    def flowchart(paper_id):
        """Generate flowchart for a paper (with caching)"""
        import time
        import torch

        try:
            # CACHE CHECK: Try to retrieve cached flowchart first
            cached_flowchart = paper_analyzer.vector_store.get_flowchart(paper_id)

            if cached_flowchart:
                # Return cached SVG
                return send_file(
                    BytesIO(cached_flowchart['svg_data']),
                    mimetype='image/svg+xml',
                    as_attachment=False,
                    download_name=f'{paper_id}_flowchart.svg'
                )

            # CACHE MISS: Generate new flowchart
            start_time = time.time()

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

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            # CACHE STORAGE: Store the generated flowchart
            paper_analyzer.vector_store.store_flowchart(
                paper_id,
                flowchart_image,
                '',  # mermaid_code - not currently extracted
                {
                    'keywords_extracted': 0,  # Can be enhanced later
                    'relationships_extracted': 0,  # Can be enhanced later
                    'processing_time_ms': processing_time
                }
            )

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
        """Answer question about a paper (with caching)"""
        import time

        try:
            payload = request.get_json() or {}
            question = payload.get("question")

            if not question:
                return jsonify({"error": "question required"}), 400

            # CACHE CHECK: Try to retrieve cached Q&A first
            cached_qa = paper_analyzer.vector_store.get_qa(paper_id, question)

            if cached_qa:
                return jsonify({
                    "paper_id": paper_id,
                    "question": cached_qa['question'],
                    "answer": cached_qa['answer'],
                    "num_chunks_used": cached_qa['num_chunks_used'],
                    "cache_hit": True
                }), 200

            # CACHE MISS: Generate new answer
            start_time = time.time()

            # Get paper chunks for context
            chunks = paper_analyzer.vector_store.get_paper_chunks(paper_id)
            if not chunks:
                return jsonify({"error": "paper not found"}), 404

            # LAYER 1: Pre-filter check WITH PAPER CONTEXT
            # Provide paper content as context so guardrail knows it's a dental paper
            paper_context = chunks[0].get('text', '') + " " + chunks[1].get('text', '') if len(chunks) > 1 else chunks[0].get('text', '')
            is_allowed, rejection_reason = domain_guardrail.check_input(question, context=paper_context)
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

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            # CACHE STORAGE: Store the Q&A pair
            paper_analyzer.vector_store.store_qa(
                paper_id,
                question,
                final_answer,
                result['num_chunks'],
                processing_time
            )

            return jsonify({
                "paper_id": paper_id,
                "question": question,
                "answer": final_answer,
                "num_chunks_used": result['num_chunks'],
                "cache_hit": False
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @api.route("/summarize/<paper_id>", methods=["GET"])
    def summarize(paper_id):
        """Get comprehensive summary of a paper (with caching and parallel processing)"""
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed

        try:
            # CACHE CHECK: Try to retrieve cached summary first
            cached_summary = paper_analyzer.vector_store.get_summary(paper_id)

            if cached_summary:
                return jsonify({
                    "paper_id": paper_id,
                    "summary": cached_summary['summary'],
                    "section_summaries": cached_summary['section_summaries'],
                    "key_findings": cached_summary['key_findings'],
                    "metadata": {
                        **cached_summary['metadata'],
                        "cache_hit": True,
                        "times_accessed": cached_summary['cache_stats']['times_accessed']
                    }
                }), 200

            # CACHE MISS: Generate new summary
            start_time = time.time()

            # Get paper chunks (reuse existing pattern)
            chunks = paper_analyzer.vector_store.get_paper_chunks(paper_id)

            if not chunks:
                return jsonify({"error": "paper not found"}), 404

            # LAYER 1: Validate paper is dental
            first_chunk_text = chunks[0].get('text', '')
            is_allowed, _ = domain_guardrail.check_input(first_chunk_text)
            if not is_allowed:
                return jsonify({
                    "error": "This paper does not appear to be related to dentistry",
                    "blocked": True
                }), 400

            # STAGE 1: Group chunks by section
            sections = {}
            for chunk in chunks:
                section = chunk.get('section', '').lower()
                # Normalize section names
                if section not in ['abstract', 'introduction', 'methodology', 'results', 'discussion', 'conclusion']:
                    section = 'other'
                if section not in sections:
                    sections[section] = []
                sections[section].append(chunk.get('text', ''))

            # Combine chunks within each section
            section_texts = {}
            for section, text_parts in sections.items():
                combined = '\n\n'.join(text_parts)
                # Limit to prevent OOM (same pattern as existing methods)
                if len(combined) > 3000:
                    combined = combined[:3000] + "..."
                section_texts[section] = combined

            # STAGE 2: Summarize sections in PARALLEL (3x faster)
            section_summaries = {}
            priority_sections = ['abstract', 'introduction', 'methodology', 'results', 'discussion', 'conclusion']

            def summarize_section(section_name):
                """Helper function for parallel processing"""
                if section_name in section_texts:
                    return section_name, paper_analyzer.model_router.summarize_section(
                        section_name,
                        section_texts[section_name]
                    )
                return None

            # Use ThreadPoolExecutor for parallel section summarization
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit all section summarization tasks
                future_to_section = {
                    executor.submit(summarize_section, section): section
                    for section in priority_sections
                }

                # Collect results as they complete
                for future in as_completed(future_to_section):
                    result = future.result()
                    if result:
                        section_name, summary = result
                        section_summaries[section_name] = summary

            # STAGE 3: Extract key findings using RAG
            key_findings = paper_analyzer.model_router.extract_key_findings(
                paper_id,
                paper_analyzer.rag_chain
            )

            # STAGE 4: Generate comprehensive summary
            comprehensive_summary = paper_analyzer.model_router.generate_comprehensive_summary(
                section_summaries,
                key_findings
            )

            # LAYER 3: Validate summary is dental-related
            is_valid, final_summary = domain_guardrail.check_response(comprehensive_summary)
            if not is_valid:
                final_summary = "Sorry, this summary could not be generated as the content is not related to dentistry."

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            # Prepare summary data
            summary_data = {
                "paper_id": paper_id,
                "summary": final_summary,
                "section_summaries": section_summaries,
                "key_findings": key_findings,
                "metadata": {
                    "total_chunks": len(chunks),
                    "sections_processed": len(section_summaries),
                    "method": "multi_stage_hierarchical",
                    "generated_at": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),
                    "processing_time_ms": processing_time
                }
            }

            # CACHE STORAGE: Store the generated summary
            paper_analyzer.vector_store.store_summary(paper_id, summary_data)

            return jsonify({
                **summary_data,
                "metadata": {
                    **summary_data["metadata"],
                    "cache_hit": False
                }
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/cache/stats", methods=["GET"])
    def cache_stats():
        """Get comprehensive cache performance statistics"""
        try:
            summary_stats = paper_analyzer.vector_store.get_cache_stats()

            # Add flowchart cache stats
            flowchart_count = paper_analyzer.vector_store.flowcharts_collection.count_documents({})
            avg_flowchart_accesses = 0
            if flowchart_count > 0:
                pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$cache_stats.times_accessed"}}}]
                result = list(paper_analyzer.vector_store.flowcharts_collection.aggregate(pipeline))
                avg_flowchart_accesses = result[0]['avg'] if result else 0

            # Add Q&A cache stats
            qa_count = paper_analyzer.vector_store.qa_cache_collection.count_documents({})
            avg_qa_accesses = 0
            if qa_count > 0:
                pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$cache_stats.times_accessed"}}}]
                result = list(paper_analyzer.vector_store.qa_cache_collection.aggregate(pipeline))
                avg_qa_accesses = result[0]['avg'] if result else 0

            return jsonify({
                "summaries": summary_stats,
                "flowcharts": {
                    "total_cached": flowchart_count,
                    "average_access_count": round(avg_flowchart_accesses, 2)
                },
                "qa": {
                    "total_cached": qa_count,
                    "average_access_count": round(avg_qa_accesses, 2)
                }
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/cache/clear/<paper_id>", methods=["DELETE"])
    def clear_cache(paper_id):
        """Clear all cached data for a specific paper"""
        try:
            summary_deleted = paper_analyzer.vector_store.delete_summary(paper_id)
            flowchart_deleted = paper_analyzer.vector_store.delete_flowchart(paper_id)
            qa_deleted = paper_analyzer.vector_store.delete_qa_all(paper_id)

            cleared_types = []
            if summary_deleted: cleared_types.append("summary")
            if flowchart_deleted: cleared_types.append("flowchart")
            if qa_deleted > 0: cleared_types.append(f"qa ({qa_deleted} entries)")

            if cleared_types:
                return jsonify({
                    "message": f"Cache cleared for {paper_id}",
                    "paper_id": paper_id,
                    "cleared": cleared_types
                }), 200
            else:
                return jsonify({"error": "Paper not found in cache"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route("/cache/clear", methods=["DELETE"])
    def clear_all_cache():
        """Clear all cached data (admin operation)"""
        try:
            summary_result = paper_analyzer.vector_store.summaries_collection.delete_many({})
            flowchart_result = paper_analyzer.vector_store.flowcharts_collection.delete_many({})
            qa_result = paper_analyzer.vector_store.qa_cache_collection.delete_many({})

            total_cleared = (
                summary_result.deleted_count +
                flowchart_result.deleted_count +
                qa_result.deleted_count
            )

            return jsonify({
                "message": f"Cleared {total_cleared} cached entries",
                "breakdown": {
                    "summaries": summary_result.deleted_count,
                    "flowcharts": flowchart_result.deleted_count,
                    "qa_entries": qa_result.deleted_count
                },
                "count": total_cleared
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    app.register_blueprint(api)
