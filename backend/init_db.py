#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables and optionally seeds initial data.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.database import init_db, get_db_context
from src.core.logging import get_logger
from src.models.database import Stock

logger = get_logger(__name__)


def seed_stocks():
    """Seed initial stock data."""
    initial_stocks = [
        {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "sector": "Energy", "market_cap": 1700000},
        {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "sector": "IT", "market_cap": 1300000},
        {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "sector": "Banking", "market_cap": 1200000},
        {"symbol": "INFY", "name": "Infosys Ltd", "sector": "IT", "market_cap": 600000},
        {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "sector": "Banking", "market_cap": 700000},
        {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "sector": "Telecom", "market_cap": 560000},
        {"symbol": "ITC", "name": "ITC Ltd", "sector": "FMCG", "market_cap": 520000},
        {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking", "market_cap": 600000},
        {"symbol": "LT", "name": "Larsen & Toubro Ltd", "sector": "Infrastructure", "market_cap": 480000},
        {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "sector": "FMCG", "market_cap": 580000},
    ]
    
    with get_db_context() as db:
        # Check if stocks already exist
        existing_count = db.query(Stock).count()
        
        if existing_count > 0:
            logger.info(f"Database already has {existing_count} stocks. Skipping seed.")
            return
        
        # Add stocks
        for stock_data in initial_stocks:
            stock = Stock(**stock_data, exchange="NSE", is_active=True)
            db.add(stock)
        
        db.commit()
        logger.info(f"Seeded {len(initial_stocks)} stocks successfully")


def main():
    """Main initialization function."""
    logger.info("=== Database Initialization ===")
    
    # Create tables
    logger.info("Creating database tables...")
    init_db()
    logger.info("✓ Tables created successfully")
    
    # Seed initial data
    logger.info("Seeding initial stock data...")
    seed_stocks()
    logger.info("✓ Initial data seeded")
    
    logger.info("=== Database Initialization Complete ===")


if __name__ == "__main__":
    main()
