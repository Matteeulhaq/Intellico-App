from flask import Flask, jsonify
from flask_cors import CORS
from .controllers import register_routes

app = Flask(__name__)
CORS(app)

# load config from environment or .env
app.config.from_prefixed_env()  # convenience if using python-dotenv in dev

register_routes(app)

@app.route("/health")
def health():
    return jsonify({"status":"ok"}), 200
