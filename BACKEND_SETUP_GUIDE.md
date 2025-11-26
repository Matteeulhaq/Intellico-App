# Backend Server Setup Guide

This guide will help you configure and run the Intellico backend server with your fine-tuned model.

## Prerequisites

1. **Fine-tuned model uploaded to HuggingFace** (or available locally)
2. **MongoDB running** (local or remote)
3. **Python 3.11+** with virtual environment
4. **All dependencies installed**

## Step 1: Configure Environment Variables

### Create `.env` File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your configuration:

   ```bash
   # Model Configuration (REQUIRED)
   ADAPTER_PATH=your-username/your-model-name
   USE_HUGGINGFACE_REPO=true
   HUGGINGFACE_TOKEN=your-hf-token-here
   BASE_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
   
   # MongoDB (REQUIRED)
   # Use port 27017 if MongoDB is on default port
   # Use port 27018 if you mapped Docker container to 27018 (e.g., -p 27018:27017)
   MONGO_URI=mongodb://localhost:27018/
   
   # Server Configuration (OPTIONAL - has defaults)
   FLASK_HOST=0.0.0.0
   FLASK_PORT=2750
   FLASK_DEBUG=false
   
   # Storage (OPTIONAL - has defaults)
   STORAGE_PATH=./storage
   ```

### Key Variables Explained

- **`ADAPTER_PATH`**: Your HuggingFace repository ID (e.g., `mattee/my-fine-tuned-model`) or local path
- **`USE_HUGGINGFACE_REPO`**: Set to `true` if using HuggingFace, `false` for local path
- **`HUGGINGFACE_TOKEN`**: Required if your model is private. Get it from [HuggingFace Settings](https://huggingface.co/settings/tokens)
- **`MONGO_URI`**: MongoDB connection string. Default: `mongodb://localhost:27017/`

## Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 3: Start MongoDB

### Option A: Local MongoDB

```bash
# If MongoDB is installed locally, start it:
sudo systemctl start mongod
# or
mongod
```

### Option B: Docker MongoDB

**Standard port mapping:**
```bash
docker run -d -p 27017:27017 --name mongo mongo:6.0
```
Then use: `MONGO_URI=mongodb://localhost:27017/`

**Custom port mapping (if 27017 is already in use):**
```bash
docker run -d -p 27018:27017 --name mongo mongo:6.0
```
Then use: `MONGO_URI=mongodb://localhost:27018/`

**Note:** The format is `-p HOST_PORT:CONTAINER_PORT`. The container always uses 27017 internally, but you can map it to any available port on your host.

### Option C: Use Existing MongoDB

Just ensure your `MONGO_URI` in `.env` points to your MongoDB instance with the correct port.

## Step 4: Create Storage Directory

```bash
mkdir -p backend/storage
```

## Step 5: Start the Server

```bash
cd backend
python -m app.main
```

### Expected Output

You should see:

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

## Step 6: Test the Server

### Health Check

```bash
curl http://localhost:2750/health
```

Expected response:
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

### Test Upload Endpoint

```bash
curl -X POST http://localhost:2750/api/upload \
  -F "file=@path/to/your/paper.pdf"
```

## Troubleshooting

### Model Not Loading

**Error: "Model not found"**
- Verify `ADAPTER_PATH` is correct in `.env`
- Check if model is public or you have the correct `HUGGINGFACE_TOKEN`
- Ensure `USE_HUGGINGFACE_REPO=true` if using HuggingFace

**Error: "Out of memory"**
- Model is too large for your GPU
- Try using a smaller base model
- Check GPU memory: `nvidia-smi`

### MongoDB Connection Issues

**Error: "Connection refused"**
- Ensure MongoDB is running: 
  - Docker: `docker ps | grep mongo`
  - Local: `sudo systemctl status mongod`
- Check `MONGO_URI` in `.env` matches your MongoDB port:
  - If Docker mapped to 27018: `MONGO_URI=mongodb://localhost:27018/`
  - If default port: `MONGO_URI=mongodb://localhost:27017/`
- Test connection: `mongosh mongodb://localhost:27018/` (use your actual port)

### Server Not Starting

**Error: "Address already in use"**
- Port 2750 is already in use
- Change `FLASK_PORT` in `.env` to a different port
- Or stop the process using port 2750: `lsof -ti:2750 | xargs kill`

**Error: "Module not found"**
- Ensure you're in the `backend` directory
- Install dependencies: `pip install -r requirements.txt`
- Activate virtual environment if using one

### Import Errors

**Error: "No module named 'app'"**
- Run from `backend` directory: `cd backend`
- Use: `python -m app.main` (not `python app/main.py`)

## API Endpoints

### Health Check
```
GET /health
```

### Upload Paper
```
POST /api/upload
Content-Type: multipart/form-data
Body: file (PDF)
```

### Question Answering
```
POST /api/qa/<paper_id>
Content-Type: application/json
Body: {"question": "Your question here"}
```

### Summarize Paper
```
GET /api/summarize/<paper_id>
```

### Generate Flowchart
```
GET /api/flowchart/<paper_id>
Returns: SVG image
```

## Next Steps

1. **Test with a PDF**: Upload a research paper and test all endpoints
2. **Check logs**: Monitor server output for any errors
3. **Frontend integration**: Connect your frontend to `http://localhost:2750/api`
4. **Production deployment**: Use gunicorn for production (see Dockerfile)

## Production Deployment

For production, use gunicorn:

```bash
gunicorn --bind 0.0.0.0:2750 --workers 4 --threads 4 app.main:app
```

Or use Docker:
```bash
docker compose up -d --build
```

## Support

If you encounter issues:
1. Check the server logs for error messages
2. Verify all environment variables are set correctly
3. Test MongoDB connection separately
4. Ensure model loads in training scripts first

