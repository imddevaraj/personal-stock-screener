"""
Screening API endpoints.
Provides stock screening and ranking functionality.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ...core.database import get_db
from ...core.logging import get_logger
from ...models.database import Stock, Fundamental, CompositeScore
from ...models.schemas import (
    ScreeningFilters,
    ScreeningResponse,
    StockWithScore,
    StockResponse,
    CompositeScoreResponse,
    FundamentalResponse
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=ScreeningResponse)
def screen_stocks(
    filters: ScreeningFilters = Body(...),
    db: Session = Depends(get_db)
):
    """
    Screen stocks based on filters.
    
    Args:
        filters: Screening criteria
        db: Database session
        
    Returns:
        Filtered and ranked stocks
    """
    # Start with latest composite scores
    subquery = db.query(
        CompositeScore.stock_id,
        CompositeScore.id.label("score_id")
    ).distinct(
        CompositeScore.stock_id
    ).order_by(
        CompositeScore.stock_id,
        desc(CompositeScore.score_date)
    ).subquery()
    
    query = db.query(Stock, CompositeScore, Fundamental).join(
        subquery, Stock.id == subquery.c.stock_id
    ).join(
        CompositeScore, CompositeScore.id == subquery.c.score_id
    ).outerjoin(
        Fundamental, and_(
            Fundamental.stock_id == Stock.id,
            Fundamental.id == db.query(Fundamental.id).filter(
                Fundamental.stock_id == Stock.id
            ).order_by(desc(Fundamental.data_date)).limit(1).scalar_subquery()
        )
    ).filter(
        Stock.is_active == True
    )
    
    # Apply filters
    if filters.sectors:
        query = query.filter(Stock.sector.in_(filters.sectors))
    
    if filters.market_cap_min:
        query = query.filter(Stock.market_cap >= filters.market_cap_min)
    
    if filters.market_cap_max:
        query = query.filter(Stock.market_cap <= filters.market_cap_max)
    
    if filters.fundamental_score_min:
        query = query.filter(CompositeScore.fundamental_score >= filters.fundamental_score_min)
    
    if filters.sentiment_score_min:
        query = query.filter(CompositeScore.sentiment_score >= filters.sentiment_score_min)
    
    if filters.composite_score_min:
        query = query.filter(CompositeScore.composite_score >= filters.composite_score_min)
    
    # Fundamental filters (if fundamental data exists)
    if filters.pe_ratio_min and Fundamental.pe_ratio:
        query = query.filter(Fundamental.pe_ratio >= filters.pe_ratio_min)
    
    if filters.pe_ratio_max and Fundamental.pe_ratio:
        query = query.filter(Fundamental.pe_ratio <= filters.pe_ratio_max)
    
    if filters.pb_ratio_min and Fundamental.pb_ratio:
        query = query.filter(Fundamental.pb_ratio >= filters.pb_ratio_min)
    
    if filters.pb_ratio_max and Fundamental.pb_ratio:
        query = query.filter(Fundamental.pb_ratio <= filters.pb_ratio_max)
    
    if filters.roe_min and Fundamental.roe:
        query = query.filter(Fundamental.roe >= filters.roe_min)
    
    if filters.debt_to_equity_max and Fundamental.debt_to_equity:
        query = query.filter(Fundamental.debt_to_equity <= filters.debt_to_equity_max)
    
    # Count total before pagination
    total_count = query.count()
    
    # Apply sorting
    sort_column_map = {
        "composite_score": CompositeScore.composite_score,
        "fundamental_score": CompositeScore.fundamental_score,
        "sentiment_score": CompositeScore.sentiment_score,
        "rank": CompositeScore.rank,
        "pe_ratio": Fundamental.pe_ratio,
        "market_cap": Stock.market_cap
    }
    
    sort_column = sort_column_map.get(filters.sort_by, CompositeScore.composite_score)
    
    if filters.sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    query = query.offset(filters.offset).limit(filters.limit)
    
    # Execute query
    results = query.all()
    
    # Build response
    stocks_with_scores = []
    for stock, score, fundamental in results:
        stocks_with_scores.append({
            "stock": stock,
            "latest_score": score,
            "latest_fundamental": fundamental
        })
    
    return {
        "total_count": total_count,
        "results": stocks_with_scores,
        "filters_applied": filters
    }


@router.get("/rankings/composite", response_model=List[dict])
def get_composite_rankings(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get top stocks by composite score.
    
    Args:
        limit: Number of top stocks
        db: Database session
        
    Returns:
        Top ranked stocks
    """
    from ...scoring.composite_scorer import CompositeScorer
    
    scorer = CompositeScorer()
    return scorer.get_top_stocks(db=db, limit=limit)


@router.get("/rankings/fundamental", response_model=List[dict])
def get_fundamental_rankings(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get top stocks by fundamental score.
    
    Args:
        limit: Number of top stocks
        db: Database session
        
    Returns:
        Top stocks by fundamentals
    """
    # Get latest scores
    subquery = db.query(
        CompositeScore.stock_id,
        CompositeScore.id.label("score_id")
    ).distinct(
        CompositeScore.stock_id
    ).order_by(
        CompositeScore.stock_id,
        desc(CompositeScore.score_date)
    ).limit(1000).subquery()
    
    results = db.query(Stock, CompositeScore).join(
        subquery, Stock.id == subquery.c.stock_id
    ).join(
        CompositeScore, CompositeScore.id == subquery.c.score_id
    ).order_by(
        desc(CompositeScore.fundamental_score)
    ).limit(limit).all()
    
    return [
        {
            "rank": idx + 1,
            "symbol": stock.symbol,
            "name": stock.name,
            "fundamental_score": score.fundamental_score,
            "sentiment_score": score.sentiment_score,
            "composite_score": score.composite_score
        }
        for idx, (stock, score) in enumerate(results)
    ]


@router.get("/rankings/sentiment", response_model=List[dict])
def get_sentiment_rankings(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get top stocks by sentiment score.
    
    Args:
        limit: Number of top stocks
        db: Database session
        
    Returns:
        Top stocks by sentiment
    """
    # Get latest scores
    subquery = db.query(
        CompositeScore.stock_id,
        CompositeScore.id.label("score_id")
    ).distinct(
        CompositeScore.stock_id
    ).order_by(
        CompositeScore.stock_id,
        desc(CompositeScore.score_date)
    ).limit(1000).subquery()
    
    results = db.query(Stock, CompositeScore).join(
        subquery, Stock.id == subquery.c.stock_id
    ).join(
        CompositeScore, CompositeScore.id == subquery.c.score_id
    ).order_by(
        desc(CompositeScore.sentiment_score)
    ).limit(limit).all()
    
    return [
        {
            "rank": idx + 1,
            "symbol": stock.symbol,
            "name": stock.name,
            "fundamental_score": score.fundamental_score,
            "sentiment_score": score.sentiment_score,
            "composite_score": score.composite_score
        }
        for idx, (stock, score) in enumerate(results)
    ]
