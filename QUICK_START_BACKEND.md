# Quick Start: Backend Server

## 🚀 Quick Setup (5 minutes)

### 1. Create `.env` file in project root

```bash
cd /home/mattee/Intellico-App
cat > .env << 'EOF'
# Model Configuration
ADAPTER_PATH=your-username/your-model-name
USE_HUGGINGFACE_REPO=true
HUGGINGFACE_TOKEN=your-hf-token-here
BASE_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct

# MongoDB
# Use port 27018 if you ran: docker run -d -p 27018:27017 --name mongo mongo:6.0
# Use port 27017 if MongoDB is on default port
MONGO_URI=mongodb://localhost:27018/

# Server (optional - has defaults)
FLASK_PORT=2750
FLASK_HOST=0.0.0.0
FLASK_DEBUG=false

# Storage (optional - has defaults)
STORAGE_PATH=./storage
EOF
```

**Replace:**
- `your-username/your-model-name` with your actual HuggingFace repo ID
- `your-hf-token-here` with your HuggingFace token

### 2. Ensure MongoDB is running

**Option A: Docker (what you used)**
```bash
# You already ran this:
sudo docker run -d -p 27018:27017 --name mongo mongo:6.0

# Check if it's running:
docker ps | grep mongo
```

**Option B: Local MongoDB**
```bash
# Check if MongoDB is running
sudo systemctl status mongod

# If not running, start it:
sudo systemctl start mongod
```

### 3. Create storage directory

```bash
mkdir -p backend/storage
```

### 4. Start the server

```bash
cd backend
python -m app.main
```

## ✅ Verify It's Working

### Check Health Endpoint

```bash
curl http://localhost:2750/health
```

You should see:
```json
{
  "status": "ok",
  "server": "running",
  "model": {
    "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
    "adapter_path": "your-username/your-model-name",
    "use_hf_repo": true,
    "loaded": true
  },
  "mongodb": {
    "uri": "mongodb://localhost:27017/"
  }
}
```

## 📝 What You'll See

When the server starts, you'll see:

```
============================================================
Intellico Backend Server
============================================================

Model Configuration:
  Base Model: Qwen/Qwen2.5-1.5B-Instruct
  Adapter: your-username/your-model-name
  HuggingFace Repo: True

Server Configuration:
  Host: 0.0.0.0
  Port: 2750
  Debug Mode: False

MongoDB:
  URI: mongodb://localhost:27017/

============================================================
Starting server on http://0.0.0.0:2750
============================================================

API Endpoints:
  Health Check: http://0.0.0.0:2750/health
  Upload Paper: http://0.0.0.0:2750/api/upload
  Question Answer: http://0.0.0.0:2750/api/qa/<paper_id>
  Summarize: http://0.0.0.0:2750/api/summarize/<paper_id>
  Flowchart: http://0.0.0.0:2750/api/flowchart/<paper_id>

Press CTRL+C to stop the server

Loading embedding model: BAAI/bge-small-en-v1.5
Loading base model: Qwen/Qwen2.5-1.5B-Instruct
Model loaded successfully
 * Running on http://0.0.0.0:2750
```

## 🧪 Test the API

### Upload a PDF

```bash
curl -X POST http://localhost:2750/api/upload \
  -F "file=@path/to/your/paper.pdf"
```

### Ask a Question

```bash
curl -X POST http://localhost:2750/api/qa/<paper_id> \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main methodology?"}'
```

## ❌ Troubleshooting

**Model not loading?**
- Check `ADAPTER_PATH` in `.env` is correct
- Verify `HUGGINGFACE_TOKEN` is set (if model is private)
- Ensure `USE_HUGGINGFACE_REPO=true`

**MongoDB connection error?**
- Start MongoDB: `sudo systemctl start mongod`
- Check `MONGO_URI` in `.env`

**Port already in use?**
- Change `FLASK_PORT` in `.env` to a different port
- Or stop the process: `lsof -ti:2750 | xargs kill`

For detailed setup, see `BACKEND_SETUP_GUIDE.md`

