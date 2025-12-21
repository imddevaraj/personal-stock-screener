"""
Stock Details Page - Deep dive into individual stock analysis.
"""
import streamlit as st
import plotly.graph_objects as go
from utils.api_client import get_api_client
from utils.config import get_score_color

st.set_page_config(page_title="Stock Details", page_icon="📊", layout="wide")

st.title("📊 Stock Details")
st.markdown("Detailed analysis of individual stocks")
st.markdown("---")

# Initialize API client
client = get_api_client()

# Stock selector
stocks = client.get_all_stocks(limit=1000)
if stocks:
    stock_symbols = sorted([s.get('symbol') for s in stocks if s.get('symbol')])
    selected_symbol = st.selectbox(
        "Select a stock",
        options=stock_symbols,
        index=0 if stock_symbols else None
    )
    
    if selected_symbol:
        with st.spinner(f"Loading {selected_symbol} details..."):
            stock_data = client.get_stock(selected_symbol)
        
        if stock_data:
            # Header section
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.header(f"{stock_data.get('symbol')} - {stock_data.get('name', 'N/A')}")
            
            with col2:
                composite_score = stock_data.get('composite_score', 0)
                color = get_score_color(composite_score)
                st.markdown(f"""
                    <div style='text-align: center; padding: 1rem; background-color: #262730; border-radius: 0.5rem;'>
                        <div style='color: #888; font-size: 0.9rem;'>COMPOSITE SCORE</div>
                        <div style='color: {color}; font-size: 3rem; font-weight: bold;'>{composite_score:.1f}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Score Breakdown
            st.subheader("📈 Score Breakdown")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fundamental = stock_data.get('fundamental_score', 0)
                st.metric(
                    "Fundamental Score",
                    f"{fundamental:.1f}",
                    delta=None
                )
                
                # Gauge chart for fundamental
                fig_fund = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=fundamental,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Fundamental"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': get_score_color(fundamental)},
                        'steps': [
                            {'range': [0, 40], 'color': '#1a1a2e'},
                            {'range': [40, 60], 'color': '#16213e'},
                            {'range': [60, 80], 'color': '#0f3460'},
                            {'range': [80, 100], 'color': '#0a1929'}
                        ],
                    }
                ))
                fig_fund.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_fund, use_container_width=True)
            
            with col2:
                sentiment = stock_data.get('sentiment_score', 0)
                st.metric(
                    "Sentiment Score",
                    f"{sentiment:.1f}",
                    delta=None
                )
                
                # Gauge chart for sentiment
                fig_sent = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=sentiment,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Sentiment"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': get_score_color(sentiment)},
                        'steps': [
                            {'range': [0, 40], 'color': '#1a1a2e'},
                            {'range': [40, 60], 'color': '#16213e'},
                            {'range': [60, 80], 'color': '#0f3460'},
                            {'range': [80, 100], 'color': '#0a1929'}
                        ],
                    }
                ))
                fig_sent.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_sent, use_container_width=True)
            
            with col3:
                st.metric(
                    "Composite Score",
                    f"{composite_score:.1f}",
                    delta=None
                )
                
                # Gauge chart for composite
                fig_comp = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=composite_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Composite"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': get_score_color(composite_score)},
                        'steps': [
                            {'range': [0, 40], 'color': '#1a1a2e'},
                            {'range': [40, 60], 'color': '#16213e'},
                            {'range': [60, 80], 'color': '#0f3460'},
                            {'range': [80, 100], 'color': '#0a1929'}
                        ],
                    }
                ))
                fig_comp.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_comp, use_container_width=True)
            
            st.markdown("---")
            
            # Fundamental Metrics
            st.subheader("📊 Fundamental Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("PE Ratio", f"{stock_data.get('pe_ratio', 0):.2f}")
                st.metric("PB Ratio", f"{stock_data.get('pb_ratio', 0):.2f}")
            
            with col2:
                st.metric("ROE", f"{stock_data.get('roe', 0):.1f}%")
                st.metric("ROCE", f"{stock_data.get('roce', 0):.1f}%")
            
            with col3:
                st.metric("Debt-to-Equity", f"{stock_data.get('debt_to_equity', 0):.2f}")
                st.metric("Current Ratio", f"{stock_data.get('current_ratio', 0):.2f}")
            
            with col4:
                st.metric("Revenue Growth", f"{stock_data.get('revenue_growth_3y', 0):.1f}%")
                st.metric("Profit Growth", f"{stock_data.get('profit_growth_3y', 0):.1f}%")
            
            st.markdown("---")
            
            # Sentiment Details
            st.subheader("💬 Sentiment Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Sentiment Score", f"{sentiment:.1f}/100")
                st.caption("Based on recent news article analysis using FinBERT")
            
            with col2:
                # Sentiment bar chart
                sentiment_label = "Positive" if sentiment >= 60 else "Neutral" if sentiment >= 40 else "Negative"
                sentiment_color = get_score_color(sentiment)
                
                st.markdown(f"""
                    <div style='padding: 1rem; background-color: #262730; border-radius: 0.5rem;'>
                        <div>Overall Sentiment: <span style='color: {sentiment_color}; font-weight: bold;'>{sentiment_label}</span></div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Score Explanation
            with st.expander("ℹ️ How are scores calculated?"):
                st.markdown("""
                **Composite Score** is a weighted combination of:
                - **Fundamental Score (60%)**: Based on PE ratio, ROE, debt ratios, growth metrics
                - **Sentiment Score (40%)**: ML-powered sentiment analysis of news articles
                
                **Scoring Ranges**:
                - 🟢 80-100: Excellent
                - 🔵 60-79: Good
                - 🟡 40-59: Fair
                - 🔴 0-39: Poor
                """)
        else:
            st.error(f"Could not load data for {selected_symbol}")
else:
    st.warning("No stocks available. Please run the data ingestion pipeline first.")
    st.info("Backend endpoint: http://localhost:8000/api/v1/stocks")
