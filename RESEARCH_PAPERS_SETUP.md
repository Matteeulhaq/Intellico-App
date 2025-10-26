# Research Papers Setup Guide

This guide will help you set up and process your 42 research papers for model training in the Intellico-App project.

## 🎯 Overview

The system is designed to:
- Extract and process text from PDF research papers
- Generate embeddings for semantic search
- Train machine learning models for classification, summarization, and Q&A
- Provide API endpoints for interacting with the processed papers

## 📁 Directory Structure

After setup, your project will have the following structure:

```
Intellico-App/
├── research_papers/           # Main directory for research papers
│   ├── raw_pdfs/             # Original PDF files
│   ├── processed/            # Processed JSON files
│   ├── embeddings/           # Vector embeddings and ChromaDB
│   └── trained_models/       # Trained ML models
├── backend/
│   ├── app/
│   │   ├── pdf_processor.py     # PDF text extraction
│   │   ├── ml_processor.py      # ML processing and embeddings
│   │   ├── batch_processor.py   # Batch processing script
│   │   ├── training_scripts.py  # Model training
│   │   └── services.py          # API endpoints
│   └── requirements.txt         # Updated with ML dependencies
└── setup_research_papers.py     # Setup script
```

## 🚀 Quick Start

### 1. Prepare Your PDFs

Place your 42 research papers in a directory (e.g., `/path/to/your/pdfs/`).

### 2. Run the Setup Script

```bash
# Basic setup (process PDFs only)
python setup_research_papers.py --pdf-dir /path/to/your/pdfs

# Full setup (process PDFs + train models)
python setup_research_papers.py --pdf-dir /path/to/your/pdfs --train-models

# Skip processing, only setup directories
python setup_research_papers.py --pdf-dir /path/to/your/pdfs --skip-processing
```

### 3. Start the Application

```bash
# Build and start the application
docker compose up -d --build

# For WSL users, also run:
ngrok http 2600
```

## 📊 What Happens During Processing

### Phase 1: PDF Processing
- **Text Extraction**: Uses PyMuPDF and pdfplumber for robust text extraction
- **Text Cleaning**: Removes headers, footers, URLs, and normalizes whitespace
- **Section Detection**: Automatically identifies abstract, introduction, methodology, results, discussion, conclusion, and references
- **Metadata Extraction**: Extracts title, authors, publication info from PDF metadata

### Phase 2: ML Processing
- **Text Chunking**: Splits papers into manageable chunks for better embedding quality
- **Embedding Generation**: Creates vector embeddings using Sentence Transformers
- **Vector Storage**: Stores embeddings in ChromaDB for fast similarity search
- **FAISS Index**: Creates FAISS index for efficient vector similarity search

### Phase 3: Model Training
- **Classification Model**: BERT-based model to classify text sections
- **Summarization Model**: BART-based model for text summarization
- **Q&A Model**: DistilBERT-based model for question answering

## 🔧 API Endpoints

After processing, you can use these API endpoints:

### List Papers
```bash
GET /api/papers
```
Returns list of all processed papers with metadata.

### Semantic Search
```bash
POST /api/search
Content-Type: application/json

{
  "query": "machine learning applications in healthcare",
  "top_k": 5
}
```

### Ask Questions
```bash
POST /api/qa/{paper_id}
Content-Type: application/json

{
  "question": "What methodology was used in this study?"
}
```

### Get Paper Details
```bash
GET /api/paper/{paper_id}
```

### Batch Process
```bash
POST /api/batch-process
Content-Type: application/json

{
  "pdf_directory": "/path/to/pdfs"
}
```

### Dataset Report
```bash
GET /api/dataset-report
```

## 📈 Monitoring and Reports

The system generates several reports:

1. **Processing Summary**: `research_papers/processing_summary.json`
2. **Dataset Report**: `research_papers/dataset_report.json`
3. **Training Results**: `research_papers/trained_models/*_results.json`
4. **Setup Summary**: `research_papers/setup_summary.json`

## 🛠️ Manual Processing

If you prefer to process papers manually:

### 1. Process Individual PDFs
```python
from backend.app.pdf_processor import PDFProcessor

processor = PDFProcessor()
result = processor.process_pdf("/path/to/paper.pdf", "paper_id")
```

### 2. Batch Process
```python
from backend.app.batch_processor import BatchProcessor

processor = BatchProcessor()
summary = processor.process_all_papers("/path/to/pdfs")
```

### 3. Generate Embeddings
```python
from backend.app.ml_processor import MLProcessor

ml_processor = MLProcessor()
ml_processor.initialize_models()
embeddings_data = ml_processor.process_paper_embeddings(processed_papers)
```

### 4. Train Models
```python
from backend.app.training_scripts import ResearchPaperTrainer

trainer = ResearchPaperTrainer()
results = trainer.train_all_models()
```

## 🔍 Troubleshooting

### Common Issues

1. **Permission Denied**: Make sure you have write permissions to the storage directory
2. **Memory Issues**: Large PDFs might require more memory. Consider processing in smaller batches
3. **Model Download**: First run might take time to download pre-trained models
4. **Docker Issues**: Ensure Docker has enough memory allocated (recommend 4GB+)

### Logs

Check the following log files:
- `batch_processing.log` - Processing logs
- Docker logs: `docker compose logs backend`

### Performance Tips

1. **Processing Speed**: Use SSD storage for better I/O performance
2. **Memory Usage**: Process papers in batches if you have memory constraints
3. **Model Size**: Consider using smaller models for faster processing

## 📚 Advanced Usage

### Custom Models

You can customize the models by modifying the configurations in:
- `backend/app/ml_processor.py` - Embedding models
- `backend/app/training_scripts.py` - Training configurations

### Custom Processing

Extend the processing pipeline by:
1. Modifying `pdf_processor.py` for custom text extraction
2. Updating `ml_processor.py` for custom embeddings
3. Adding new models in `training_scripts.py`

## 🎯 Next Steps

After successful setup:

1. **Test the API**: Use the provided endpoints to search and query your papers
2. **Customize Models**: Fine-tune models based on your specific domain
3. **Add More Papers**: Use the batch processing API to add more papers
4. **Monitor Performance**: Check the generated reports for insights
5. **Integrate with Frontend**: Connect the API with your React frontend

## 📞 Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all dependencies are installed
3. Ensure sufficient disk space and memory
4. Check file permissions

The system is designed to be robust and handle various PDF formats, but some complex PDFs might require manual preprocessing.
