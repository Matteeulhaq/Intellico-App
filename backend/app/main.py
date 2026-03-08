import os
import signal
import sys
# Set PyTorch CUDA memory allocator config BEFORE importing torch
# This must be done before any PyTorch imports
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
from .controllers import register_routes

# Load .env file before creating Flask app
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Also try loading from backend directory
    load_dotenv(Path(__file__).parent.parent / '.env')

app = Flask(__name__)
CORS(app)

# Load config from environment variables (now includes .env file)
app.config.from_prefixed_env()

register_routes(app)

@app.route("/health")
def health():
    """Health check endpoint with model status"""
    from .config import Config
    from .controllers import paper_analyzer
    config = Config()
    
    # Check if model is loaded
    model_loaded = False
    try:
        if hasattr(paper_analyzer, 'model_router') and paper_analyzer.model_router:
            model_loaded = paper_analyzer.model_router.model is not None
    except:
        pass
    
    health_status = {
        "status": "ok",
        "server": "running",
        "model": {
            "base_model": config.BASE_MODEL_NAME,
            "adapter_path": config.ADAPTER_PATH if config.ADAPTER_PATH else "none (using base model)",
            "use_hf_repo": config.USE_HUGGINGFACE_REPO,
            "loaded": model_loaded
        },
        "mongodb": {
            "uri": config.MONGO_URI.split('@')[-1] if '@' in config.MONGO_URI else config.MONGO_URI
        }
    }
    
    return jsonify(health_status), 200

if __name__ == "__main__":
    # Get configuration from environment variables
    port = int(os.getenv("FLASK_PORT", "2750"))
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    from .config import Config
    config = Config()
    
    # Print startup information
    print("\n" + "=" * 60)
    print("Intellico Backend Server")
    print("=" * 60)
    print(f"\nModel Configuration:")
    print(f"  Base Model: {config.BASE_MODEL_NAME}")
    if config.ADAPTER_PATH:
        print(f"  Adapter: {config.ADAPTER_PATH}")
        print(f"  HuggingFace Repo: {config.USE_HUGGINGFACE_REPO}")
    else:
        print(f"  Adapter: None (using base model)")
    print(f"\nServer Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Debug Mode: {debug}")
    print(f"\nMongoDB:")
    print(f"  URI: {config.MONGO_URI}")
    print(f"\n" + "=" * 60)
    print(f"Starting server on http://{host}:{port}")
    print("=" * 60)
    print("\nAPI Endpoints:")
    print(f"  Health Check: http://{host}:{port}/health")
    print(f"  Upload Paper: http://{host}:{port}/api/upload")
    print(f"  Question Answer: http://{host}:{port}/api/qa/<paper_id>")
    print(f"  Summarize: http://{host}:{port}/api/summarize/<paper_id>")
    print(f"  Flowchart: http://{host}:{port}/api/flowchart/<paper_id>")
    print("\nPress CTRL+C to stop the server\n")

    # Global flag to indicate shutdown
    shutdown_flag = False

    def cleanup_and_exit(signum=None, frame=None):
        """Gracefully cleanup resources before exiting"""
        global shutdown_flag
        if shutdown_flag:
            # Already shutting down, force exit
            os._exit(0)

        shutdown_flag = True
        print("\n\nShutting down gracefully...")

        try:
            # Cleanup model and GPU memory
            if 'paper_analyzer' in sys.modules:
                from .controllers import paper_analyzer
                if hasattr(paper_analyzer, 'model_router') and paper_analyzer.model_router:
                    print("  - Unloading model...")
                    # Clean up model
                    if hasattr(paper_analyzer.model_router, 'model'):
                        del paper_analyzer.model_router.model
                    paper_analyzer.model_router.model = None
                # Clean up any remaining references
                if hasattr(paper_analyzer, 'model_router'):
                    paper_analyzer.model_router = None

            # Cleanup PyTorch CUDA memory
            if 'torch' in sys.modules:
                import torch
                if torch.cuda.is_available():
                    print("  - Clearing GPU cache...")
                    torch.cuda.empty_cache()

            # Force garbage collection
            import gc
            gc.collect()
            print("  - Cleanup complete")

        except Exception as e:
            print(f"  - Cleanup error: {e}")

        print("Goodbye!\n")
        os._exit(0)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup_and_exit)   # Ctrl+C
    signal.signal(signal.SIGTERM, cleanup_and_exit) # terminate command

    try:
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    except KeyboardInterrupt:
        cleanup_and_exit()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        cleanup_and_exit()
