"""
Celery tasks for scoring computation.
"""
from celery import shared_task

from ..core.database import get_db_context
from ..core.logging import get_logger
from ..scoring.composite_scorer import CompositeScorer

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2)
def compute_all_scores(self):
    """
    Celery task to compute composite scores for all stocks.
    
    Runs daily after fundamental data ingestion.
    """
    logger.info("Starting composite score computation task")
    
    try:
        scorer = CompositeScorer()
        
        with get_db_context() as db:
            result = scorer.score_all_stocks(db=db)
        
        logger.info(
            f"Score computation completed: {result['scored']} scored, "
            f"{result['skipped']} skipped, {result['errors']} errors"
        )
        
        return {
            "status": "success",
            "scored": result["scored"],
            "skipped": result["skipped"],
            "errors": result["errors"]
        }
    
    except Exception as e:
        logger.error(f"Score computation failed: {e}")
        raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))


@shared_task
def compute_score_for_stock(stock_id: int):
    """
    Compute composite score for a single stock.
    
    Args:
        stock_id: Stock ID
        
    Returns:
        Score computation result
    """
    logger.info(f"Computing score for stock ID: {stock_id}")
    
    try:
        scorer = CompositeScorer()
        
        with get_db_context() as db:
            result = scorer.compute_composite_score(stock_id=stock_id, db=db)
        
        if result:
            logger.info(
                f"Score computed for stock {result['symbol']}: "
                f"composite={result['composite_score']}"
            )
            return result
        else:
            logger.warning(f"Could not compute score for stock ID {stock_id}")
            return None
    
    except Exception as e:
        logger.error(f"Failed to compute score for stock {stock_id}: {e}")
        raise
