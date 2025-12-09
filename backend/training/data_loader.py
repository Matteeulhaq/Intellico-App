"""
Data loader for training datasets
Converts datasets to instruction format for fine-tuning
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datasets import Dataset

class TrainingDataLoader:
    """Load and preprocess training datasets"""
    
    def __init__(self, training_data_dir: str, processed_papers_dir: str = None):
        self.training_data_dir = Path(training_data_dir)
        self.processed_papers_dir = Path(processed_papers_dir) if processed_papers_dir else None
    
    def load_summarization_dataset(self) -> List[Dict[str, Any]]:
        """Load summarization dataset and convert to instruction format"""
        file_path = self.training_data_dir / "summarization_dataset.json"
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        examples = []
        for item in data.get('data', []):
            instruction = "Summarize the following research paper text:"
            examples.append({
                'instruction': instruction,
                'input': item['text'],
                'output': item['summary'],
                'paper_id': item.get('paper_id', ''),
                'task': 'summarization'
            })
        
        return examples
    
    def load_classification_dataset(self) -> List[Dict[str, Any]]:
        """Load classification dataset and convert to instruction format"""
        file_path = self.training_data_dir / "classification_dataset.json"
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        examples = []
        for item in data.get('data', []):
            instruction = "Classify the following text section from a research paper. Choose from: abstract, introduction, methodology, results, discussion, conclusion, references."
            examples.append({
                'instruction': instruction,
                'input': item['text'],
                'output': item['label'],
                'paper_id': item.get('paper_id', ''),
                'task': 'classification'
            })
        
        return examples
    
    def load_metadata_dataset(self) -> List[Dict[str, Any]]:
        """Load metadata extraction dataset and convert to instruction format"""
        file_path = self.training_data_dir / "metadata_extraction_dataset.json"
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        examples = []
        for item in data.get('data', []):
            instruction = "Extract metadata from the following research paper text. Return a JSON object with: title, authors, abstract, keywords, publication_date."
            # Assuming item has metadata field or we need to extract it
            metadata = item.get('metadata', {})
            examples.append({
                'instruction': instruction,
                'input': item.get('text', ''),
                'output': json.dumps(metadata) if isinstance(metadata, dict) else str(metadata),
                'paper_id': item.get('paper_id', ''),
                'task': 'metadata_extraction'
            })
        
        return examples
    
    def load_keyword_dataset(self) -> List[Dict[str, Any]]:
        """Load keyword extraction dataset and convert to instruction format"""
        file_path = self.training_data_dir / "keyword_extraction_dataset.json"
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        examples = []
        for item in data.get('data', []):
            instruction = "Extract key terms and keywords from the following research paper text. Return a comma-separated list of keywords."
            keywords = item.get('keywords', [])
            if isinstance(keywords, list):
                output = ', '.join(keywords)
            else:
                output = str(keywords)
            
            examples.append({
                'instruction': instruction,
                'input': item.get('text', ''),
                'output': output,
                'paper_id': item.get('paper_id', ''),
                'task': 'keyword_extraction'
            })
        
        return examples
    
    def format_instruction(self, example: Dict[str, Any]) -> str:
        """Format example as instruction-following prompt"""
        # Format for Qwen (ChatML format)
        if example['task'] == 'classification':
            prompt = f"""<|im_start|>user
{example['instruction']}

Text: {example['input']}<|im_end|>
<|im_start|>assistant
{example['output']}<|im_end|>"""
        else:
            prompt = f"""<|im_start|>user
{example['instruction']}

{example['input']}<|im_end|>
<|im_start|>assistant
{example['output']}<|im_end|>"""
        
        return prompt
    
    def load_all_datasets(self) -> Dataset:
        """Load all datasets and combine into single dataset"""
        all_examples = []
        
        # Load from training datasets
        all_examples.extend(self.load_summarization_dataset())
        all_examples.extend(self.load_classification_dataset())
        all_examples.extend(self.load_metadata_dataset())
        all_examples.extend(self.load_keyword_dataset())
        
        # Format as instruction-following prompts
        formatted_data = []
        for example in all_examples:
            formatted_data.append({
                'text': self.format_instruction(example),
                'task': example['task'],
                'paper_id': example.get('paper_id', '')
            })
        
        # Convert to HuggingFace Dataset
        dataset = Dataset.from_list(formatted_data)
        return dataset
    
    def train_test_split(self, dataset: Dataset, test_size: float = 0.1):
        """Split dataset into train and test sets"""
        return dataset.train_test_split(test_size=test_size)

