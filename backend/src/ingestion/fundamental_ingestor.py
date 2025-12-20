"""
Fundamental data ingestor for Indian stock market.
Fetches financial metrics from configured data sources.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from .base import BaseIngestor
from ..core.config import settings
from ..models.database import Stock, Fundamental


class FundamentalIngestor(BaseIngestor):
    """Ingestor for fundamental stock data."""
    
    def __init__(self, source: str = "yahoo_finance"):
        """
        Initialize fundamental ingestor.
        
        Args:
            source: Data source identifier (yahoo_finance, alpha_vantage, etc.)
        """
        super().__init__(source=source, ingestion_type="fundamental")
        self.api_url = settings.MARKET_DATA_BASE_URL
        self.api_key = settings.MARKET_DATA_API_KEY or settings.ALPHA_VANTAGE_API_KEY
    
    def fetch_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch fundamental data for tracked stocks.
        
        Returns:
            Dictionary mapping stock symbols to their fundamental data
        """
        all_data = {}
        
        for symbol in settings.TRACKED_STOCKS:
            self.logger.info(f"Fetching fundamental data for {symbol}")
            
            try:
                # Yahoo Finance-like API pattern (adjust based on actual API)
                # For MVP, using Alpha Vantage or Yahoo Finance alternative
                data = self._fetch_stock_fundamentals(symbol)
                if data:
                    all_data[symbol] = data
            except Exception as e:
                self.logger.error(f"Failed to fetch data for {symbol}: {e}")
                continue
        
        return all_data
    
    def _fetch_stock_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch fundamentals for a single stock.
        
        This is a placeholder implementation. In production, integrate with:
        - Alpha Vantage API
        - Yahoo Finance via yfinance library
        - NSE/BSE official APIs
        - Commercial data providers
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with fundamental metrics or None
        """
        # Placeholder implementation using yfinance concept
        # In production, replace with actual API calls
        
        try:
            import yfinance as yf
            
            # For Indian stocks, append .NS (NSE) or .BO (BSE)
            ticker_symbol = f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            
            info = ticker.info
            
            # Extract fundamental metrics
            fundamentals = {
                "symbol": symbol,
                "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "dividend_yield": info.get("dividendYield"),
                
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "operating_margin": info.get("operatingMargins"),
                "net_margin": info.get("profitMargins"),
                
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "week_52_high": info.get("fiftyTwoWeekHigh"),
                "week_52_low": info.get("fiftyTwoWeekLow"),
                
                "data_date": datetime.utcnow()
            }
            
            return fundamentals
            
        except Exception as e:
            self.logger.error(f"Failed to fetch fundamentals for {symbol}: {e}")
            return None
    
    def process_data(self, data: Dict[str, Dict[str, Any]], db: Session) -> Dict[str, int]:
        """
        Process and store fundamental data.
        
        Args:
            data: Fetched fundamental data
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
        
        for symbol, fundamentals in data.items():
            try:
                # Get or create stock
                stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                
                if not stock:
                    # Create new stock entry
                    stock = Stock(
                        symbol=symbol,
                        name=fundamentals.get("name", symbol),
                        exchange="NSE"
                    )
                    db.add(stock)
                    db.flush()  # Get stock ID
                    self.logger.info(f"Created new stock: {symbol}")
                
                # Create fundamental entry
                fundamental = Fundamental(
                    stock_id=stock.id,
                    pe_ratio=fundamentals.get("pe_ratio"),
                    pb_ratio=fundamentals.get("pb_ratio"),
                    ps_ratio=fundamentals.get("ps_ratio"),
                    dividend_yield=fundamentals.get("dividend_yield"),
                    roe=fundamentals.get("roe"),
                    roa=fundamentals.get("roa"),
                    operating_margin=fundamentals.get("operating_margin"),
                    net_margin=fundamentals.get("net_margin"),
                    debt_to_equity=fundamentals.get("debt_to_equity"),
                    current_ratio=fundamentals.get("current_ratio"),
                    quick_ratio=fundamentals.get("quick_ratio"),
                    revenue_growth=fundamentals.get("revenue_growth"),
                    earnings_growth=fundamentals.get("earnings_growth"),
                    current_price=fundamentals.get("current_price"),
                    week_52_high=fundamentals.get("week_52_high"),
                    week_52_low=fundamentals.get("week_52_low"),
                    data_date=fundamentals.get("data_date", datetime.utcnow())
                )
                
                db.add(fundamental)
                metrics["inserted"] += 1
                
                self.logger.info(f"Stored fundamental data for {symbol}")
                
            except Exception as e:
                self.logger.error(f"Failed to store data for {symbol}: {e}")
                metrics["skipped"] += 1
                continue
        
        db.commit()
        return metrics
