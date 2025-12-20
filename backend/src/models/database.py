"""
Database models using SQLAlchemy ORM.
Defines tables for stocks, fundamentals, news, sentiment, scores, and alerts.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, ForeignKey, Index, UniqueConstraint, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


Base = declarative_base()


class Stock(Base):
    """Company/Stock master data."""
    
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    sector = Column(String(100), index=True)
    industry = Column(String(100))
    market_cap = Column(Float)  # In crores
    exchange = Column(String(10), default="NSE")  # NSE/BSE
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fundamentals = relationship("Fundamental", back_populates="stock", cascade="all, delete-orphan")
    news = relationship("News", secondary="news_stocks", back_populates="stocks")
    sentiment_scores = relationship("SentimentScore", back_populates="stock", cascade="all, delete-orphan")
    composite_scores = relationship("CompositeScore", back_populates="stock", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Stock {self.symbol} - {self.name}>"


class Fundamental(Base):
    """Fundamental financial metrics for stocks."""
    
    __tablename__ = "fundamentals"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    
    # Valuation Ratios
    pe_ratio = Column(Float)  # Price to Earnings
    pb_ratio = Column(Float)  # Price to Book
    ps_ratio = Column(Float)  # Price to Sales
    dividend_yield = Column(Float)
    
    # Profitability Metrics
    roe = Column(Float)  # Return on Equity
    roa = Column(Float)  # Return on Assets
    operating_margin = Column(Float)
    net_margin = Column(Float)
    
    # Financial Health
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    
    # Growth Metrics
    revenue_growth = Column(Float)  # YoY %
    earnings_growth = Column(Float)  # YoY %
    
    # Price Information
    current_price = Column(Float)
    week_52_high = Column(Float)
    week_52_low = Column(Float)
    
    # Metadata
    data_date = Column(DateTime, nullable=False)  # Date of the financial data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    stock = relationship("Stock", back_populates="fundamentals")
    
    __table_args__ = (
        Index("idx_stock_data_date", "stock_id", "data_date"),
    )
    
    def __repr__(self):
        return f"<Fundamental stock_id={self.stock_id} date={self.data_date}>"


class News(Base):
    """News articles related to stocks."""
    
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String(1000), unique=True, nullable=False)
    source = Column(String(100))  # News source name
    author = Column(String(200))
    
    published_at = Column(DateTime, nullable=False, index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Hash for idempotency check
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Relationships
    stocks = relationship("Stock", secondary="news_stocks", back_populates="news")
    sentiment_scores = relationship("SentimentScore", back_populates="news", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<News {self.title[:50]}...>"


class NewsStock(Base):
    """Association table between News and Stocks (many-to-many)."""
    
    __tablename__ = "news_stocks"
    
    id = Column(Integer, primary_key=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("news_id", "stock_id", name="uq_news_stock"),
        Index("idx_news_stock", "news_id", "stock_id"),
    )


class SentimentScore(Base):
    """Sentiment analysis results for news articles."""
    
    __tablename__ = "sentiment_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    
    # Sentiment Analysis Results
    sentiment_label = Column(String(20), nullable=False)  # positive/negative/neutral
    sentiment_score = Column(Float, nullable=False)  # -1 to +1
    confidence = Column(Float)  # 0 to 1
    
    # Model Information
    model_name = Column(String(100))
    model_version = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    news = relationship("News", back_populates="sentiment_scores")
    stock = relationship("Stock", back_populates="sentiment_scores")
    
    __table_args__ = (
        Index("idx_sentiment_stock_created", "stock_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<SentimentScore stock_id={self.stock_id} label={self.sentiment_label} score={self.sentiment_score}>"


class CompositeScore(Base):
    """Composite scores combining fundamental and sentiment analysis."""
    
    __tablename__ = "composite_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    
    # Individual Scores (0-100)
    fundamental_score = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    
    # Composite Score (weighted average, 0-100)
    composite_score = Column(Float, nullable=False, index=True)
    
    # Ranking
    rank = Column(Integer, index=True)
    
    # Explainability - JSON field with score breakdown
    score_breakdown = Column(JSON)
    
    # Metadata
    score_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    stock = relationship("Stock", back_populates="composite_scores")
    
    __table_args__ = (
        Index("idx_composite_score_date", "composite_score", "score_date"),
        Index("idx_stock_score_date", "stock_id", "score_date"),
    )
    
    def __repr__(self):
        return f"<CompositeScore stock_id={self.stock_id} score={self.composite_score} rank={self.rank}>"


class Alert(Base):
    """User-defined alert rules."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Alert Configuration
    name = Column(String(200), nullable=False)
    description = Column(Text)
    alert_type = Column(String(50), nullable=False)  # score_threshold, sentiment_change, price_change
    
    # Conditions (JSON)
    conditions = Column(JSON, nullable=False)
    
    # Target stocks (null = all stocks)
    stock_symbols = Column(JSON)  # List of symbols or null for all
    
    # Notification
    notification_channels = Column(JSON)  # email, webhook, etc.
    notification_config = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Alert {self.name} type={self.alert_type}>"


class IngestionLog(Base):
    """Audit log for data ingestion (ensures idempotency)."""
    
    __tablename__ = "ingestion_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Ingestion metadata
    ingestion_type = Column(String(50), nullable=False, index=True)  # fundamental/news
    source = Column(String(100), nullable=False)
    
    # Idempotency key (hash of source data)
    data_hash = Column(String(64), nullable=False, index=True)
    
    # Status
    status = Column(String(20), nullable=False)  # success/failed/partial
    error_message = Column(Text)
    
    # Metrics
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_ingestion_type_hash", "ingestion_type", "data_hash"),
        Index("idx_ingestion_created", "ingestion_type", "created_at"),
    )
    
    def __repr__(self):
        return f"<IngestionLog type={self.ingestion_type} status={self.status}>"
