"""
Pydantic schemas for API request/response validation.
Updated for Pydantic v2.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# Stock Schemas
# ============================================================================

class StockBase(BaseModel):
    """Base stock schema."""
    symbol: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    sector: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    market_cap: Optional[float] = None
    exchange: str = Field(default="NSE", max_length=10)


class StockCreate(StockBase):
    """Schema for creating a stock."""
    pass


class StockResponse(StockBase):
    """Schema for stock API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Fundamental Schemas
# ============================================================================

class FundamentalBase(BaseModel):
    """Base fundamental schema."""
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    current_price: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    data_date: datetime


class FundamentalCreate(FundamentalBase):
    """Schema for creating fundamental data."""
    stock_id: int


class FundamentalResponse(FundamentalBase):
    """Schema for fundamental API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    stock_id: int
    created_at: datetime


# ============================================================================
# News Schemas
# ============================================================================

class NewsBase(BaseModel):
    """Base news schema."""
    title: str = Field(..., max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = None
    url: str = Field(..., max_length=1000)
    source: Optional[str] = Field(None, max_length=100)
    author: Optional[str] = Field(None, max_length=200)
    published_at: datetime


class NewsCreate(NewsBase):
    """Schema for creating news."""
    content_hash: str = Field(..., max_length=64)
    stock_symbols: List[str] = []


class NewsResponse(NewsBase):
    """Schema for news API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    fetched_at: datetime


# ============================================================================
# Sentiment Schemas
# ============================================================================

class SentimentScoreBase(BaseModel):
    """Base sentiment score schema."""
    sentiment_label: str = Field(..., max_length=20)
    sentiment_score: float = Field(..., ge=-1, le=1)
    confidence: Optional[float] = Field(None, ge=0, le=1)


class SentimentScoreCreate(SentimentScoreBase):
    """Schema for creating sentiment score."""
    news_id: int
    stock_id: int
    model_name: Optional[str] = Field(None, max_length=100)
    model_version: Optional[str] = Field(None, max_length=50)


class SentimentScoreResponse(SentimentScoreBase):
    """Schema for sentiment score API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    news_id: int
    stock_id: int
    model_name: Optional[str] = None
    created_at: datetime


# ============================================================================
# Composite Score Schemas
# ============================================================================

class CompositeScoreBase(BaseModel):
    """Base composite score schema."""
    fundamental_score: float = Field(..., ge=0, le=100)
    sentiment_score: float = Field(..., ge=0, le=100)
    composite_score: float = Field(..., ge=0, le=100)
    rank: Optional[int] = None
    score_breakdown: Optional[Dict[str, Any]] = None


class CompositeScoreCreate(CompositeScoreBase):
    """Schema for creating composite score."""
    stock_id: int
    score_date: datetime


class CompositeScoreResponse(CompositeScoreBase):
    """Schema for composite score API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    stock_id: int
    score_date: datetime
    created_at: datetime


class StockWithScore(BaseModel):
    """Stock information with latest composite score."""
    model_config = ConfigDict(from_attributes=True)
    
    stock: StockResponse
    latest_score: Optional[CompositeScoreResponse] = None
    latest_fundamental: Optional[FundamentalResponse] = None


# ============================================================================
# Alert Schemas
# ============================================================================

class AlertBase(BaseModel):
    """Base alert schema."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    alert_type: str = Field(..., max_length=50)
    conditions: Dict[str, Any]
    stock_symbols: Optional[List[str]] = None
    notification_channels: Optional[List[str]] = None
    notification_config: Optional[Dict[str, Any]] = None


class AlertCreate(AlertBase):
    """Schema for creating alert."""
    is_active: bool = True


class AlertUpdate(BaseModel):
    """Schema for updating alert."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    stock_symbols: Optional[List[str]] = None
    notification_channels: Optional[List[str]] = None
    notification_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AlertResponse(AlertBase):
    """Schema for alert API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Screening Schemas
# ============================================================================

class ScreeningFilters(BaseModel):
    """Filters for stock screening."""
    sectors: Optional[List[str]] = None
    
    # Fundamental filters
    pe_ratio_min: Optional[float] = None
    pe_ratio_max: Optional[float] = None
    pb_ratio_min: Optional[float] = None
    pb_ratio_max: Optional[float] = None
    roe_min: Optional[float] = None
    debt_to_equity_max: Optional[float] = None
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    
    # Score filters
    fundamental_score_min: Optional[float] = Field(None, ge=0, le=100)
    sentiment_score_min: Optional[float] = Field(None, ge=0, le=100)
    composite_score_min: Optional[float] = Field(None, ge=0, le=100)
    
    # Pagination
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    
    # Sorting
    sort_by: str = Field(default="composite_score")
    sort_order: str = Field(default="desc")
    
    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v


class ScreeningResponse(BaseModel):
    """Response for stock screening."""
    total_count: int
    results: List[StockWithScore]
    filters_applied: ScreeningFilters


# ============================================================================
# Health & Status Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    database: str
    redis: str


class IngestionStatusResponse(BaseModel):
    """Ingestion status response."""
    ingestion_type: str
    last_successful_run: Optional[datetime] = None
    last_run_status: Optional[str] = None
    next_scheduled_run: Optional[datetime] = None
