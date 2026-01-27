"""
News Page - Display Intelligence Dashboard
Industry news, market updates, and media monitoring.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import get_css, get_plotly_theme
from utils.database import DatabaseManager
from utils.exports import create_download_buttons

# Page config
st.set_page_config(
    page_title="News - Display Intelligence",
    page_icon="📰",
    layout="wide"
)

# Apply styling
st.markdown(get_css(), unsafe_allow_html=True)

# Check authentication
if not st.session_state.get("password_correct", False):
    st.warning("Please login from the main page.")
    st.stop()

# Page header
st.markdown("""
    <h1>📰 Industry News</h1>
    <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
        Latest updates, market news, and industry developments
    </p>
""", unsafe_allow_html=True)

# Filters in sidebar
with st.sidebar:
    st.markdown("### Filters")

    # News categories
    category_options = ["All", "Capacity", "Technology", "Financial", "M&A", "Supply Chain", "Product Launch"]
    category = st.selectbox(
        "Category",
        options=category_options,
        key="news_category"
    )

    # Impact level
    impact_options = ["All", "High", "Medium", "Low"]
    impact = st.selectbox(
        "Impact Level",
        options=impact_options,
        key="news_impact"
    )

    st.divider()

    # Date range
    st.markdown("### Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start",
            value=date.today() - timedelta(days=90),
            key="news_start"
        )
    with col2:
        end_date = st.date_input(
            "End",
            value=date.today(),
            key="news_end"
        )

    # Search
    st.divider()
    search_query = st.text_input(
        "Search",
        placeholder="Search news...",
        key="news_search"
    )

# Load news data
news_df = DatabaseManager.get_news(
    start_date=start_date.strftime("%Y-%m-%d"),
    end_date=end_date.strftime("%Y-%m-%d"),
    category=category,
    impact_level=impact
)

theme = get_plotly_theme()

# Main content
if len(news_df) > 0:
    # Apply search filter if provided
    if search_query:
        mask = (
            news_df['title'].str.contains(search_query, case=False, na=False) |
            news_df['content'].str.contains(search_query, case=False, na=False) |
            news_df['summary'].str.contains(search_query, case=False, na=False)
        )
        news_df = news_df[mask]

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Articles", len(news_df))

    with col2:
        high_impact = len(news_df[news_df['impact_level'] == 'High'])
        st.metric("High Impact", high_impact)

    with col3:
        unique_sources = news_df['source'].nunique()
        st.metric("Sources", unique_sources)

    with col4:
        # Recent 7 days
        recent_mask = pd.to_datetime(news_df['published_date']) >= (datetime.now() - timedelta(days=7))
        recent_count = len(news_df[recent_mask])
        st.metric("Last 7 Days", recent_count)

    st.divider()

    # News feed
    st.markdown("### Latest News")

    for idx, row in news_df.head(20).iterrows():
        # Determine impact badge color
        impact_color = {
            'High': '#FF3B30',
            'Medium': '#FF9500',
            'Low': '#34C759'
        }.get(row.get('impact_level', 'Low'), '#86868B')

        category_str = row.get('category', 'General')
        impact_str = row.get('impact_level', 'Low')
        pub_date = row.get('published_date', '')
        if pub_date:
            try:
                pub_date = datetime.strptime(str(pub_date)[:10], '%Y-%m-%d').strftime('%B %d, %Y')
            except:
                pub_date = str(pub_date)[:10]

        st.markdown(f"""
        <div style="
            background: white;
            border: 1px solid #E5E5E7;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: box-shadow 0.2s ease;
        ">
            <div style="display: flex; gap: 0.5rem; margin-bottom: 0.75rem;">
                <span style="
                    background: {impact_color}15;
                    color: {impact_color};
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-weight: 500;
                ">{impact_str} Impact</span>
                <span style="
                    background: #F5F5F7;
                    color: #86868B;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.75rem;
                ">{category_str}</span>
            </div>
            <h3 style="
                font-size: 1.1rem;
                font-weight: 600;
                color: #1D1D1F;
                margin-bottom: 0.5rem;
                line-height: 1.4;
            ">{row.get('title', 'Untitled')}</h3>
            <p style="
                color: #86868B;
                font-size: 0.9rem;
                line-height: 1.6;
                margin-bottom: 0.75rem;
            ">{row.get('summary', row.get('content', 'No summary available.'))[:300]}{'...' if len(str(row.get('summary', row.get('content', '')))) > 300 else ''}</p>
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding-top: 0.75rem;
                border-top: 1px solid #F5F5F7;
            ">
                <span style="color: #86868B; font-size: 0.8rem;">{row.get('source', 'Unknown source')}</span>
                <span style="color: #86868B; font-size: 0.8rem;">{pub_date}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Export
    st.divider()
    create_download_buttons(news_df, "news", "News Intelligence Report")

