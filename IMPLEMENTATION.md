# LLM Training and RAG Implementation

This document describes the complete implementation of the LLM training and RAG system for research paper analysis.

## Architecture Overview

The system consists of:
1. **QLoRA Fine-tuning** - Train local models (Gemma 2B/7B, Mistral 7B) on your dataset
2. **RAG Pipeline** - Retrieve relevant context from papers for question answering
3. **Flowchart Generation** - Generate methodology flowcharts using Mermaid/Graphviz
4. **Flask API** - RESTful endpoints for all functionality

## Directory Structure

```
backend/
├── training/              # Model training scripts
│   ├── config.py          # Training configuration
│   ├── data_loader.py     # Dataset loading and preprocessing
│   ├── train_qlora.py     # Main training script
│   └── requirements.txt   # Training dependencies
├── app/
│   ├── rag/               # RAG pipeline components
│   │   ├── chunker.py     # Text chunking
│   │   ├── embedder.py    # Embedding generation
│   │   ├── vector_store.py # MongoDB vector storage
│   │   ├── retriever.py   # Similarity search
│   │   └── rag_chain.py   # RAG orchestration
│   ├── models/            # Model inference
│   │   ├── local_model.py # Model loading and inference
│   │   ├── model_router.py # Task routing
│   │   └── prompt_templates.py # Prompt templates
│   ├── flowchart/         # Flowchart generation
│   │   ├── generator.py   # Main flowchart generator
│   │   ├── methodology_extractor.py # Extract workflow steps
│   │   ├── mermaid_renderer.py # Mermaid rendering
│   │   └── graphviz_renderer.py # Graphviz rendering
│   ├── pdf_processor.py   # PDF text extraction
│   ├── paper_analyzer.py  # Main orchestrator
│   ├── config.py         # Application configuration
│   └── controllers.py    # Flask API endpoints
└── models/adapters/      # Fine-tuned model adapters (created after training)
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your settings:
- MongoDB URI
- Model paths
- Storage paths

### 3. Train Models (Optional)

If you want to fine-tune models on your dataset:

```bash
cd backend/training
pip install -r requirements.txt

# For laptop (Gemma 2B)
python train_qlora.py --model google/gemma-2b-it --output-dir ../../models/adapters/gemma-2b

# For office PC (Mistral 7B or Gemma 7B)
python train_qlora.py --model mistralai/Mistral-7B-Instruct-v0.2 --output-dir ../../models/adapters/mistral-7b
```

### 4. Run Application

```bash
cd backend
python -m app.main
```

Or using Docker:
```bash
docker compose up -d --build
```

## API Endpoints

### Upload Paper
```bash
POST /api/upload
Content-Type: multipart/form-data
Body: file (PDF)

Response:
{
  "paper_id": "uuid",
  "status": "success",
  "data": {
    "filename": "...",
    "word_count": 1234,
    "page_count": 10,
    "sections": ["abstract", "introduction", ...],
    "metadata": {...}
  }
}
```

### Answer Question
```bash
POST /api/qa/<paper_id>
Content-Type: application/json
Body: {"question": "What is the main methodology?"}

Response:
{
  "paper_id": "...",
  "question": "...",
  "answer": "...",
  "num_chunks_used": 5
}
```

### Generate Flowchart
```bash
GET /api/flowchart/<paper_id>

Response: SVG image
```

### Summarize Paper
```bash
GET /api/summarize/<paper_id>

Response:
{
  "paper_id": "...",
  "summary": "..."
}
```

## How It Works

### 1. Paper Upload and Indexing
- PDF is processed to extract text and sections
- Text is chunked into overlapping segments
- Chunks are embedded using sentence-transformers
- Embeddings stored in MongoDB with metadata

### 2. Question Answering (RAG)
- User question is embedded
- Similar chunks are retrieved from MongoDB
- Retrieved context + question sent to fine-tuned model
- Model generates answer based on context

### 3. Flowchart Generation
- Fine-tuned model extracts keywords/terminologies and their relationships from paper
- Identifies conceptual flow: which terms lead to which other terms (Term1 → Term2 → Term3)
- Builds concept flow graph showing origins and evolution of research concepts
- Converts keyword relationships to Mermaid or Graphviz syntax
- Flowchart rendered as SVG/PNG image showing conceptual flow
- Uses free mermaid.ink API (no keys required)

### 4. Metadata Extraction
- Fine-tuned model extracts structured metadata
- Returns JSON with title, authors, keywords, etc.

## Model Training

The training system supports:
- **4-bit quantization** for memory efficiency
- **QLoRA** for parameter-efficient fine-tuning
- **Multiple tasks**: summarization, classification, metadata extraction, keyword extraction
- **Automatic data loading** from your training datasets

Training datasets are loaded from:
- `training_data/training_datasets/` - Pre-formatted instruction datasets
- `research_papers/research_papers/processed/` - Processed papers (optional)

## Configuration

Key configuration options in `backend/app/config.py`:
- `BASE_MODEL_NAME`: Base model to use (default: google/gemma-2b-it)
- `ADAPTER_PATH`: Path to fine-tuned adapter (optional)
- `EMBEDDING_MODEL`: Embedding model (default: BAAI/bge-small-en-v1.5)
- `FLOWCHART_RENDERER`: "mermaid" or "graphviz"

## Notes

- All models run locally - no external API keys required (except optional mermaid.ink for flowcharts)
- MongoDB is used for vector storage and retrieval
- Fine-tuned adapters are saved separately from base models
- System supports both Gemma and Mistral model families

