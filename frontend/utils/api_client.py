"""
API Client for communicating with the backend.
"""
import requests
import streamlit as st
from typing import Dict, List, Optional, Any
from utils.config import API_BASE_URL


class APIClient:
    """Client for backend API interactions."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            st.error(f"API Error: {e}")
            return {}
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend API. Is it running?")
            return {}
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return {}
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_health(_self) -> Dict[str, Any]:
        """Check API health status."""
        response = _self.session.get(f"{_self.base_url.replace('/api/v1', '')}/health")
        return _self._handle_response(response)
    
    @st.cache_data(ttl=60)  # Cache for 1 minute
    def get_all_stocks(_self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all stocks with pagination."""
        response = _self.session.get(
            f"{_self.base_url}/stocks",
            params={"skip": skip, "limit": limit}
        )
        result = _self._handle_response(response)
        return result if isinstance(result, list) else []
    
    @st.cache_data(ttl=60)
    def get_stock(_self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock information."""
        response = _self.session.get(f"{_self.base_url}/stocks/{symbol}")
        return _self._handle_response(response)
    
    def screen_stocks(_self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Screen stocks with filters."""
        # Remove None values
        clean_filters = {k: v for k, v in filters.items() if v is not None}
        
        response = _self.session.post(
            f"{_self.base_url}/screen",
            json=clean_filters
        )
        result = _self._handle_response(response)
        return result if isinstance(result, list) else []
    
    @st.cache_data(ttl=60)
    def get_rankings(_self, ranking_type: str = "composite", limit: int = 10) -> List[Dict[str, Any]]:
        """Get stock rankings by type (composite, fundamental, sentiment)."""
        response = _self.session.get(
            f"{_self.base_url}/screen/rankings/{ranking_type}",
            params={"limit": limit}
        )
        result = _self._handle_response(response)
        return result if isinstance(result, list) else []


# Singleton instance
@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance."""
    return APIClient()