else:
    # Empty state
    st.markdown("""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: #F5F5F7;
        border-radius: 20px;
        margin-top: 2rem;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📰</div>
        <h2 style="color: #1D1D1F; margin-bottom: 0.5rem;">No News Articles Yet</h2>
        <p style="color: #86868B; max-width: 400px; margin: 0 auto;">
            News articles will appear here as they are added to the database.
            Check back later for the latest industry updates.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Sample news cards to show layout
    st.divider()
    st.markdown("### Sample News Layout")
    st.info("The following are placeholder examples showing how news will be displayed:")

    sample_news = [
        {
            'title': 'BOE Expands OLED Production Capacity in China',
            'summary': 'BOE Technology Group announced plans to expand its OLED production capacity with a new Gen 8.6 line expected to begin mass production in 2025.',
            'category': 'Capacity',
            'impact': 'High',
            'source': 'Display Daily',
            'date': 'January 15, 2024'
        },
        {
            'title': 'Samsung Display Invests in QD-OLED Technology',
            'summary': 'Samsung Display continues to invest in quantum dot OLED technology, targeting premium TV and monitor markets with enhanced color accuracy.',
            'category': 'Technology',
            'impact': 'Medium',
            'source': 'Tech Report',
            'date': 'January 12, 2024'
        },
        {
            'title': 'LG Display Posts Quarterly Profit Recovery',
            'summary': 'LG Display reports improved financial results driven by OLED TV panel demand and strategic cost reductions across its LCD operations.',
            'category': 'Financial',
            'impact': 'Medium',
            'source': 'Reuters',
            'date': 'January 10, 2024'
        }
    ]

    for news in sample_news:
        impact_color = {'High': '#FF3B30', 'Medium': '#FF9500', 'Low': '#34C759'}.get(news['impact'], '#86868B')

        st.markdown(f"""
        <div style="
            background: white;
            border: 1px solid #E5E5E7;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            opacity: 0.6;
        ">
            <div style="display: flex; gap: 0.5rem; margin-bottom: 0.75rem;">
                <span style="
                    background: {impact_color}15;
                    color: {impact_color};
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-weight: 500;
                ">{news['impact']} Impact</span>
                <span style="
                    background: #F5F5F7;
                    color: #86868B;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.75rem;
                ">{news['category']}</span>
            </div>
            <h3 style="
                font-size: 1.1rem;
                font-weight: 600;
                color: #1D1D1F;
                margin-bottom: 0.5rem;
            ">{news['title']}</h3>
            <p style="
                color: #86868B;
                font-size: 0.9rem;
                line-height: 1.6;
                margin-bottom: 0.75rem;
            ">{news['summary']}</p>
            <div style="
                display: flex;
                justify-content: space-between;
                padding-top: 0.75rem;
                border-top: 1px solid #F5F5F7;
            ">
                <span style="color: #86868B; font-size: 0.8rem;">{news['source']}</span>
                <span style="color: #86868B; font-size: 0.8rem;">{news['date']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
