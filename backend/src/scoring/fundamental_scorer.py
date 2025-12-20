"""
Fundamental scoring engine with config-driven rules.
Computes fundamental score based on financial metrics.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.logging import get_logger
from ..models.database import Stock, Fundamental, CompositeScore


logger = get_logger(__name__)


class FundamentalScorer:
    """
    Score stocks based on fundamental metrics.
    
    Uses configurable thresholds from settings to rate various financial metrics.
    """
    
    def __init__(self):
        """Initialize fundamental scorer with configuration."""
        self.logger = get_logger(self.__class__.__name__)
        
        # Load scoring thresholds from config
        self.thresholds = {
            "pe_ratio": {
                "excellent": settings.PE_RATIO_EXCELLENT,
                "good": settings.PE_RATIO_GOOD,
                "weight": 0.15
            },
            "pb_ratio": {
                "excellent": settings.PB_RATIO_EXCELLENT,
                "good": settings.PB_RATIO_GOOD,
                "weight": 0.10
            },
            "roe": {
                "excellent": settings.ROE_EXCELLENT,
                "good": settings.ROE_GOOD,
                "weight": 0.20
            },
            "debt_to_equity": {
                "excellent": settings.DEBT_TO_EQUITY_EXCELLENT,
                "good": settings.DEBT_TO_EQUITY_GOOD,
                "weight": 0.15,
                "inverse": True  # Lower is better
            },
            "current_ratio": {
                "excellent": 2.0,
                "good": 1.5,
                "weight": 0.10
            },
            "operating_margin": {
                "excellent": 0.20,  # 20%
                "good": 0.10,  # 10%
                "weight": 0.15
            },
            "revenue_growth": {
                "excellent": 0.20,  # 20% growth
                "good": 0.10,  # 10% growth
                "weight": 0.15
            }
        }
    
    def score_metric(
        self,
        value: Optional[float],
        excellent_threshold: float,
        good_threshold: float,
        inverse: bool = False
    ) -> float:
        """
        Score a single metric on a 0-100 scale.
        
        Args:
            value: Metric value
            excellent_threshold: Threshold for excellent score (100pts)
            good_threshold: Threshold for good score (70pts)
            inverse: If True, lower values are better
            
        Returns:
            Score from 0-100
        """
        if value is None:
            return 50  # Neutral score for missing data
        
        if inverse:
            # For debt ratios, lower is better
            if value <= excellent_threshold:
                return 100
            elif value <= good_threshold:
                # Linear interpolation between excellent and good
                return 70 + 30 * (1 - (value - excellent_threshold) / (good_threshold - excellent_threshold))
            else:
                # Decaying score for values above good threshold
                penalty = max(0, 70 - (value - good_threshold) * 20)
                return max(0, penalty)
        else:
            # For most metrics, higher is better
            if value >= excellent_threshold:
                return 100
            elif value >= good_threshold:
                # Linear interpolation between good and excellent
                return 70 + 30 * (value - good_threshold) / (excellent_threshold - good_threshold)
            else:
                # Decaying score below good threshold
                return max(0, 70 * (value / good_threshold))
    
    def compute_fundamental_score(self, fundamental: Fundamental) -> Dict[str, Any]:
        """
        Compute fundamental score with breakdown.
        
        Args:
            fundamental: Fundamental data record
            
        Returns:
            Dictionary with total score and detailed breakdown
        """
        scores = {}
        total_score = 0
        total_weight = 0
        
        # Score each metric
        metric_mappings = {
            "pe_ratio": fundamental.pe_ratio,
            "pb_ratio": fundamental.pb_ratio,
            "roe": fundamental.roe,
            "debt_to_equity": fundamental.debt_to_equity,
            "current_ratio": fundamental.current_ratio,
            "operating_margin": fundamental.operating_margin,
            "revenue_growth": fundamental.revenue_growth
        }
        
        for metric_name, metric_value in metric_mappings.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]
                
                score = self.score_metric(
                    value=metric_value,
                    excellent_threshold=threshold["excellent"],
                    good_threshold=threshold["good"],
                    inverse=threshold.get("inverse", False)
                )
                
                weight = threshold["weight"]
                weighted_score = score * weight
                
                scores[metric_name] = {
                    "value": metric_value,
                    "score": round(score, 2),
                    "weight": weight,
                    "weighted_score": round(weighted_score, 2)
                }
                
                total_score += weighted_score
                total_weight += weight
        
        # Normalize if total weight != 1 (due to missing metrics)
        if total_weight > 0:
            final_score = (total_score / total_weight) * 100
        else:
            final_score = 50  # Neutral score if no metrics available
        
        return {
            "total_score": round(final_score, 2),
            "breakdown": scores,
            "metrics_used": len(scores),
            "total_weight": round(total_weight, 2)
        }
    
    def score_all_stocks(self, db: Session) -> Dict[str, Any]:
        """
        Compute fundamental scores for all stocks with recent data.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with scoring results
        """
        results = {
            "scored": 0,
            "skipped": 0,
            "errors": 0
        }
        
        # Get all active stocks
        stocks = db.query(Stock).filter(Stock.is_active == True).all()
        
        for stock in stocks:
            try:
                # Get latest fundamental data
                latest_fundamental = db.query(Fundamental).filter(
                    Fundamental.stock_id == stock.id
                ).order_by(Fundamental.data_date.desc()).first()
                
                if not latest_fundamental:
                    self.logger.warning(f"No fundamental data for {stock.symbol}")
                    results["skipped"] += 1
                    continue
                
                # Compute score
                score_data = self.compute_fundamental_score(latest_fundamental)
                
                self.logger.info(
                    f"Fundamental score for {stock.symbol}: {score_data['total_score']} "
                    f"({score_data['metrics_used']} metrics)"
                )
                
                results["scored"] += 1
                
                # Store score would happen in composite_scorer
                # This method is primarily for batch computation
                
            except Exception as e:
                self.logger.error(f"Error scoring {stock.symbol}: {e}")
                results["errors"] += 1
        
        return results
