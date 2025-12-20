"""
Base class for all data ingestors.
Provides common functionality: idempotency, retry logic, logging, error handling.
"""
import time
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from functools import wraps

from sqlalchemy.orm import Session

from ..core.logging import get_logger
from ..core.database import get_db_context
from ..models.database import IngestionLog


logger = get_logger(__name__)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


class BaseIngestor(ABC):
    """
    Abstract base class for all data ingestors.
    
    Ensures consistent behavior:
    - Idempotent ingestion via hash-based deduplication
    - Retry logic with exponential backoff
    - Structured logging
    - Error handling and audit trail
    """
    
    def __init__(self, source: str, ingestion_type: str):
        """
        Initialize ingestor.
        
        Args:
            source: Data source identifier
            ingestion_type: Type of ingestion (fundamental/news)
        """
        self.source = source
        self.ingestion_type = ingestion_type
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def fetch_data(self) -> Any:
        """
        Fetch data from the source.
        
        Must be implemented by subclasses.
        
        Returns:
            Fetched data
        """
        pass
    
    @abstractmethod
    def process_data(self, data: Any, db: Session) -> Dict[str, int]:
        """
        Process and store fetched data.
        
        Must be implemented by subclasses.
        
        Args:
            data: Fetched data
            db: Database session
            
        Returns:
            Dictionary with metrics (inserted, updated, skipped counts)
        """
        pass
    
    def compute_data_hash(self, data: Any) -> str:
        """
        Compute hash of data for idempotency check.
        
        Args:
            data: Data to hash
            
        Returns:
            SHA256 hash string
        """
        data_str = str(data).encode('utf-8')
        return hashlib.sha256(data_str).hexdigest()
    
    def is_already_ingested(self, data_hash: str, db: Session) -> bool:
        """
        Check if data with given hash has already been ingested.
        
        Args:
            data_hash: Hash of the data
            db: Database session
            
        Returns:
            True if already ingested, False otherwise
        """
        existing_log = db.query(IngestionLog).filter(
            IngestionLog.ingestion_type == self.ingestion_type,
            IngestionLog.data_hash == data_hash,
            IngestionLog.status == "success"
        ).first()
        
        return existing_log is not None
    
    def create_ingestion_log(
        self,
        db: Session,
        data_hash: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        records_fetched: int = 0,
        records_inserted: int = 0,
        records_updated: int = 0,
        records_skipped: int = 0,
        error_message: Optional[str] = None
    ) -> IngestionLog:
        """
        Create an ingestion log entry.
        
        Args:
            db: Database session
            data_hash: Hash of ingested data
            status: success/failed/partial
            started_at: Start time
            completed_at: Completion time
            records_fetched: Number of records fetched
            records_inserted: Number of records inserted
            records_updated: Number of records updated
            records_skipped: Number of records skipped
            error_message: Error message if failed
            
        Returns:
            Created ingestion log
        """
        duration = None
        if completed_at and started_at:
            duration = (completed_at - started_at).total_seconds()
        
        log = IngestionLog(
            ingestion_type=self.ingestion_type,
            source=self.source,
            data_hash=data_hash,
            status=status,
            error_message=error_message,
            records_fetched=records_fetched,
            records_inserted=records_inserted,
            records_updated=records_updated,
            records_skipped=records_skipped,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration
        )
        
        db.add(log)
        db.commit()
        
        self.logger.info(
            f"Ingestion log created: type={self.ingestion_type}, status={status}, "
            f"fetched={records_fetched}, inserted={records_inserted}, "
            f"updated={records_updated}, skipped={records_skipped}"
        )
        
        return log
    
    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def run(self) -> Dict[str, Any]:
        """
        Run the ingestion process.
        
        Returns:
            Dictionary with ingestion results and metrics
        """
        started_at = datetime.utcnow()
        self.logger.info(f"Starting {self.ingestion_type} ingestion from {self.source}")
        
        try:
            # Fetch data
            self.logger.info("Fetching data...")
            data = self.fetch_data()
            
            if not data:
                self.logger.warning("No data fetched")
                return {
                    "status": "success",
                    "message": "No data to ingest",
                    "metrics": {
                        "fetched": 0,
                        "inserted": 0,
                        "updated": 0,
                        "skipped": 0
                    }
                }
            
            # Compute hash for idempotency
            data_hash = self.compute_data_hash(data)
            
            # Check if already ingested
            with get_db_context() as db:
                if self.is_already_ingested(data_hash, db):
                    self.logger.info(f"Data already ingested (hash: {data_hash[:16]}...)")
                    return {
                        "status": "skipped",
                        "message": "Data already ingested",
                        "data_hash": data_hash
                    }
                
                # Process and store data
                self.logger.info("Processing data...")
                metrics = self.process_data(data, db)
                
                completed_at = datetime.utcnow()
                
                # Create ingestion log
                self.create_ingestion_log(
                    db=db,
                    data_hash=data_hash,
                    status="success",
                    started_at=started_at,
                    completed_at=completed_at,
                    records_fetched=metrics.get("fetched", 0),
                    records_inserted=metrics.get("inserted", 0),
                    records_updated=metrics.get("updated", 0),
                    records_skipped=metrics.get("skipped", 0)
                )
                
                self.logger.info(
                    f"{self.ingestion_type} ingestion completed successfully. "
                    f"Metrics: {metrics}"
                )
                
                return {
                    "status": "success",
                    "message": "Ingestion completed successfully",
                    "data_hash": data_hash,
                    "metrics": metrics
                }
        
        except Exception as e:
            completed_at = datetime.utcnow()
            error_message = str(e)
            
            self.logger.error(f"Ingestion failed: {error_message}", exc_info=True)
            
            # Log failure
            try:
                with get_db_context() as db:
                    self.create_ingestion_log(
                        db=db,
                        data_hash="error",
                        status="failed",
                        started_at=started_at,
                        completed_at=completed_at,
                        error_message=error_message
                    )
            except Exception as log_error:
                self.logger.error(f"Failed to create error log: {log_error}")
            
            raise
