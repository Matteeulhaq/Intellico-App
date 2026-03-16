from flask import Blueprint, request, jsonify, current_app, send_file, Response, stream_with_context
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
        """Generate flowchart for a paper with streaming progress updates"""
        import time
        import base64
        import torch
        from .utils.streaming import StreamingContext

        # CACHE CHECK: Try to retrieve cached flowchart first
        cached_flowchart = paper_analyzer.vector_store.get_flowchart(paper_id)

        if cached_flowchart:
            # Return cached SVG as-is for backward compatibility
            return send_file(
                BytesIO(cached_flowchart['svg_data']),
                mimetype='image/svg+xml',
                as_attachment=False,
                download_name=f'{paper_id}_flowchart.svg'
            )

        # CACHE MISS: Return streaming response
        def generate_flowchart_stream():
            context = StreamingContext()
            start_time = time.time()

            try:
                # Validate
                context.emit_progress("validation", "Validating paper...", 10)
                chunks = paper_analyzer.vector_store.get_paper_chunks(paper_id)
                if not chunks:
                    context.emit_error("Paper not found")
                    return

                # LAYER 1: Validate paper is dental-related before processing
                first_chunk_text = chunks[0].get('text', '')
                is_allowed, rejection_reason = domain_guardrail.check_input(first_chunk_text)
                if not is_allowed:
                    context.emit_error("Flowcharts can only be generated for dentistry-related papers")
                    return

                # Reconstruct text
                context.emit_progress("preparation", "Preparing text...", 20)
                full_text_parts = [chunk.get('text', '') for chunk in chunks]
                full_text = "\n\n".join(full_text_parts)

                # Extract keywords and relationships
                context.emit_progress("extraction", "Extracting keyword relationships...", 40)
                from .flowchart.keyword_relationship_extractor import KeywordRelationshipExtractor
                extractor = KeywordRelationshipExtractor(paper_analyzer.model_router)

                # Limit text length
                if len(full_text) > 4000:
                    full_text = full_text[:4000] + "..."

                result = paper_analyzer.model_router.extract_keyword_relationships(full_text)
                keywords, relationships = extractor._parse_relationships(result)

                # Build concept flow
                context.emit_progress("building", "Building concept flow...", 70)
                concept_flow = extractor.build_concept_flow(keywords, relationships)

                # Render diagram
                context.emit_progress("rendering", "Rendering diagram...", 85)
                from .flowchart.mermaid_renderer import MermaidRenderer
                renderer = MermaidRenderer(use_api=True)
                mermaid_code = renderer.keywords_to_mermaid(concept_flow, relationships)
                svg_data = renderer.render(mermaid_code, "svg")

                # Calculate processing time
                processing_time = int((time.time() - start_time) * 1000)

                # CACHE STORAGE: Store the generated flowchart
                paper_analyzer.vector_store.store_flowchart(
                    paper_id,
                    svg_data,
                    mermaid_code,
                    {
                        'keywords_extracted': len(keywords),
                        'relationships_extracted': len(relationships),
                        'processing_time_ms': processing_time
                    }
                )

                # Return as base64 encoded SVG in JSON
                context.emit_complete({
                    "svg": base64.b64encode(svg_data).decode(),
                    "mermaid_code": mermaid_code,
                    "metadata": {
                        "keywords_extracted": len(keywords),
                        "relationships_extracted": len(relationships),
                        "processing_time_ms": processing_time,
                        "cache_hit": False
                    }
                })

            except Exception as e:
                context.emit_error(str(e))

            # Yield all events
            for event in context.generator():
                yield event

        return Response(
            stream_with_context(generate_flowchart_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    
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
        """Get comprehensive summary with streaming progress updates"""
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from .utils.streaming import StreamingContext

        # CACHE CHECK: Return immediately if cached
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

        # CACHE MISS: Return streaming response
        def generate_summary_stream():
            context = StreamingContext()
            start_time = time.time()

            try:
                # Validate
                context.emit_progress("validation", "Validating paper...", 5)
                chunks = paper_analyzer.vector_store.get_paper_chunks(paper_id)
                if not chunks:
                    context.emit_error("Paper not found")
                    return

                # LAYER 1: Validate paper is dental
                first_chunk_text = chunks[0].get('text', '')
                is_allowed, _ = domain_guardrail.check_input(first_chunk_text)
                if not is_allowed:
                    context.emit_error("This paper does not appear to be related to dentistry")
                    return

                # STAGE 1: Group chunks by section
                context.emit_progress("preparation", "Preparing sections...", 10)
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

                # STAGE 2: Summarize sections with progress updates
                section_summaries = {}
                priority_sections = ['abstract', 'introduction', 'methodology', 'results', 'discussion', 'conclusion']

                for i, section in enumerate(priority_sections):
                    if section in section_texts:
                        context.emit_progress("sections", f"Summarizing {section}...", 15 + i * 5)
                        summary = paper_analyzer.model_router.summarize_section(
                            section,
                            section_texts[section]
                        )
                        section_summaries[section] = summary

                # STAGE 3: Extract key findings using RAG
                context.emit_progress("findings", "Extracting key findings...", 50)
                key_findings = paper_analyzer.model_router.extract_key_findings(
                    paper_id,
                    paper_analyzer.rag_chain
                )

                # STAGE 4: Generate comprehensive summary
                context.emit_progress("synthesis", "Generating comprehensive summary...", 75)
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
                        "processing_time_ms": processing_time,
                        "cache_hit": False
                    }
                }

                # CACHE STORAGE: Store the generated summary
                paper_analyzer.vector_store.store_summary(paper_id, summary_data)

                # Send completion
                context.emit_complete(summary_data)

            except Exception as e:
                context.emit_error(str(e))

            # Yield all events
            for event in context.generator():
                yield event

        return Response(
            stream_with_context(generate_summary_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )

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
