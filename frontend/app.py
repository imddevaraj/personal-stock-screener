"""
Personal Stock Screener - Main Application
A Streamlit app for screening Indian stocks based on fundamentals and sentiment.
"""
import streamlit as st
from utils.config import APP_TITLE, APP_ICON

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #262730;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stock-card {
        background-color: #262730;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .stock-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    h1 {
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# Main page content
st.title(f"{APP_ICON} {APP_TITLE}")
st.markdown("---")

# Welcome message
st.markdown("""
### Welcome to Personal Stock Screener! 👋

A powerful tool for screening Indian equities using:
- **Fundamental Analysis**: PE ratio, ROE, debt ratios, and more
- **Sentiment Analysis**: ML-powered analysis of news articles
- **Composite Scoring**: Weighted scores combining both approaches

#### 🔍 Getting Started:
1. **Screener** - Filter stocks based on your criteria
2. **Stock Details** - Deep dive into individual stocks
3. **Rankings** - View top performers across different metrics

Use the sidebar to navigate between pages.
""")

st.markdown("---")

# Quick stats and status check
col1, col2, col3 = st.columns(3)

with col1:
    with st.spinner("Checking API status..."):
        from utils.api_client import get_api_client
        client = get_api_client()
        health = client.get_health()
        
        if health.get("status") == "healthy":
            st.success("✅ Backend is healthy")
            st.metric("Database", health.get("database", "unknown").upper())
            st.metric("Redis", health.get("redis", "unknown").upper())
        else:
            st.error("❌ Backend is unhealthy")
            st.info("Make sure the backend service is running on port 8000")

with col2:
    st.info("📊 **Features**")
    st.markdown("""
    - Interactive filters
    - Real-time screening
    - Score breakdowns
    - Export capabilities
    """)

with col3:
    st.info("🎯 **Metrics Tracked**")
    st.markdown("""
    - PE Ratio
    - ROE (Return on Equity)
    - Debt-to-Equity
    - Sentiment Score
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    Built with ❤️ using Streamlit and FastAPI | 
    <a href='http://localhost:8000/docs' target='_blank'>API Documentation</a>
</div>
""", unsafe_allow_html=True)
