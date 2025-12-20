"""
News ingestor for stock-related news articles.
Fetches news from configured sources and associates with relevant stocks.
"""
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from .base import BaseIngestor
from ..core.config import settings
from ..models.database import Stock, News, NewsStock


class NewsIngestor(BaseIngestor):
    """Ingestor for stock-related news."""
    
    def __init__(self, source: str = "newsapi"):
        """
        Initialize news ingestor.
        
        Args:
            source: News source identifier
        """
        super().__init__(source=source, ingestion_type="news")
        self.api_url = settings.NEWS_API_BASE_URL
        self.api_key = settings.NEWS_API_KEY
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetch news articles related to tracked stocks.
        
        Returns:
            List of news article dictionaries
        """
        all_articles = []
        
        # Build query for Indian stock market news
        # Search for company names or general Indian market news
        queries = [
            "Indian stock market",
            "NSE BSE",
            "NIFTY"
        ] + [symbol for symbol in settings.TRACKED_STOCKS[:5]]  # Limit to avoid API quota
        
        for query in queries:
            self.logger.info(f"Fetching news for query: {query}")
            
            try:
                articles = self._fetch_news_for_query(query)
                if articles:
                    all_articles.extend(articles)
            except Exception as e:
                self.logger.error(f"Failed to fetch news for query '{query}': {e}")
                continue
        
        # Deduplicate by URL
        unique_articles = {article["url"]: article for article in all_articles}
        
        self.logger.info(f"Fetched {len(unique_articles)} unique articles")
        return list(unique_articles.values())
    
    def _fetch_news_for_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Fetch news articles for a specific query.
        
        Args:
            query: Search query
            
        Returns:
            List of articles
        """
        if not self.api_key:
            self.logger.warning("News API key not configured, using mock data")
            return self._generate_mock_news(query)
        
        try:
            # NewsAPI endpoint
            url = f"{self.api_url}/everything"
            
            # Fetch news from last 24 hours
            from_date = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            params = {
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.api_key
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get("articles", [])
                
                # Transform to internal format
                transformed = []
                for article in articles:
                    transformed.append({
                        "title": article.get("title"),
                        "content": article.get("content") or article.get("description"),
                        "summary": article.get("description"),
                        "url": article.get("url"),
                        "source": article.get("source", {}).get("name"),
                        "author": article.get("author"),
                        "published_at": article.get("publishedAt"),
                        "query": query  # Track which query found this article
                    })
                
                return transformed
        
        except Exception as e:
            self.logger.error(f"Error fetching news from API: {e}")
            return []
    
    def _generate_mock_news(self, query: str) -> List[Dict[str, Any]]:
        """
        Generate mock news for testing when API is not configured.
        
        Args:
            query: Search query
            
        Returns:
            List of mock articles
        """
        return [
            {
                "title": f"{query} shows strong performance in Q4",
                "content": f"Latest analysis shows {query} demonstrating robust growth...",
                "summary": f"{query} Q4 performance summary",
                "url": f"https://example.com/news/{query.replace(' ', '-').lower()}-{int(datetime.utcnow().timestamp())}",
                "source": "Mock Financial Times",
                "author": "Test Author",
                "published_at": datetime.utcnow().isoformat(),
                "query": query
            }
        ]
    
    def _extract_stock_symbols(self, article: Dict[str, Any]) -> List[str]:
        """
        Extract relevant stock symbols from article content.
        
        Args:
            article: Article dictionary
            
        Returns:
            List of stock symbols mentioned in the article
        """
        mentioned_symbols = []
        
        # Search for tracked stock symbols in title and content
        text = f"{article.get('title', '')} {article.get('content', '')} {article.get('summary', '')}".upper()
        
        for symbol in settings.TRACKED_STOCKS:
            if symbol in text:
                mentioned_symbols.append(symbol)
        
        # Also check if query was a stock symbol
        query = article.get("query", "").upper()
        if query in settings.TRACKED_STOCKS and query not in mentioned_symbols:
            mentioned_symbols.append(query)
        
        return mentioned_symbols
    
    def process_data(self, data: List[Dict[str, Any]], db: Session) -> Dict[str, int]:
        """
        Process and store news articles.
        
        Args:
            data: List of news articles
            db: Database session
            
        Returns:
            Metrics dictionary
        """
        metrics = {
            "fetched": len(data),
            "inserted": 0,
            "updated": 0,
            "skipped": 0
        }
        
        for article in data:
            try:
                # Compute content hash for idempotency
                content_str = f"{article['url']}{article['title']}"
                content_hash = hashlib.sha256(content_str.encode()).hexdigest()
                
                # Check if article already exists
                existing = db.query(News).filter(News.content_hash == content_hash).first()
                if existing:
                    metrics["skipped"] += 1
                    continue
                
                # Extract relevant stocks
                stock_symbols = self._extract_stock_symbols(article)
                
                if not stock_symbols:
                    # Skip articles not related to any tracked stocks
                    metrics["skipped"] += 1
                    continue
                
                # Parse published date
                published_at = article.get("published_at")
                if isinstance(published_at, str):
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                elif not published_at:
                    published_at = datetime.utcnow()
                
                # Create news entry
                news = News(
                    title=article.get("title", "")[:500],
                    content=article.get("content"),
                    summary=article.get("summary"),
                    url=article.get("url"),
                    source=article.get("source"),
                    author=article.get("author"),
                    published_at=published_at,
                    content_hash=content_hash
                )
                
                db.add(news)
                db.flush()  # Get news ID
                
                # Associate with stocks
                for symbol in stock_symbols:
                    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                    if stock:
                        news_stock = NewsStock(
                            news_id=news.id,
                            stock_id=stock.id
                        )
                        db.add(news_stock)
                
                metrics["inserted"] += 1
                self.logger.info(f"Stored news article: {news.title[:50]}... (stocks: {stock_symbols})")
                
            except Exception as e:
                self.logger.error(f"Failed to store article: {e}")
                metrics["skipped"] += 1
                continue
        
        db.commit()
        return metrics
