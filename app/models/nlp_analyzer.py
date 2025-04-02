from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPAnalyzer:
    def __init__(self):
        """Initialize NLP models for task analysis"""
        logger.info("Initializing NLP models...")
        
        # Sentiment analysis
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        # Text classification for task type
        self.task_classifier = pipeline(
            "text-classification",
            model="facebook/bart-large-mnli"
        )
        
        # Named entity recognition
        self.ner_pipeline = pipeline(
            "ner",
            model="dbmdz/bert-large-cased-finetuned-conll03-english"
        )
        
        # Text summarization
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )
        
        # Keyword extraction
        self.keyword_extractor = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        logger.info("NLP models initialized successfully")
    
    def analyze_task(self, text: str) -> Dict[str, float]:
        """
        Analyze task description using multiple NLP models
        
        Returns a dictionary of metrics
        """
        metrics = {}
        
        # Sentiment analysis
        sentiment_result = self.sentiment_analyzer(text)[0]
        metrics["sentiment_score"] = float(sentiment_result["score"])
        metrics["sentiment_label"] = sentiment_result["label"]
        
        # Task complexity (based on length and structure)
        metrics["complexity"] = self._calculate_complexity(text)
        
        # Task type classification
        task_type = self._classify_task_type(text)
        metrics["task_type"] = task_type
        
        # Entity count (people, organizations, etc.)
        entities = self.ner_pipeline(text)
        metrics["entity_count"] = len(entities)
        
        # Keyword importance
        keywords = self._extract_keywords(text)
        metrics["keyword_count"] = len(keywords)
        
        # Time estimation factor (based on complexity and keywords)
        metrics["time_estimation_factor"] = self._estimate_time_factor(metrics)
        
        return metrics
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate task complexity based on text features"""
        # Simple complexity score based on length, sentence count, and vocabulary
        sentences = text.split('.')
        words = text.split()
        unique_words = len(set(words))
        
        # Normalize complexity score between 0 and 1
        complexity = min(1.0, (len(words) / 100) * 0.3 + 
                                (len(sentences) / 10) * 0.3 + 
                                (unique_words / len(words)) * 0.4)
        
        return complexity
    
    def _classify_task_type(self, text: str) -> str:
        """Classify the type of task"""
        candidate_labels = [
            "development", "design", "research", "documentation", 
            "testing", "deployment", "meeting", "planning"
        ]
        
        result = self.task_classifier(
            text, 
            candidate_labels=candidate_labels,
            hypothesis_template="This task is about {}."
        )
        
        return result["labels"][0]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from the text"""
        # Use zero-shot classification to identify important concepts
        candidate_labels = [
            "urgent", "important", "complex", "simple", "technical",
            "creative", "collaborative", "independent", "high-priority",
            "low-priority", "time-sensitive", "resource-intensive"
        ]
        
        result = self.keyword_extractor(
            text,
            candidate_labels=candidate_labels,
            multi_label=True
        )
        
        # Return labels with confidence > 0.5
        return [label for label, score in zip(result["labels"], result["scores"]) if score > 0.5]
    
    def _estimate_time_factor(self, metrics: Dict[str, Any]) -> float:
        """Estimate a time factor based on task metrics"""
        # Combine various metrics to estimate time factor
        complexity_factor = metrics["complexity"] * 2.0  # 0-2 range
        entity_factor = min(1.0, metrics["entity_count"] / 5)  # 0-1 range
        keyword_factor = min(1.0, metrics["keyword_count"] / 3)  # 0-1 range
        
        # Calculate weighted average
        time_factor = (complexity_factor * 0.5) + (entity_factor * 0.3) + (keyword_factor * 0.2)
        
        return time_factor
    
    def summarize_text(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
        """Generate a summary of the text"""
        if len(text.split()) < 50:
            return text  # Text too short to summarize
        
        summary = self.summarizer(
            text, 
            max_length=max_length, 
            min_length=min_length,
            do_sample=False
        )
        
        return summary[0]["summary_text"]
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from the text"""
        entities = self.ner_pipeline(text)
        return [{"text": e["word"], "type": e["entity"], "score": e["score"]} for e in entities] 