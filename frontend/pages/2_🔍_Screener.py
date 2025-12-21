"""
Screener Page - Filter and search stocks based on criteria.
"""
import streamlit as st
import pandas as pd
from utils.api_client import get_api_client
from utils.config import DEFAULT_FILTERS, get_score_color

st.set_page_config(page_title="Stock Screener", page_icon="🔍", layout="wide")

st.title("🔍 Stock Screener")
st.markdown("Filter stocks based on fundamental metrics and scores")
st.markdown("---")

# Initialize API client
client = get_api_client()

# Sidebar filters
with st.sidebar:
    st.header("Screening Filters")
    
    # PE Ratio
    st.subheader("PE Ratio")
    pe_min = st.number_input("Min PE", value=DEFAULT_FILTERS["pe_ratio_min"], min_value=0.0, max_value=100.0, step=1.0)
    pe_max = st.number_input("Max PE", value=DEFAULT_FILTERS["pe_ratio_max"], min_value=0.0, max_value=200.0, step=1.0)
    
    # PB Ratio
    st.subheader("PB Ratio")
    pb_min = st.number_input("Min PB", value=DEFAULT_FILTERS["pb_ratio_min"], min_value=0.0, max_value=20.0, step=0.1)
    pb_max = st.number_input("Max PB", value=DEFAULT_FILTERS["pb_ratio_max"], min_value=0.0, max_value=20.0, step=0.1)
    
    # ROE
    st.subheader("ROE (%)")
    roe_min = st.number_input("Min ROE", value=DEFAULT_FILTERS["roe_min"], min_value=0.0, max_value=100.0, step=1.0)
    roe_max = st.number_input("Max ROE", value=DEFAULT_FILTERS["roe_max"], min_value=0.0, max_value=100.0, step=1.0)
    
    # Debt to Equity
    st.subheader("Debt-to-Equity")
    debt_min = st.number_input("Min D/E", value=DEFAULT_FILTERS["debt_to_equity_min"], min_value=0.0, max_value=10.0, step=0.1)
    debt_max = st.number_input("Max D/E", value=DEFAULT_FILTERS["debt_to_equity_max"], min_value=0.0, max_value=10.0, step=0.1)
    
    # Composite Score
    st.subheader("Composite Score")
    score_min = st.slider("Minimum Score", min_value=0.0, max_value=100.0, value=DEFAULT_FILTERS["composite_score_min"], step=5.0)
    
    # Limit
    st.subheader("Results")
    limit = st.selectbox("Max Results", options=[10, 25, 50, 100], index=2)
    
    # Sort options
    sort_by = st.selectbox("Sort By", options=["composite_score", "fundamental_score", "sentiment_score", "pe_ratio", "roe"])
    sort_order = st.radio("Sort Order", options=["desc", "asc"], index=0)
    
    # Screen button
    screen_button = st.button("🔍 Screen Stocks", type="primary", use_container_width=True)
    
    # Reset button
    if st.button("🔄 Reset Filters", use_container_width=True):
        st.rerun()

# Main content
if screen_button:
    # Prepare filters
    filters = {
        "pe_ratio_min": pe_min if pe_min > 0 else None,
        "pe_ratio_max": pe_max if pe_max < 200 else None,
        "pb_ratio_min": pb_min if pb_min > 0 else None,
        "pb_ratio_max": pb_max if pb_max < 20 else None,
        "roe_min": roe_min if roe_min > 0 else None,
        "roe_max": roe_max if roe_max < 100 else None,
        "debt_to_equity_min": debt_min if debt_min > 0 else None,
        "debt_to_equity_max": debt_max if debt_max < 10 else None,
        "composite_score_min": score_min if score_min > 0 else None,
        "limit": limit,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    
    with st.spinner("Screening stocks..."):
        results = client.screen_stocks(filters)
    
    if results:
        st.success(f"Found {len(results)} stocks matching your criteria")
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(results)
        
        # Display results in a nice format
        for idx, stock in enumerate(results):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                st.markdown(f"### **{stock.get('symbol', 'N/A')}**")
                st.caption(stock.get('name', 'N/A'))
            
            with col2:
                composite = stock.get('composite_score', 0)
                st.metric(
                    "Composite Score",
                    f"{composite:.1f}",
                    delta=None,
                    delta_color="off"
                )
            
            with col3:
                pe = stock.get('pe_ratio', 0)
                roe = stock.get('roe', 0)
                st.metric("PE Ratio", f"{pe:.2f}")
                st.metric("ROE", f"{roe:.1f}%")
            
            with col4:
                fundamental = stock.get('fundamental_score', 0)
                sentiment = stock.get('sentiment_score', 0)
                st.metric("Fundamental", f"{fundamental:.1f}")
                st.metric("Sentiment", f"{sentiment:.1f}")
            
            if idx < len(results) - 1:
                st.divider()
        
        # Download button for CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name="screened_stocks.csv",
            mime="text/csv",
        )
    else:
        st.warning("No stocks found matching your criteria. Try adjusting your filters.")
else:
    st.info("👈 Use the sidebar to set your screening criteria and click 'Screen Stocks'")
    
    # Show some example stocks
    st.subheader("💡 Example: Top Stocks")
    with st.spinner("Loading top stocks..."):
        top_stocks = client.get_rankings("composite", limit=5)
    
    if top_stocks:
        for stock in top_stocks:
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"**{stock.get('symbol')}** - {stock.get('name', 'N/A')}")
            with col2:
                st.metric("Composite Score", f"{stock.get('composite_score', 0):.1f}")
            with col3:
                st.metric("PE Ratio", f"{stock.get('pe_ratio', 0):.2f}")
