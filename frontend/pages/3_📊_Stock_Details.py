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
stocks = client.get_all_stocks(limit=500)
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
            # Parse nested response
            stock_info = stock_data.get('stock', {})
            latest_score = stock_data.get('latest_score', {}) or {}
            fundamentals = stock_data.get('latest_fundamental', {}) or {}
            
            # Header section
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.header(f"{stock_info.get('symbol')} - {stock_info.get('name', 'N/A')}")
            
            with col2:
                composite_score = latest_score.get('composite_score') or 0
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
                fundamental = latest_score.get('fundamental_score') or 0
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
                sentiment = latest_score.get('sentiment_score') or 0
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
                st.metric("PE Ratio", f"{fundamentals.get('pe_ratio') or 0:.2f}")
                st.metric("PB Ratio", f"{fundamentals.get('pb_ratio') or 0:.2f}")
            
            with col2:
                st.metric("ROE", f"{fundamentals.get('roe') or 0:.1f}%")
                st.metric("ROCE", f"{fundamentals.get('roce') or 0:.1f}%")
            
            with col3:
                st.metric("Debt-to-Equity", f"{fundamentals.get('debt_to_equity') or 0:.2f}")
                st.metric("Current Ratio", f"{fundamentals.get('current_ratio') or 0:.2f}")
            
            with col4:
                st.metric("Revenue Growth", f"{fundamentals.get('revenue_growth') or 0:.1f}%")
                st.metric("Earnings Growth", f"{fundamentals.get('earnings_growth') or 0:.1f}%")
            
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

            # Latest News & Sentiment
            st.subheader("📰 Latest News & Sentiment")
            
            # Fetch recent sentiment data
            news_sentiments = client.get_stock_sentiment(selected_symbol)
            
            if news_sentiments:
                for item in news_sentiments:
                    news = item.get('news', {})
                    if not news:
                        continue
                        
                    s_score = item.get('sentiment_score', 0)
                    s_label = item.get('sentiment_label', 'neutral')
                    
                    # Sentiment icon
                    icon = "🟢" if s_score >= 0.2 else "🔴" if s_score <= -0.2 else "⚪"
                    color = get_score_color((s_score + 1) * 50)  # Map -1..1 to 0..100
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="padding: 1rem; background-color: #1E1E1E; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 5px solid {color}">
                            <div style="font-size: 1.1rem; font-weight: bold;">
                                <a href="{news.get('url', '#')}" target="_blank" style="text-decoration: none; color: white;">
                                    {icon} {news.get('title', 'No Title')}
                                </a>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.8rem; color: #888;">
                                <span>{news.get('source', 'Unknown Source')} • {news.get('published_at', '')[:10]}</span>
                                <span>Sentiment: {s_label.upper()} ({s_score:.2f})</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No recent news articles found for this stock.")
            
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
