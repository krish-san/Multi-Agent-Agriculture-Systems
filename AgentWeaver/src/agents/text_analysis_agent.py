
from typing import Dict, Any, List
import logging
from datetime import datetime

from .base_agent import BaseWorkerAgent
from ..core.models import AgentCapability, Task, TaskStatus


logger = logging.getLogger(__name__)


class TextAnalysisAgent(BaseWorkerAgent):
    
    def __init__(self, name: str = "TextAnalyzer"):
        capabilities = [AgentCapability.ANALYSIS, AgentCapability.DATA_PROCESSING]
        super().__init__(name, capabilities, "text_analyzer")
        
        # Agent-specific configuration
        self.max_summary_length = 500  # Maximum length for summaries
        self.min_text_length = 50      # Minimum text length to process
        
        self.logger.info(f"Text Analysis Agent '{name}' initialized")
    
    def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = datetime.utcnow()
        
        try:
            # Extract text content from task parameters
            text_content = task.parameters.get('text', '')
            analysis_type = task.parameters.get('analysis_type', 'summarize')
            
            if not text_content:
                # Try to get text from context
                text_content = context.get('text', '')
            
            if not text_content:
                raise ValueError("No text content provided for analysis")
            
            if len(text_content.strip()) < self.min_text_length:
                raise ValueError(f"Text too short for analysis (minimum {self.min_text_length} characters)")
            
            self.logger.info(f"Processing {analysis_type} task for {len(text_content)} characters of text")
            
            # Perform the requested analysis
            if analysis_type == 'summarize':
                result = self._summarize_text(text_content, task.parameters)
            elif analysis_type == 'extract_keywords':
                result = self._extract_keywords(text_content, task.parameters)
            elif analysis_type == 'analyze_sentiment':
                result = self._analyze_sentiment(text_content, task.parameters)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Prepare the final result
            final_result = {
                'analysis_type': analysis_type,
                'original_text_length': len(text_content),
                'result': result,
                'execution_time': execution_time,
                'agent_id': self.agent_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Text analysis completed in {execution_time:.2f}s")
            return final_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Text analysis failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'error': error_msg,
                'execution_time': execution_time,
                'agent_id': self.agent_id,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _summarize_text(self, text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Get target summary length from parameters
        target_length = parameters.get('summary_length', self.max_summary_length)
        
        # Simple extractive summarization algorithm
        # In a real implementation, you'd use a language model here
        sentences = self._split_into_sentences(text)
        
        if len(sentences) <= 3:
            # If text is already short, return it as is
            summary = text.strip()
        else:
            # Score sentences based on position and length
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                # Simple scoring: prefer sentences in the beginning and middle
                position_score = 1.0 if i < len(sentences) * 0.3 else 0.7
                length_score = min(len(sentence) / 100, 1.0)  # Prefer longer sentences
                
                total_score = position_score * length_score
                scored_sentences.append((sentence, total_score))
            
            # Sort by score and take top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            
            # Build summary up to target length
            summary_parts = []
            current_length = 0
            
            for sentence, score in scored_sentences:
                if current_length + len(sentence) <= target_length:
                    summary_parts.append(sentence)
                    current_length += len(sentence)
                else:
                    break
            
            # Reorder sentences to maintain original order
            summary_sentences = []
            for sentence in sentences:
                if sentence in summary_parts:
                    summary_sentences.append(sentence)
            
            summary = ' '.join(summary_sentences)
        
        return {
            'summary': summary,
            'original_sentences': len(sentences),
            'summary_length': len(summary),
            'compression_ratio': len(summary) / len(text) if text else 0
        }
    
    def _extract_keywords(self, text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        max_keywords = parameters.get('max_keywords', 10)
        
        # Simple keyword extraction based on word frequency
        import re
        from collections import Counter
        
        # Clean and tokenize text
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'this', 'that', 'these', 'those', 'will', 'would', 'could', 'should'
        }
        
        filtered_words = [word for word in words if word not in stop_words]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Get top keywords
        keywords = [word for word, count in word_counts.most_common(max_keywords)]
        
        return {
            'keywords': keywords,
            'word_frequencies': dict(word_counts.most_common(max_keywords)),
            'total_words': len(words),
            'unique_words': len(word_counts)
        }
    
    def _analyze_sentiment(self, text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Simple rule-based sentiment analysis
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'happy', 'pleased', 'satisfied', 'perfect',
            'awesome', 'brilliant', 'outstanding', 'superb'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike',
            'angry', 'disappointed', 'frustrated', 'annoyed', 'poor',
            'worst', 'disgusting', 'pathetic', 'useless'
        }
        
        words = text.lower().split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            sentiment = 'neutral'
            confidence = 0.5
        elif positive_count > negative_count:
            sentiment = 'positive'
            confidence = positive_count / total_sentiment_words
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = negative_count / total_sentiment_words
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_words_found': positive_count,
            'negative_words_found': negative_count,
            'total_words': len(words)
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        import re
        
        # Simple sentence splitting based on punctuation
        sentences = re.split(r'[.!?]+', text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def can_handle_task(self, task: Task) -> bool:
        # Check if it's a text analysis task
        if task.task_type == 'text_analysis':
            return True
        
        # Check if the task has text content to analyze
        if 'text' in task.parameters or task.parameters.get('analysis_type') in ['summarize', 'extract_keywords', 'analyze_sentiment']:
            return True
        
        # Fall back to base capability checking
        return super().can_handle_task(task)
    
    def health_check(self) -> bool:
        try:
            # Basic health check from parent
            if not super().health_check():
                return False
            
            # Test basic text processing capability
            test_text = "This is a simple test sentence."
            test_result = self._split_into_sentences(test_text)
            
            if not test_result or len(test_result) != 1:
                self.set_error("Text processing capability test failed")
                return False
            
            self.logger.debug(f"Text Analysis Agent {self.name} health check passed")
            return True
            
        except Exception as e:
            self.set_error(f"Health check failed: {str(e)}")
            return False
