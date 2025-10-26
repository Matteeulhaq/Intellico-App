"""
Advanced Training Scripts for Research Paper Models
Includes fine-tuning, custom model training, and evaluation
"""

import os
import json
import torch
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from transformers import (
    AutoTokenizer, AutoModel, 
    TrainingArguments, Trainer,
    AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering,
    AutoModelForCausalLM
)
from datasets import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchPaperTrainer:
    def __init__(self, storage_path: str = "/app/storage"):
        self.storage_path = storage_path
        self.research_papers_path = os.path.join(storage_path, "research_papers")
        self.processed_path = os.path.join(self.research_papers_path, "processed")
        self.models_path = os.path.join(self.research_papers_path, "trained_models")
        
        # Create models directory
        os.makedirs(self.models_path, exist_ok=True)
        
        # Model configurations
        self.model_configs = {
            "classification": {
                "model_name": "bert-base-uncased",
                "num_labels": 7,  # Common research paper sections
                "max_length": 512
            },
            "summarization": {
                "model_name": "facebook/bart-large-cnn",
                "max_length": 1024,
                "summary_length": 150
            },
            "question_answering": {
                "model_name": "distilbert-base-cased-distilled-squad",
                "max_length": 512
            }
        }
    
    def prepare_classification_data(self) -> Tuple[List[str], List[str]]:
        """
        Prepare data for section classification training
        """
        texts = []
        labels = []
        
        # Load all processed papers
        processed_files = [f for f in os.listdir(self.processed_path) 
                          if f.endswith('_processed.json')]
        
        section_mapping = {
            "abstract": 0,
            "introduction": 1,
            "methodology": 2,
            "results": 3,
            "discussion": 4,
            "conclusion": 5,
            "references": 6
        }
        
        for file in processed_files:
            file_path = os.path.join(self.processed_path, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    paper_data = json.load(f)
                
                # Extract sections
                sections = paper_data.get("sections", {})
                for section_name, section_text in sections.items():
                    if section_text.strip() and section_name in section_mapping:
                        texts.append(section_text)
                        labels.append(section_mapping[section_name])
                
            except Exception as e:
                logger.error(f"Error processing {file}: {str(e)}")
        
        return texts, labels
    
    def prepare_summarization_data(self) -> Tuple[List[str], List[str]]:
        """
        Prepare data for text summarization training
        """
        texts = []
        summaries = []
        
        processed_files = [f for f in os.listdir(self.processed_path) 
                          if f.endswith('_processed.json')]
        
        for file in processed_files:
            file_path = os.path.join(self.processed_path, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    paper_data = json.load(f)
                
                full_text = paper_data.get("full_text", "")
                abstract = paper_data.get("sections", {}).get("abstract", "")
                
                if full_text and abstract and len(full_text) > 500:
                    # Truncate text if too long
                    if len(full_text) > 4000:
                        full_text = full_text[:4000]
                    
                    texts.append(full_text)
                    summaries.append(abstract)
                
            except Exception as e:
                logger.error(f"Error processing {file}: {str(e)}")
        
        return texts, summaries
    
    def prepare_qa_data(self) -> List[Dict]:
        """
        Prepare data for question-answering training
        """
        qa_data = []
        
        processed_files = [f for f in os.listdir(self.processed_path) 
                          if f.endswith('_processed.json')]
        
        for file in processed_files:
            file_path = os.path.join(self.processed_path, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    paper_data = json.load(f)
                
                paper_id = paper_data.get("paper_id", "")
                sections = paper_data.get("sections", {})
                
                # Create QA pairs based on sections
                for section_name, section_text in sections.items():
                    if section_text.strip() and len(section_text) > 100:
                        # Generate questions based on section type
                        if section_name == "abstract":
                            question = f"What is the main contribution of this research paper {paper_id}?"
                        elif section_name == "methodology":
                            question = f"What methodology was used in {paper_id}?"
                        elif section_name == "results":
                            question = f"What are the main results in {paper_id}?"
                        else:
                            question = f"What does the {section_name} section say in {paper_id}?"
                        
                        qa_data.append({
                            "question": question,
                            "context": section_text,
                            "answer": section_text[:200] + "...",  # Truncated answer
                            "paper_id": paper_id,
                            "section": section_name
                        })
                
            except Exception as e:
                logger.error(f"Error processing {file}: {str(e)}")
        
        return qa_data
    
    def train_classification_model(self) -> Dict[str, any]:
        """
        Train a BERT-based classification model for section classification
        """
        logger.info("Training classification model...")
        
        # Prepare data
        texts, labels = self.prepare_classification_data()
        
        if len(texts) < 10:
            return {"error": "Insufficient data for training"}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Load tokenizer and model
        model_name = self.model_configs["classification"]["model_name"]
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, 
            num_labels=self.model_configs["classification"]["num_labels"]
        )
        
        # Tokenize data
        def tokenize_function(examples):
            return tokenizer(
                examples["text"], 
                truncation=True, 
                padding=True, 
                max_length=512
            )
        
        # Create datasets
        train_dataset = Dataset.from_dict({"text": X_train, "labels": y_train})
        test_dataset = Dataset.from_dict({"text": X_test, "labels": y_test})
        
        train_dataset = train_dataset.map(tokenize_function, batched=True)
        test_dataset = test_dataset.map(tokenize_function, batched=True)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=os.path.join(self.models_path, "classification"),
            num_train_epochs=3,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir=os.path.join(self.models_path, "logs"),
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=test_dataset,
            tokenizer=tokenizer,
        )
        
        # Train model
        trainer.train()
        
        # Evaluate
        predictions = trainer.predict(test_dataset)
        y_pred = np.argmax(predictions.predictions, axis=1)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Save model
        model_path = os.path.join(self.models_path, "classification")
        trainer.save_model(model_path)
        tokenizer.save_pretrained(model_path)
        
        # Generate report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        result = {
            "model_type": "classification",
            "accuracy": accuracy,
            "classification_report": report,
            "model_path": model_path,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "trained_at": datetime.now().isoformat()
        }
        
        # Save training results
        results_path = os.path.join(self.models_path, "classification_results.json")
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Classification model trained with accuracy: {accuracy:.3f}")
        return result
    
    def train_summarization_model(self) -> Dict[str, any]:
        """
        Train a BART-based summarization model
        """
        logger.info("Training summarization model...")
        
        # Prepare data
        texts, summaries = self.prepare_summarization_data()
        
        if len(texts) < 5:
            return {"error": "Insufficient data for training"}
        
        # For now, we'll use a pre-trained model and fine-tune it
        # This is a simplified version - full implementation would require more complex setup
        
        model_name = self.model_configs["summarization"]["model_name"]
        
        # Load pre-trained model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Save model (in a real scenario, you would fine-tune it)
        model_path = os.path.join(self.models_path, "summarization")
        model.save_pretrained(model_path)
        tokenizer.save_pretrained(model_path)
        
        result = {
            "model_type": "summarization",
            "model_path": model_path,
            "training_samples": len(texts),
            "trained_at": datetime.now().isoformat(),
            "status": "pre_trained_model_saved"
        }
        
        # Save results
        results_path = os.path.join(self.models_path, "summarization_results.json")
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info("Summarization model setup completed")
        return result
    
    def train_qa_model(self) -> Dict[str, any]:
        """
        Train a question-answering model
        """
        logger.info("Training QA model...")
        
        # Prepare data
        qa_data = self.prepare_qa_data()
        
        if len(qa_data) < 10:
            return {"error": "Insufficient data for training"}
        
        # Use pre-trained model for now
        model_name = self.model_configs["question_answering"]["model_name"]
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForQuestionAnswering.from_pretrained(model_name)
        
        # Save model
        model_path = os.path.join(self.models_path, "question_answering")
        model.save_pretrained(model_path)
        tokenizer.save_pretrained(model_path)
        
        result = {
            "model_type": "question_answering",
            "model_path": model_path,
            "training_samples": len(qa_data),
            "trained_at": datetime.now().isoformat(),
            "status": "pre_trained_model_saved"
        }
        
        # Save results
        results_path = os.path.join(self.models_path, "qa_results.json")
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info("QA model setup completed")
        return result
    
    def train_all_models(self) -> Dict[str, any]:
        """
        Train all available models
        """
        logger.info("Starting training of all models...")
        
        results = {
            "training_started": datetime.now().isoformat(),
            "models": {}
        }
        
        # Train classification model
        try:
            results["models"]["classification"] = self.train_classification_model()
        except Exception as e:
            results["models"]["classification"] = {"error": str(e)}
        
        # Train summarization model
        try:
            results["models"]["summarization"] = self.train_summarization_model()
        except Exception as e:
            results["models"]["summarization"] = {"error": str(e)}
        
        # Train QA model
        try:
            results["models"]["question_answering"] = self.train_qa_model()
        except Exception as e:
            results["models"]["question_answering"] = {"error": str(e)}
        
        results["training_completed"] = datetime.now().isoformat()
        
        # Save overall results
        results_path = os.path.join(self.models_path, "all_models_results.json")
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info("All models training completed")
        return results
    
    def evaluate_model(self, model_type: str, test_data: List[Dict]) -> Dict[str, any]:
        """
        Evaluate a trained model
        """
        model_path = os.path.join(self.models_path, model_type)
        
        if not os.path.exists(model_path):
            return {"error": f"Model {model_type} not found"}
        
        # Load model and tokenizer
        if model_type == "classification":
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSequenceClassification.from_pretrained(model_path)
            
            # Evaluation logic for classification
            # This would include running inference on test data
            
        elif model_type == "summarization":
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(model_path)
            
        elif model_type == "question_answering":
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForQuestionAnswering.from_pretrained(model_path)
        
        return {
            "model_type": model_type,
            "evaluation_completed": datetime.now().isoformat(),
            "status": "evaluation_placeholder"
        }

# Example usage
if __name__ == "__main__":
    trainer = ResearchPaperTrainer()
    # Example: trainer.train_all_models()
