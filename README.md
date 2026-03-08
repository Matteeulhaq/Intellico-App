# Intellico 🦷🤖

AI-powered dental research assistant that helps you analyze and understand scientific research papers.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16.1.6-black.svg)](https://nextjs.org/)

## ✨ Features

- **📄 PDF Upload & Processing**: Extract text, metadata, and structure from dental research papers
- **📝 AI Summarization**: Generate concise summaries using fine-tuned language models
- **💬 Q&A Chat**: Ask questions and get answers grounded in the paper's content (RAG)
- **🔑 Keyword Extraction**: Identify key terms and concepts automatically
- **📊 Flowchart Generation**: Visualize research methodologies and concept flows
- **🔍 Domain-Specific**: Fine-tuned for dentistry/oral health content only

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (local or Docker)
- Docker (optional, for containerized deployment)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Intellico-App

# Install all dependencies
npm run install:all
```

### Running the Application

**Option 1: Development Mode (Recommended)**
```bash
npm run dev
```
This starts both backend (port 2750) and frontend (port 3000) with hot-reload.

**Option 2: Docker Mode**
```bash
npm run docker:up
```
Access the application at http://localhost:2600

**Option 3: Individual Services**
```bash
# Backend only
npm run dev:backend

# Frontend only
npm run dev:frontend
```

## 📚 Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive guide explaining:
  - How the application works
  - Architecture and components
  - Step-by-step usage instructions
  - API endpoints
  - Troubleshooting guide

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development setup and workflow

- **[frontend/intellico/README.md](frontend/intellico/README.md)** - Frontend-specific documentation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                       │
│              Next.js 16 + React 19 + Tailwind           │
│                  Port: 3000 (dev) / 2600 (Docker)       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────┐
│                   Backend Layer                         │
│              Flask + Python + ML Models                 │
│                   Port: 2750                            │
└──────┬───────────────────────────┬─────────────────────┘
       │                           │
       ▼                           ▼
┌──────────────┐          ┌──────────────────┐
│   MongoDB    │          │  HuggingFace     │
│   Port:27018 │          │  Qwen2.5-1.5B    │
└──────────────┘          └──────────────────┘
```

### Technology Stack

**Frontend:**
- Next.js 16.1.6 with React 19.2.3
- TypeScript for type safety
- Tailwind CSS + shadcn/ui for styling
- Zustand for state management
- Fetch API for backend communication

**Backend:**
- Flask with CORS support
- PyPDF2 & pdfplumber for PDF processing
- Transformers + Torch for ML inference
- FAISS for vector search
- MongoDB for metadata storage

**ML Models:**
- **Base Model**: Qwen/Qwen2.5-1.5B-Instruct (1.5B parameters)
- **Fine-tuned Adapter**: matteeulhaq/Qwen-1.5B (dental domain)
- **Embedding Model**: BAAI/bge-small-en-v1.5 (semantic search)

## 📖 Usage

1. **Upload PDF**: Drag & drop dental research papers
2. **Generate Summary**: Get AI-powered summaries (short/medium/detailed)
3. **Ask Questions**: Chat with your papers using RAG
4. **View Keywords**: Extracted key terms and concepts
5. **Create Flowcharts**: Visualize methodologies and relationships

For detailed usage instructions, see [USER_GUIDE.md](USER_GUIDE.md).

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start all containers
npm run docker:up

# View logs
npm run docker:logs

# Stop containers
npm run docker:down
```

### Access Points (Docker)
- Frontend: http://localhost:2600
- Backend API: http://localhost:2750
- Health Check: http://localhost:2750/health

### WSL Users

If running on WSL and want to access from Windows browser:

```bash
# After starting Docker containers
ngrok http 2600
```

This forwards WSL localhost to a public ngrok URL accessible from Windows.

## 🔄 Updating Code

After making changes to the codebase:

```bash
# Stop containers
docker compose down

# Rebuild and restart
docker compose up -d --build
```

The containers will rebuild with your latest changes.

## 🧪 Testing

```bash
# Test backend health
curl http://localhost:2750/health

# Expected response:
{
  "status": "ok",
  "server": "running",
  "model": {
    "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
    "loaded": true
  }
}
```

## 🐛 Troubleshooting

### Common Issues

**Backend not starting?**
```bash
# Check MongoDB is running
docker ps | grep mongo

# Check environment variables
cat .env | grep MONGO_URI
```

**Frontend can't connect to backend?**
```bash
# Verify backend is running
curl http://localhost:2750/health

# Check frontend environment
cat frontend/intellico/.env.local
```

**Model loading errors?**
```bash
# Verify HuggingFace token
cat .env | grep HUGGINGFACE_TOKEN

# Check model access
# Visit: https://huggingface.co/settings/tokens
```

For more troubleshooting tips, see [USER_GUIDE.md](USER_GUIDE.md#troubleshooting).

## 📁 Project Structure

```
Intellico-App/
├── backend/                    # Flask backend + ML models
│   ├── app/
│   │   ├── main.py            # Flask app initialization
│   │   ├── controllers.py     # API route handlers
│   │   ├── paper_analyzer.py  # Core analysis engine
│   │   ├── rag/               # RAG components
│   │   ├── flowchart/         # Flowchart generation
│   │   └── guardrails/        # Content moderation
│   ├── storage/               # Uploaded PDFs
│   └── requirements.txt
│
├── frontend/
│   ├── intellico/             # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/          # Next.js app directory
│   │   │   ├── components/   # React components
│   │   │   ├── lib/          # API client & store
│   │   │   └── types/        # TypeScript types
│   │   ├── package.json
│   │   └── next.config.ts
│   └── Dockerfile
│
├── docker-compose.yml         # Docker orchestration
├── package.json              # Root scripts
├── .env                      # Environment variables
├── USER_GUIDE.md            # Comprehensive user guide
└── README.md                # This file
```

## 🔑 Environment Variables

Key environment variables in `.env`:

```bash
# MongoDB
MONGO_URI=mongodb://localhost:27018/intellico

# Model Configuration
BASE_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
ADAPTER_PATH=matteeulhaq/Qwen-1.5B
USE_HUGGINGFACE_REPO=true
HUGGINGFACE_TOKEN=hf_****************

# RAG Configuration
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
CHUNK_SIZE=512
TOP_K_CHUNKS=5

# Backend Server
FLASK_PORT=2750
FLASK_HOST=0.0.0.0
```

## 🙏 Acknowledgments

- **Qwen Team** for the base language model
- **HuggingFace** for model hosting and inference tools
- **FAISS** by Meta for efficient vector search
- **Dental research community** for domain expertise

## 📞 Support

For detailed documentation, troubleshooting, and usage guides, see:
- [USER_GUIDE.md](USER_GUIDE.md) - Complete user guide
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup

---
