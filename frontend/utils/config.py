"""
Configuration management for the frontend application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_VERSION = "v1"
API_BASE_URL = f"{API_URL}/api/{API_VERSION}"

# App Configuration
APP_TITLE = "Personal Stock Screener"
APP_ICON = "📊"

# Default Filter Values
DEFAULT_FILTERS = {
    "pe_ratio_max": 50.0,
    "pe_ratio_min": 0.0,
    "pb_ratio_max": 10.0,
    "pb_ratio_min": 0.0,
    "roe_min": 0.0,
    "roe_max": 100.0,
    "debt_to_equity_max": 5.0,
    "debt_to_equity_min": 0.0,
    "composite_score_min": 0.0,
    "composite_score_max": 100.0,
    "limit": 50,
}

# Score Color Thresholds
SCORE_COLORS = {
    "excellent": {"min": 80, "color": "#10b981"},  # green
    "good": {"min": 60, "color": "#3b82f6"},       # blue
    "fair": {"min": 40, "color": "#f59e0b"},       # orange
    "poor": {"min": 0, "color": "#ef4444"},        # red
}

def get_score_color(score: float) -> str:
    """Get color based on score value."""
    if score >= SCORE_COLORS["excellent"]["min"]:
        return SCORE_COLORS["excellent"]["color"]
    elif score >= SCORE_COLORS["good"]["min"]:
        return SCORE_COLORS["good"]["color"]
    elif score >= SCORE_COLORS["fair"]["min"]:
        return SCORE_COLORS["fair"]["color"]
    else:
        return SCORE_COLORS["poor"]["color"]
