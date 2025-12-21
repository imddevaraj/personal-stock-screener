"""
Rankings Page - View top stocks by different metrics.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api_client import get_api_client
from utils.config import get_score_color

st.set_page_config(page_title="Rankings", page_icon="📈", layout="wide")

st.title("📈 Stock Rankings")
st.markdown("Top performing stocks across different metrics")
st.markdown("---")

# Initialize API client
client = get_api_client()

# Sidebar controls
with st.sidebar:
    st.header("Ranking Options")
    
    ranking_type = st.selectbox(
        "Ranking Type",
        options=["composite", "fundamental", "sentiment"],
        format_func=lambda x: x.capitalize()
    )
    
    limit = st.slider("Number of Stocks", min_value=5, max_value=50, value=20, step=5)

# Fetch rankings
with st.spinner(f"Loading top {limit} stocks by {ranking_type}..."):
    rankings = client.get_rankings(ranking_type, limit=limit)

if rankings:
    # Create DataFrame
    df = pd.DataFrame(rankings)
    
    # Main metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Ranked", len(rankings))
    
    with col2:
        avg_score = df[f'{ranking_type}_score'].mean()
        st.metric(f"Average {ranking_type.capitalize()} Score", f"{avg_score:.1f}")
    
    with col3:
        top_score = df[f'{ranking_type}_score'].max()
        st.metric("Top Score", f"{top_score:.1f}")
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 List View", "📊 Chart View", "📄 Table View"])
    
    with tab1:
        st.subheader(f"Top {limit} by {ranking_type.capitalize()} Score")
        
        for idx, stock in enumerate(rankings, 1):
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
            
            with col1:
                # Rank badge
                if idx == 1:
                    st.markdown("### 🥇")
                elif idx == 2:
                    st.markdown("### 🥈")
                elif idx == 3:
                    st.markdown("### 🥉")
                else:
                    st.markdown(f"### #{idx}")
            
            with col2:
                st.markdown(f"**{stock.get('symbol')}**")
                st.caption(stock.get('name', 'N/A'))
            
            with col3:
                score = stock.get(f'{ranking_type}_score', 0)
                color = get_score_color(score)
                st.markdown(f"<div style='font-size: 1.5rem; color: {color}; font-weight: bold;'>{score:.1f}</div>", unsafe_allow_html=True)
                st.caption(f"{ranking_type.capitalize()} Score")
            
            with col4:
                st.metric("PE Ratio", f"{stock.get('pe_ratio', 0):.2f}")
                st.metric("ROE", f"{stock.get('roe', 0):.1f}%")
            
            with col5:
                st.metric("Composite", f"{stock.get('composite_score', 0):.1f}")
                if ranking_type != "fundamental":
                    st.metric("Fundamental", f"{stock.get('fundamental_score', 0):.1f}")
                if ranking_type != "sentiment":
                    st.metric("Sentiment", f"{stock.get('sentiment_score', 0):.1f}")
            
            st.divider()
    
    with tab2:
        st.subheader("Score Distribution")
        
        # Bar chart of scores
        fig = px.bar(
            df.head(20),
            x='symbol',
            y=f'{ranking_type}_score',
            color=f'{ranking_type}_score',
            color_continuous_scale=['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
            labels={f'{ranking_type}_score': f'{ranking_type.capitalize()} Score', 'symbol': 'Stock Symbol'},
            title=f'Top 20 Stocks by {ranking_type.capitalize()} Score'
        )
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Scatter plot: Composite vs Fundamental vs Sentiment
        st.subheader("Score Comparison")
        
        if ranking_type == "composite":
            fig2 = px.scatter(
                df.head(20),
                x='fundamental_score',
                y='sentiment_score',
                size='composite_score',
                color='composite_score',
                hover_data=['symbol', 'name'],
                labels={
                    'fundamental_score': 'Fundamental Score',
                    'sentiment_score': 'Sentiment Score',
                    'composite_score': 'Composite Score'
                },
                title='Fundamental vs Sentiment (sized by Composite Score)',
                color_continuous_scale=['#ef4444', '#f59e0b', '#3b82f6', '#10b981']
            )
            fig2.update_layout(height=500)
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        st.subheader("Detailed Rankings Table")
        
        # Prepare display dataframe
        display_df = df[[
            'symbol', 'name', f'{ranking_type}_score',
            'pe_ratio', 'pb_ratio', 'roe', 'debt_to_equity',
            'composite_score', 'fundamental_score', 'sentiment_score'
        ]].copy()
        
        # Round numeric columns
        numeric_cols = display_df.select_dtypes(include=['float64']).columns
        display_df[numeric_cols] = display_df[numeric_cols].round(2)
        
        # Display table
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600
        )
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {ranking_type.capitalize()} Rankings (CSV)",
            data=csv,
            file_name=f"{ranking_type}_rankings.csv",
            mime="text/csv",
        )

else:
    st.warning("No ranking data available. Please run the data pipeline first.")
    st.info("Make sure you have:")
    st.code("""
    1. Ingested fundamental data
    2. Ingested news data  
    3. Analyzed sentiment
    4. Computed scores
    """)
