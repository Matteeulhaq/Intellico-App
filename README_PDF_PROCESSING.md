# PDF to Training Data Converter

## 🎯 Overview

This single file solution (`pdf_to_training_data.py`) converts your 41 research papers into training-ready metadata for machine learning models.

## 📋 What You Get

The script creates:
- **Individual processed papers** (JSON format with extracted text and metadata)
- **Training datasets** (ready for ML model training)
- **Comprehensive metadata** (authors, titles, keywords, sections)

## 🚀 Quick Start

### Option 1: With PDF Libraries (Recommended)

1. **Install PDF processing libraries:**
   ```bash
   pip3 install PyMuPDF pdfplumber pypdf2
   ```

2. **Run the converter:**
   ```bash
   python3 pdf_to_training_data.py /home/mattee/Intellico-App/research_papers/raw_pdfs ./training_data
   ```

### Option 2: Using Docker (No Installation Required)

1. **Create a Dockerfile for PDF processing:**
   ```bash
   cat > Dockerfile.pdf << 'EOF'
   FROM python:3.11-slim
   RUN pip install PyMuPDF pdfplumber pypdf2
   COPY pdf_to_training_data.py /app/
   WORKDIR /app
   CMD ["python", "pdf_to_training_data.py", "/data/input", "/data/output"]
   EOF
   ```

2. **Run with Docker:**
   ```bash
   docker build -f Dockerfile.pdf -t pdf-processor .
   docker run -v /home/mattee/Intellico-App/research_papers/raw_pdfs:/data/input -v $(pwd)/training_data:/data/output pdf-processor
   ```

### Option 3: Manual Installation

If you prefer to install libraries manually:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip

# Install PDF libraries
pip3 install --user PyMuPDF pdfplumber pypdf2

# Run the script
python3 pdf_to_training_data.py /home/mattee/Intellico-App/research_papers/raw_pdfs ./training_data
```

## 📊 Output Structure

After running, you'll get:

```
training_data/
├── processed_papers/          # Individual processed papers
│   ├── paper1_processed.json
│   ├── paper2_processed.json
│   └── ...
├── training_datasets/         # Ready-to-use training datasets
│   ├── classification_dataset.json
│   ├── summarization_dataset.json
│   ├── keyword_extraction_dataset.json
│   └── metadata_extraction_dataset.json
└── metadata/                  # Processing reports
    └── processing_summary.json
```

## 🔧 What the Script Does

### 1. **PDF Text Extraction**
- Extracts text from all 41 PDFs
- Handles various PDF formats and structures
- Cleans and preprocesses text

### 2. **Section Detection**
- **Enhanced section extraction** with improved regex patterns
- Automatically identifies:
  - **Abstract** - Multiple pattern matching for better detection
  - **Introduction** - Including Background and Overview variations
  - **Methodology** - Methods, Approach, Materials and Methods
  - **Results** - Findings, Outcomes, Data, Experimental Results
  - **Discussion** - Analysis, Interpretation, Implications
  - **Conclusion** - Summary, Final Remarks, Concluding Remarks
  - **References** - Bibliography, Citations
- **Consistent heading normalization** - Maps variations to standard section names
- **Robust pattern matching** - Handles various PDF formatting styles

### 3. **Metadata Extraction**
- Paper titles
- Authors
- Publication years
- Journal names
- Keywords
- Word counts

### 4. **Training Dataset Creation**
- **Classification Dataset**: For section identification
- **Summarization Dataset**: Full text to abstract mapping
- **Keyword Extraction Dataset**: Text to keywords mapping
- **Metadata Extraction Dataset**: Text to metadata mapping

## 📈 Expected Results

With proper PDF libraries installed, you should see:
- ✅ 41 successfully processed papers
- 📝 Thousands of words extracted
- 📊 Multiple training datasets created
- 🏷️ Rich metadata for each paper
- 📑 **All major sections extracted** (Abstract, Introduction, Methods, Results, Discussion, Conclusion, References)
- 🎯 **Improved section detection** with consistent heading normalization

## 🛠️ Troubleshooting

### Issue: "PDF processing libraries not available"
**Solution**: Install the required libraries:
```bash
pip3 install PyMuPDF pdfplumber pypdf2
```

### Issue: Permission denied
**Solution**: Use user installation:
```bash
pip3 install --user PyMuPDF pdfplumber pypdf2
```

### Issue: Network timeout during installation
**Solution**: Use alternative package sources:
```bash
pip3 install -i https://pypi.org/simple/ PyMuPDF pdfplumber pypdf2
```

## 🎯 Next Steps

After successful processing:

1. **Check the results:**
   ```bash
   ls -la training_data/processed_papers/
   cat training_data/metadata/processing_summary.json
   ```

2. **Use the training datasets:**
   - Load the JSON files into your ML framework
   - Use the classification dataset for section identification
   - Use the summarization dataset for text summarization models

3. **Customize the extraction:**
   - Modify section detection patterns in `_extract_common_sections()` method
   - Add custom metadata extraction rules in `extract_metadata()` method
   - Adjust text cleaning parameters in `clean_text()` method
   - Customize heading normalization in `_normalize_heading()` method

## 📝 Example Usage

```python
import json

# Load a processed paper
with open('training_data/processed_papers/paper1_processed.json', 'r') as f:
    paper = json.load(f)

print(f"Title: {paper['metadata']['title']}")
print(f"Authors: {paper['metadata']['authors']}")
print(f"Word Count: {paper['word_count']}")
print(f"Sections: {list(paper['sections'].keys())}")

# Load training dataset
with open('training_data/training_datasets/classification_dataset.json', 'r') as f:
    dataset = json.load(f)

print(f"Classification samples: {len(dataset['data'])}")
```

## 🎉 Success!

Once you see the processing summary with actual word counts (not just 10 words per paper), you'll have successfully converted your 41 research papers into training-ready metadata!

### ✨ Recent Improvements

- **Enhanced Section Extraction**: Improved regex patterns that better capture Abstract, Introduction, Methods, Results, Discussion, Conclusion, and References sections
- **Consistent Heading Normalization**: All section variations are mapped to standard names (e.g., "Summary" → "Abstract", "Methods" → "Methodology")
- **Robust Pattern Matching**: Multiple fallback patterns for each section type to handle various PDF formatting styles
- **Better Text Processing**: Improved text cleaning and section boundary detection

The script is designed to be robust and handle various PDF formats, but some complex PDFs might require manual preprocessing or different extraction methods.

