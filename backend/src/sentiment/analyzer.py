"""
Sentiment analysis using FinBERT or similar financial NLP model.
Analyzes news articles for sentiment towards stocks.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from ..core.config import settings
from ..core.logging import get_logger
from ..models.database import News, Stock, SentimentScore


logger = get_logger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analyzer using FinBERT for financial text.
    
    Analyzes news articles and assigns sentiment scores.
    """
    
    def __init__(self):
        """Initialize sentiment analyzer with FinBERT model."""
        self.logger = get_logger(self.__class__.__name__)
        self.model_name = settings.SENTIMENT_MODEL
        self.confidence_threshold = settings.SENTIMENT_CONFIDENCE_THRESHOLD
        
        # Lazy load model (only when needed)
        self._tokenizer = None
        self._model = None
        self._device = None
    
    def load_model(self) -> None:
        """Load FinBERT model and tokenizer."""
        if self._model is not None:
            return  # Already loaded
        
        self.logger.info(f"Loading sentiment model: {self.model_name}")
        
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Use GPU if available
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._model.to(self._device)
            self._model.eval()
            
            self.logger.info(f"Model loaded successfully on device: {self._device}")
        
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment label, score, and confidence
        """
        # Load model if not loaded
        if self._model is None:
            self.load_model()
        
        # Tokenize
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self._device)
        
        # Get predictions
        with torch.no_grad():
            outputs = self._model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # FinBERT outputs: [negative, neutral, positive]
        probabilities = predictions[0].cpu().numpy()
        
        # Determine sentiment
        labels = ["negative", "neutral", "positive"]
        max_prob_idx = probabilities.argmax()
        sentiment_label = labels[max_prob_idx]
        confidence = float(probabilities[max_prob_idx])
        
        # Compute sentiment score (-1 to +1)
        # negative=-1, neutral=0, positive=+1, weighted by confidence
        sentiment_score = (probabilities[2] - probabilities[0])  # positive - negative
        
        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": float(sentiment_score),
            "confidence": confidence,
            "probabilities": {
                "negative": float(probabilities[0]),
                "neutral": float(probabilities[1]),
                "positive": float(probabilities[2])
            }
        }
    
    def analyze_news_article(
        self,
        news: News,
        stock: Stock,
        db: Session
    ) -> Optional[SentimentScore]:
        """
        Analyze sentiment of a news article for a specific stock.
        
        Args:
            news: News article
            stock: Stock entity
            db: Database session
            
        Returns:
            SentimentScore record or None if analysis fails
        """
        try:
            # Use title and summary for sentiment analysis
            text = f"{news.title}. {news.summary or ''}"
            
            # Analyze
            result = self.analyze_text(text)
            
            # Only store if confidence meets threshold
            if result["confidence"] < self.confidence_threshold:
                self.logger.warning(
                    f"Low confidence ({result['confidence']:.2f}) for article: {news.title[:50]}"
                )
                # Still store but flag low confidence
            
            # Create sentiment score record
            sentiment_score = SentimentScore(
                news_id=news.id,
                stock_id=stock.id,
                sentiment_label=result["sentiment_label"],
                sentiment_score=result["sentiment_score"],
                confidence=result["confidence"],
                model_name=self.model_name,
                model_version="1.0"
            )
            
            db.add(sentiment_score)
            db.commit()
            
            self.logger.info(
                f"Analyzed sentiment for {stock.symbol}: {result['sentiment_label']} "
                f"(score={result['sentiment_score']:.2f}, conf={result['confidence']:.2f})"
            )
            
            return sentiment_score
        
        except Exception as e:
            self.logger.error(f"Failed to analyze sentiment: {e}")
            db.rollback()
            return None
    
    def analyze_pending_news(self, db: Session, limit: int = 100) -> Dict[str, int]:
        """
        Analyze sentiment for news articles without sentiment scores.
        
        Args:
            db: Database session
            limit: Maximum number of articles to process
            
        Returns:
            Dictionary with processing metrics
        """
        metrics = {
            "processed": 0,
            "skipped": 0,
            "errors": 0
        }
        
        # Find news without sentiment scores
        from sqlalchemy.orm import aliased
        from ..models.database import NewsStock
        
        # Query news that don't have sentiment scores yet
        subquery = db.query(SentimentScore.news_id).distinct()
        
        news_items = db.query(News).filter(
            ~News.id.in_(subquery)
        ).order_by(News.published_at.desc()).limit(limit).all()
        
        self.logger.info(f"Found {len(news_items)} news articles to analyze")
        
        for news in news_items:
            try:
                # Get associated stocks
                news_stocks = db.query(NewsStock).filter(
                    NewsStock.news_id == news.id
                ).all()
                
                if not news_stocks:
                    metrics["skipped"] += 1
                    continue
                
                # Analyze sentiment for each associated stock
                for news_stock in news_stocks:
                    stock = db.query(Stock).get(news_stock.stock_id)
                    if stock:
                        self.analyze_news_article(news, stock, db)
                        metrics["processed"] += 1
            
            except Exception as e:
                self.logger.error(f"Error processing news {news.id}: {e}")
                metrics["errors"] += 1
        
        return metrics
    
    def aggregate_sentiment_score(
        self,
        stock_id: int,
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Aggregate sentiment scores for a stock over a time period.
        
        Args:
            stock_id: Stock ID
            db: Database session
            days: Number of days to look back
            
        Returns:
            Aggregated sentiment data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recent sentiment scores
        scores = db.query(SentimentScore).filter(
            SentimentScore.stock_id == stock_id,
            SentimentScore.created_at >= cutoff_date
        ).all()
        
        if not scores:
            return {
                "average_score": 0,
                "score_0_100": 50,  # Neutral
                "count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            }
        
        # Count by sentiment
        label_counts = {
            "positive": len([s for s in scores if s.sentiment_label == "positive"]),
            "negative": len([s for s in scores if s.sentiment_label == "negative"]),
            "neutral": len([s for s in scores if s.sentiment_label == "neutral"])
        }
        
        # Average sentiment score (-1 to +1)
        avg_score = sum(s.sentiment_score for s in scores) / len(scores)
        
        # Convert to 0-100 scale
        # -1 -> 0, 0 -> 50, +1 -> 100
        score_0_100 = (avg_score + 1) * 50
        
        return {
            "average_score": round(avg_score, 3),
            "score_0_100": round(score_0_100, 2),
            "count": len(scores),
            "positive_count": label_counts["positive"],
            "negative_count": label_counts["negative"],
            "neutral_count": label_counts["neutral"],
            "period_days": days
        }
