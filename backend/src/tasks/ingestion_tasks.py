"""
Celery tasks for data ingestion.
"""
from celery import shared_task

from ..core.database import get_db_context
from ..core.logging import get_logger
from ..ingestion.fundamental_ingestor import FundamentalIngestor
from ..ingestion.news_ingestor import NewsIngestor
from ..sentiment.analyzer import SentimentAnalyzer

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3)
def ingest_fundamental_data(self):
    """
    Celery task to ingest fundamental stock data.
    
    Runs daily after market close.
    """
    logger.info("Starting fundamental data ingestion task")
    
    try:
        ingestor = FundamentalIngestor(source="yfinance")
        result = ingestor.run()
        
        logger.info(f"Fundamental ingestion completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Fundamental ingestion failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def ingest_news_data(self):
    """
    Celery task to ingest news articles.
    
    Runs every few hours.
    """
    logger.info("Starting news data ingestion task")
    
    try:
        ingestor = NewsIngestor(source="newsapi")
        result = ingestor.run()
        
        logger.info(f"News ingestion completed: {result}")
        
        # Trigger sentiment analysis for new articles
        if result.get("status") == "success":
            analyze_pending_sentiment.delay()
        
        return result
    
    except Exception as e:
        logger.error(f"News ingestion failed: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=2)
def analyze_pending_sentiment(self):
    """
    Celery task to analyze sentiment for news without sentiment scores.
    
    Runs after news ingestion.
    """
    logger.info("Starting sentiment analysis task")
    
    try:
        analyzer = SentimentAnalyzer()
        
        with get_db_context() as db:
            result = analyzer.analyze_pending_news(db=db, limit=100)
        
        logger.info(f"Sentiment analysis completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))


@shared_task
def ingest_fundamental_for_symbol(symbol: str):
    """
    Ingest fundamental data for a single stock symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Ingestion result
    """
    logger.info(f"Ingesting fundamental data for {symbol}")
    
    try:
        from ..core.config import settings
        # Temporarily override tracked stocks
        original_stocks = settings.TRACKED_STOCKS
        settings.TRACKED_STOCKS = [symbol]
        
        ingestor = FundamentalIngestor(source="yfinance")
        result = ingestor.run()
        
        # Restore original stocks
        settings.TRACKED_STOCKS = original_stocks
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to ingest fundamental data for {symbol}: {e}")
        raise
