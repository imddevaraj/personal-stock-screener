"""
Home Page - Dashboard with overview and top performers.
"""
import streamlit as st
import pandas as pd
from utils.api_client import get_api_client
from utils.config import get_score_color

st.set_page_config(page_title="Home Dashboard", page_icon="🏠", layout="wide")

st.title("🏠 Dashboard")
st.markdown("Overview of stock screening system and top performers")
st.markdown("---")

# Initialize API client
client = get_api_client()

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Backend Status",
        value="Healthy ✅",
        delta="Connected"
    )

with col2:
    # Get total stocks count
    stocks = client.get_all_stocks(limit=500)
    st.metric(
        label="Total Stocks",
        value=len(stocks) if stocks else 0,
        delta="Tracked"
    )

with col3:
    # Calculate average composite score
    if stocks:
        avg_score = sum(s.get('composite_score', 0) for s in stocks) / len(stocks)
        st.metric(
            label="Avg Composite Score",
            value=f"{avg_score:.1f}",
            delta=None
        )
    else:
        st.metric("Avg Composite Score", "N/A")

with col4:
    st.metric(
        label="Data Sources",
        value="2",
        delta="Fundamentals + Sentiment"
    )

st.markdown("---")

# Top Performers Section
st.header("🏆 Top Performers")

tab1, tab2, tab3 = st.tabs(["📊 Composite Score", "📈 Fundamentals", "💬 Sentiment"])

with tab1:
    st.subheader("Top 10 by Composite Score")
    with st.spinner("Loading top stocks..."):
        top_composite = client.get_rankings("composite", limit=10)
    
    if top_composite:
        # Create DataFrame
        df = pd.DataFrame(top_composite)
        
        # Display as cards
        for idx, stock in enumerate(top_composite, 1):
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
            
            with col1:
                st.markdown(f"### #{idx}")
            
            with col2:
                st.markdown(f"**{stock.get('symbol')}**")
                st.caption(stock.get('name', 'N/A'))
            
            with col3:
                score = stock.get('composite_score', 0)
                color = get_score_color(score)
                st.markdown(f"<span style='color: {color}; font-size: 1.5rem; font-weight: bold;'>{score:.1f}</span>", unsafe_allow_html=True)
                st.caption("Composite")
            
            with col4:
                st.metric("PE Ratio", f"{stock.get('pe_ratio', 0):.2f}")
            
            with col5:
                st.metric("ROE", f"{stock.get('roe', 0):.1f}%")
            
            st.divider()
    else:
        st.info("No data available. Run the data ingestion pipeline first.")

with tab2:
    st.subheader("Top 10 by Fundamental Score")
    with st.spinner("Loading..."):
        top_fundamental = client.get_rankings("fundamental", limit=10)
    
    if top_fundamental:
        for idx, stock in enumerate(top_fundamental, 1):
            col1, col2, col3 = st.columns([1, 4, 2])
            
            with col1:
                st.markdown(f"### #{idx}")
            
            with col2:
                st.markdown(f"**{stock.get('symbol')}** - {stock.get('name', 'N/A')}")
            
            with col3:
                score = stock.get('fundamental_score', 0)
                color = get_score_color(score)
                st.markdown(f"<span style='color: {color}; font-size: 1.3rem; font-weight: bold;'>{score:.1f}</span>", unsafe_allow_html=True)
            
            st.divider()
    else:
        st.info("No fundamental data available.")

with tab3:
    st.subheader("Top 10 by Sentiment Score")
    with st.spinner("Loading..."):
        top_sentiment = client.get_rankings("sentiment", limit=10)
    
    if top_sentiment:
        for idx, stock in enumerate(top_sentiment, 1):
            col1, col2, col3 = st.columns([1, 4, 2])
            
            with col1:
                st.markdown(f"### #{idx}")
            
            with col2:
                st.markdown(f"**{stock.get('symbol')}** - {stock.get('name', 'N/A')}")
            
            with col3:
                score = stock.get('sentiment_score', 0)
                color = get_score_color(score)
                st.markdown(f"<span style='color: {color}; font-size: 1.3rem; font-weight: bold;'>{score:.1f}</span>", unsafe_allow_html=True)
            
            st.divider()
    else:
        st.info("No sentiment data available.")

st.markdown("---")

# Quick actions
st.header("⚡ Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Go to Screener", use_container_width=True):
        st.switch_page("pages/2_🔍_Screener.py")

with col2:
    if st.button("📊 View Stock Details", use_container_width=True):
        st.switch_page("pages/3_📊_Stock_Details.py")

with col3:
    if st.button("📈 View Rankings", use_container_width=True):
        st.switch_page("pages/4_📈_Rankings.py")
