from flask import Blueprint, request, jsonify, current_app

def register_routes(app):
    api = Blueprint("api", __name__, url_prefix="/api")
    
    @api.route("/upload", methods=["POST"])
    def upload():
        # expects multipart/form-data with pdf file
        f = request.files.get("file")
        if not f:
            return jsonify({"error":"no file"}), 400
        res = process_upload(f)   # implement parsing, save to storage, store metadata
        return jsonify(res), 200

    @api.route("/flowchart/<paper_id>", methods=["GET"])
    def flowchart(paper_id):
        # Calls external flowchart API or internal generator if available
        res = generate_flowchart(paper_id)
        return jsonify(res), 200

    @api.route("/qa/<paper_id>", methods=["POST"])
    def qa(paper_id):
        payload = request.get_json() or {}
        q = payload.get("question")
        if not q:
            return jsonify({"error":"question required"}), 400
        ans = answer_question(paper_id, q)
        return jsonify(ans), 200

    app.register_blueprint(api)
