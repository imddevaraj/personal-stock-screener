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
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with auth token if available."""
        headers = {"Content-Type": "application/json"}
        if "token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state['token']}"
        return headers

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user."""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return self._handle_response(response)

    def signup(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """Register new user."""
        response = self.session.post(
            f"{self.base_url}/auth/signup",
            json={"email": email, "password": password, "full_name": full_name}
        )
        return self._handle_response(response)

    def get_me(self) -> Dict[str, Any]:
        """Get current user details."""
        response = self.session.get(
            f"{self.base_url}/auth/me",
            headers=self._get_headers()
        )
        return self._handle_response(response)

    @st.cache_data(ttl=300)
    def get_health(_self) -> Dict[str, Any]:
        """Check API health status."""
        response = _self.session.get(f"{_self.base_url.replace('/api/v1', '')}/health")
        return _self._handle_response(response)
    
    @st.cache_data(ttl=60)
    def get_all_stocks(_self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all stocks with pagination."""
        response = _self.session.get(
            f"{_self.base_url}/stocks",
            params={"skip": skip, "limit": limit},
            headers=_self._get_headers()
        )
        result = _self._handle_response(response)
        return result if isinstance(result, list) else []
    
    @st.cache_data(ttl=60)
    def get_stock(_self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock information."""
        response = _self.session.get(
            f"{_self.base_url}/stocks/{symbol}",
            headers=_self._get_headers()
        )
        return _self._handle_response(response)
    
    def screen_stocks(_self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Screen stocks with filters."""
        # Remove None values
        clean_filters = {k: v for k, v in filters.items() if v is not None}
        
        response = _self.session.post(
            f"{_self.base_url}/screen",
            json=clean_filters,
            headers=_self._get_headers()
        )
        result = _self._handle_response(response)
        return result if isinstance(result, list) else []
    
    @st.cache_data(ttl=60)
    def get_rankings(_self, ranking_type: str = "composite", limit: int = 10) -> List[Dict[str, Any]]:
        """Get stock rankings by type (composite, fundamental, sentiment)."""
        response = _self.session.get(
            f"{_self.base_url}/screen/rankings/{ranking_type}",
            params={"limit": limit},
            headers=_self._get_headers()
        )
        result = _self._handle_response(response)
        return result if isinstance(result, list) else []

    @st.cache_data(ttl=300)
    def get_stock_sentiment(_self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent sentiment scores with news details."""
        response = _self.session.get(
            f"{_self.base_url}/stocks/{symbol}/sentiment",
            params={"limit": limit},
            headers=_self._get_headers()
        )
        result = _self._handle_response(response)
        return result if isinstance(result, list) else []


# Singleton instance - NOT cached to handle session state correctly
def get_api_client() -> APIClient:
    """Get API client instance."""
    return APIClient()
