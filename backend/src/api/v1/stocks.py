"""
Stocks API endpoints.
Provides access to stock information, fundamentals, sentiment, and scores.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ...core.database import get_db
from ...core.logging import get_logger
from ...models.database import Stock, Fundamental, CompositeScore, SentimentScore
from ...models.schemas import (
    StockResponse,
    FundamentalResponse,
    CompositeScoreResponse,
    SentimentScoreResponse,
    StockWithScore
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[StockResponse])
def list_stocks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    sector: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all stocks with optional filtering.
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        sector: Filter by sector
        db: Database session
        
    Returns:
        List of stocks
    """
    query = db.query(Stock).filter(Stock.is_active == True)
    
    if sector:
        query = query.filter(Stock.sector == sector)
    
    stocks = query.offset(skip).limit(limit).all()
    
    return stocks


@router.get("/{symbol}", response_model=StockWithScore)
def get_stock(symbol: str, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific stock.
    
    Args:
        symbol: Stock symbol
        db: Database session
        
    Returns:
        Stock with latest score and fundamentals
    """
    # Get stock
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Get latest fundamental data
    latest_fundamental = db.query(Fundamental).filter(
        Fundamental.stock_id == stock.id
    ).order_by(desc(Fundamental.data_date)).first()
    
    # Get latest composite score
    latest_score = db.query(CompositeScore).filter(
        CompositeScore.stock_id == stock.id
    ).order_by(desc(CompositeScore.score_date)).first()
    
    return {
        "stock": stock,
        "latest_fundamental": latest_fundamental,
        "latest_score": latest_score
    }


@router.get("/{symbol}/fundamentals", response_model=List[FundamentalResponse])
def get_stock_fundamentals(
    symbol: str,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get historical fundamental data for a stock.
    
    Args:
        symbol: Stock symbol
        limit: Number of historical records
        db: Database session
        
    Returns:
        List of fundamental data points
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    fundamentals = db.query(Fundamental).filter(
        Fundamental.stock_id == stock.id
    ).order_by(desc(Fundamental.data_date)).limit(limit).all()
    
    return fundamentals


@router.get("/{symbol}/scores", response_model=List[CompositeScoreResponse])
def get_stock_scores(
    symbol: str,
    limit: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get historical composite scores for a stock.
    
    Args:
        symbol: Stock symbol
        limit: Number of historical records
        db: Database session
        
    Returns:
        List of composite scores
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    scores = db.query(CompositeScore).filter(
        CompositeScore.stock_id == stock.id
    ).order_by(desc(CompositeScore.score_date)).limit(limit).all()
    
    return scores


from sqlalchemy.orm import Session, joinedload

# ... (imports remain the same, just adding joinedload if not present, but for replace_file I will just modify the function)

@router.get("/{symbol}/sentiment", response_model=List[SentimentScoreResponse])
def get_stock_sentiment(
    symbol: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get recent sentiment scores for a stock.
    
    Args:
        symbol: Stock symbol
        limit: Number of sentiment records
        db: Database session
        
    Returns:
        List of sentiment scores
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    sentiments = db.query(SentimentScore).options(
        joinedload(SentimentScore.news)
    ).filter(
        SentimentScore.stock_id == stock.id
    ).order_by(desc(SentimentScore.created_at)).limit(limit).all()
    
    return sentiments


@router.get("/sectors/list", response_model=List[str])
def list_sectors(db: Session = Depends(get_db)):
    """
    Get list of all sectors.
    
    Returns:
        List of unique sector names
    """
    sectors = db.query(Stock.sector).filter(
        Stock.sector.isnot(None),
        Stock.is_active == True
    ).distinct().all()
    
    return [sector[0] for sector in sectors if sector[0]]
