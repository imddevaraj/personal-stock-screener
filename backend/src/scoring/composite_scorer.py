"""
Composite scoring engine.
Combines fundamental and sentiment scores into final ranking.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..core.config import settings
from ..core.logging import get_logger
from ..models.database import Stock, Fundamental, CompositeScore
from .fundamental_scorer import FundamentalScorer
from ..sentiment.analyzer import SentimentAnalyzer


logger = get_logger(__name__)


class CompositeScorer:
    """
    Composite scorer combining fundamental and sentiment analysis.
    
    Produces final stock rankings with explainability.
    """
    
    def __init__(self):
        """Initialize composite scorer."""
        self.logger = get_logger(self.__class__.__name__)
        self.fundamental_scorer = FundamentalScorer()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Get weights from config
        self.fundamental_weight = settings.FUNDAMENTAL_WEIGHT
        self.sentiment_weight =settings.SENTIMENT_WEIGHT
    
    def compute_composite_score(
        self,
        stock_id: int,
        db: Session,
        score_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Compute composite score for a stock.
        
        Args:
            stock_id: Stock ID
            db: Database session
            score_date: Date of scoring (default: now)
            
        Returns:
            Composite score data or None if insufficient data
        """
        if score_date is None:
            score_date = datetime.utcnow()
        
        stock = db.query(Stock).get(stock_id)
        if not stock:
            self.logger.error(f"Stock {stock_id} not found")
            return None
        
        # Get latest fundamental data
        latest_fundamental = db.query(Fundamental).filter(
            Fundamental.stock_id == stock_id
        ).order_by(desc(Fundamental.data_date)).first()
        
        if not latest_fundamental:
            self.logger.warning(f"No fundamental data for {stock.symbol}")
            return None
        
        # Compute fundamental score
        fundamental_result = self.fundamental_scorer.compute_fundamental_score(latest_fundamental)
        fundamental_score = fundamental_result["total_score"]
        
        # Get aggregated sentiment score
        sentiment_result = self.sentiment_analyzer.aggregate_sentiment_score(
            stock_id=stock_id,
            db=db,
            days=30
        )
        sentiment_score = sentiment_result["score_0_100"]
        
        # Compute weighted composite score
        composite_score = (
            self.fundamental_weight * fundamental_score +
            self.sentiment_weight * sentiment_score
        )
        
        # Build explainability breakdown
        score_breakdown = {
            "fundamental": {
                "score": fundamental_score,
                "weight": self.fundamental_weight,
                "weighted_score": self.fundamental_weight * fundamental_score,
                "breakdown": fundamental_result["breakdown"]
            },
            "sentiment": {
                "score": sentiment_score,
                "weight": self.sentiment_weight,
                "weighted_score": self.sentiment_weight * sentiment_score,
                "average_sentiment": sentiment_result["average_score"],
                "article_count": sentiment_result["count"],
                "positive_count": sentiment_result["positive_count"],
                "negative_count": sentiment_result["negative_count"],
                "neutral_count": sentiment_result["neutral_count"]
            },
            "composite": {
                "score": round(composite_score, 2),
                "formula": f"{self.fundamental_weight} * fundamental + {self.sentiment_weight} * sentiment"
            }
        }
        
        return {
            "stock_id": stock_id,
            "symbol": stock.symbol,
            "fundamental_score": round(fundamental_score, 2),
            "sentiment_score": round(sentiment_score, 2),
            "composite_score": round(composite_score, 2),
            "score_breakdown": score_breakdown,
            "score_date": score_date
        }
    
    def score_all_stocks(self, db: Session) -> Dict[str, Any]:
        """
        Compute composite scores for all active stocks and update rankings.
        
        Args:
            db: Database session
            
        Returns:
            Scoring results with metrics
        """
        score_date = datetime.utcnow()
        
        results = {
            "scored": 0,
            "skipped": 0,
            "errors": 0,
            "scores": []
        }
        
        # Get all active stocks
        stocks = db.query(Stock).filter(Stock.is_active == True).all()
        
        self.logger.info(f"Computing composite scores for {len(stocks)} stocks")
        
        # Compute scores
        for stock in stocks:
            try:
                score_data = self.compute_composite_score(
                    stock_id=stock.id,
                    db=db,
                    score_date=score_date
                )
                
                if score_data:
                    results["scores"].append(score_data)
                    results["scored"] += 1
                else:
                    results["skipped"] += 1
            
            except Exception as e:
                self.logger.error(f"Error scoring {stock.symbol}: {e}")
                results["errors"] += 1
        
        # Sort by composite score
        results["scores"].sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Assign ranks
        for rank, score_data in enumerate(results["scores"], start=1):
            score_data["rank"] = rank
        
        # Store in database
        self.logger.info("Storing composite scores in database...")
        
        for score_data in results["scores"]:
            try:
                composite_score = CompositeScore(
                    stock_id=score_data["stock_id"],
                    fundamental_score=score_data["fundamental_score"],
                    sentiment_score=score_data["sentiment_score"],
                    composite_score=score_data["composite_score"],
                    rank=score_data["rank"],
                    score_breakdown=score_data["score_breakdown"],
                    score_date=score_date
                )
                
                db.add(composite_score)
            
            except Exception as e:
                self.logger.error(f"Failed to store score for stock {score_data['stock_id']}: {e}")
        
        db.commit()
        
        self.logger.info(
            f"Composite scoring complete: {results['scored']} scored, "
            f"{results['skipped']} skipped, {results['errors']} errors"
        )
        
        return results
    
    def get_top_stocks(
        self,
        db: Session,
        limit: int = 10,
        min_composite_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top-ranked stocks by composite score.
        
        Args:
            db: Database session
            limit: Number of stocks to return
            min_composite_score: Minimum composite score filter
            
        Returns:
            List of top stock scores
        """
        query = db.query(CompositeScore).join(Stock).filter(
            Stock.is_active == True
        ).order_by(
            desc(CompositeScore.score_date),
            CompositeScore.rank
        )
        
        if min_composite_score is not None:
            query = query.filter(CompositeScore.composite_score >= min_composite_score)
        
        scores = query.limit(limit).all()
        
        results = []
        for score in scores:
            stock = db.query(Stock).get(score.stock_id)
            results.append({
                "rank": score.rank,
                "symbol": stock.symbol,
                "name": stock.name,
                "fundamental_score": score.fundamental_score,
                "sentiment_score": score.sentiment_score,
                "composite_score": score.composite_score,
                "score_breakdown": score.score_breakdown,
                "score_date": score.score_date
            })
        
        return results
