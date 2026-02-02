"""
News Page - Display Intelligence Dashboard
Industry news, market updates, and media monitoring.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import get_css, get_plotly_theme
from utils.database import format_integer
from utils.news_scraper import scrape_all_korea_sources, update_all_articles_with_ai, analyze_sentiment

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

# Database path
DB_PATH = Path(__file__).parent.parent / "displayintel.db"

# =============================================================================
# Constants
# =============================================================================

SUPPLIERS = ["Samsung", "BOE", "LGD", "CSOT", "AUO", "Innolux", "Sharp", "Tianma", "Visionox", "JDI", "EDO"]
TECHNOLOGIES = ["OLED", "LCD", "MicroLED", "MiniLED", "QD-OLED", "LTPO", "Foldable"]
PRODUCTS = ["Smartphone", "Tablet", "TV", "Monitor", "Automotive", "Wearable", "IT"]
CATEGORIES = ["Technology", "Investment", "Factory", "Product Launch", "Financials", "M&A", "Supply Chain"]
SENTIMENTS = ["Positive", "Neutral", "Negative", "Mixed"]

# =============================================================================
# Database Functions
# =============================================================================

def init_news_table():
    """Create news table if it doesn't exist, or migrate old schema."""
    conn = sqlite3.connect(DB_PATH)

    # Check if table exists and get its columns
    cursor = conn.execute("PRAGMA table_info(news)")
    columns = {row[1] for row in cursor.fetchall()}

    if not columns:
        # Table doesn't exist - create new schema
        conn.execute("""
            CREATE TABLE news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                source_url TEXT,
                article_url TEXT,
                published_date DATE,
                summary TEXT,
                full_text TEXT,
                suppliers_mentioned TEXT,
                technologies_mentioned TEXT,
                products_mentioned TEXT,
                category TEXT,
                sentiment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        # Table exists - check if it has old schema (has 'content' but not 'sentiment')
        if 'content' in columns and 'sentiment' not in columns:
            # Migrate from old schema to new schema
            # Rename old table
            conn.execute("ALTER TABLE news RENAME TO news_old")

            # Create new table with correct schema
            conn.execute("""
                CREATE TABLE news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_url TEXT,
                    article_url TEXT,
                    published_date DATE,
                    summary TEXT,
                    full_text TEXT,
                    suppliers_mentioned TEXT,
                    technologies_mentioned TEXT,
                    products_mentioned TEXT,
                    category TEXT,
                    sentiment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migrate data from old table to new table
            conn.execute("""
                INSERT INTO news (id, title, source, article_url, published_date, summary,
                                  full_text, suppliers_mentioned, category, created_at)
                SELECT id, title, source, url, published_date, summary,
                       content, manufacturers, category, created_at
                FROM news_old
            """)

            # Drop old table
            conn.execute("DROP TABLE news_old")
        elif 'sentiment' not in columns:
            # Just add missing columns
            try:
                conn.execute("ALTER TABLE news ADD COLUMN sentiment TEXT")
            except:
                pass
            try:
                conn.execute("ALTER TABLE news ADD COLUMN suppliers_mentioned TEXT")
            except:
                pass
            try:
                conn.execute("ALTER TABLE news ADD COLUMN technologies_mentioned TEXT")
            except:
                pass
            try:
                conn.execute("ALTER TABLE news ADD COLUMN products_mentioned TEXT")
            except:
                pass
            try:
                conn.execute("ALTER TABLE news ADD COLUMN full_text TEXT")
            except:
                pass
            try:
                conn.execute("ALTER TABLE news ADD COLUMN source_url TEXT")
            except:
                pass
            try:
                conn.execute("ALTER TABLE news ADD COLUMN article_url TEXT")
            except:
                pass

    conn.commit()
    conn.close()

def get_news_articles(supplier=None, source=None, category=None, sentiment=None,
                      start_date=None, end_date=None, search=None, limit=100, offset=0):
    """Get news articles with filters."""
    conn = sqlite3.connect(DB_PATH)

    query = "SELECT * FROM news WHERE 1=1"
    params = []

    if supplier and supplier != "All":
        query += " AND suppliers_mentioned LIKE ?"
        params.append(f"%{supplier}%")

    if source and source != "All":
        query += " AND source = ?"
        params.append(source)

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if sentiment and sentiment != "All":
        query += " AND sentiment = ?"
        params.append(sentiment)

    if start_date:
        query += " AND published_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND published_date <= ?"
        params.append(end_date)

    if search:
        query += " AND (title LIKE ? OR summary LIKE ? OR full_text LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY published_date DESC, created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_news_count(supplier=None, source=None, category=None, sentiment=None,
                   start_date=None, end_date=None, search=None):
    """Get total count of news articles matching filters."""
    conn = sqlite3.connect(DB_PATH)

    query = "SELECT COUNT(*) as count FROM news WHERE 1=1"
    params = []

    if supplier and supplier != "All":
        query += " AND suppliers_mentioned LIKE ?"
        params.append(f"%{supplier}%")

    if source and source != "All":
        query += " AND source = ?"
        params.append(source)

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if sentiment and sentiment != "All":
        query += " AND sentiment = ?"
        params.append(sentiment)

    if start_date:
        query += " AND published_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND published_date <= ?"
        params.append(end_date)

    if search:
        query += " AND (title LIKE ? OR summary LIKE ? OR full_text LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    cursor = conn.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_unique_sources():
    """Get list of unique news sources."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT DISTINCT source FROM news ORDER BY source")
    sources = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sources

def save_news_article(article):
    """Save a news article to the database."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            INSERT INTO news (title, source, source_url, article_url, published_date,
                            summary, full_text, suppliers_mentioned, technologies_mentioned,
                            products_mentioned, category, sentiment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article.get('title'),
            article.get('source'),
            article.get('source_url'),
            article.get('article_url'),
            article.get('published_date'),
            article.get('summary'),
            article.get('full_text'),
            article.get('suppliers_mentioned'),
            article.get('technologies_mentioned'),
            article.get('products_mentioned'),
            article.get('category'),
            article.get('sentiment')
        ))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_news_article(article_id):
    """Delete a news article."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM news WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()

def get_news_stats():
    """Get news statistics."""
    conn = sqlite3.connect(DB_PATH)

    stats = {}

    # Total articles
    cursor = conn.execute("SELECT COUNT(*) FROM news")
    stats['total'] = cursor.fetchone()[0]

    # By sentiment
    cursor = conn.execute("""
        SELECT sentiment, COUNT(*) as count FROM news
        WHERE sentiment IS NOT NULL
        GROUP BY sentiment
    """)
    stats['by_sentiment'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Most mentioned supplier
    cursor = conn.execute("SELECT suppliers_mentioned FROM news WHERE suppliers_mentioned IS NOT NULL")
    supplier_counts = {}
    for row in cursor.fetchall():
        for supplier in row[0].split(','):
            supplier = supplier.strip()
            if supplier:
                supplier_counts[supplier] = supplier_counts.get(supplier, 0) + 1
    if supplier_counts:
        stats['top_supplier'] = max(supplier_counts, key=supplier_counts.get)
        stats['top_supplier_count'] = supplier_counts[stats['top_supplier']]
    else:
        stats['top_supplier'] = None
        stats['top_supplier_count'] = 0

    # Latest article
    cursor = conn.execute("SELECT published_date FROM news ORDER BY published_date DESC LIMIT 1")
    row = cursor.fetchone()
    stats['latest_date'] = row[0] if row else None

    conn.close()
    return stats

def insert_sample_data():
    """Insert sample news articles."""
    sample_articles = [
        {
            'title': 'Samsung Display Announces $3.1B Investment in QD-OLED Expansion',
            'source': 'Display Daily',
            'source_url': 'https://displaydaily.com',
            'article_url': 'https://displaydaily.com/samsung-qd-oled-investment',
            'published_date': '2025-01-28',
            'summary': 'Samsung Display has announced a major investment of $3.1 billion to expand its QD-OLED production capacity at its Asan campus. The expansion will add a new Gen 8.5 line targeting the premium TV and monitor markets.',
            'full_text': 'Samsung Display has announced a major investment of $3.1 billion to expand its QD-OLED production capacity at its Asan campus. The expansion will add a new Gen 8.5 line targeting the premium TV and monitor markets. Production is expected to begin in late 2026.',
            'suppliers_mentioned': 'Samsung',
            'technologies_mentioned': 'QD-OLED, OLED',
            'products_mentioned': 'TV, Monitor',
            'category': 'Investment',
            'sentiment': 'Positive'
        },
        {
            'title': 'BOE B16 Factory Achieves Mass Production Milestone',
            'source': 'OLED-Info',
            'source_url': 'https://oled-info.com',
            'article_url': 'https://oled-info.com/boe-b16-mass-production',
            'published_date': '2025-01-25',
            'summary': 'BOE Technology Group has announced that its B16 Gen 8.7 OLED factory in Chengdu has achieved mass production status. The facility is now producing flexible OLED panels for smartphone and IT applications.',
            'full_text': 'BOE Technology Group has announced that its B16 Gen 8.7 OLED factory in Chengdu has achieved mass production status. The facility is now producing flexible OLED panels for smartphone and IT applications. Initial capacity is 15K substrates per month.',
            'suppliers_mentioned': 'BOE',
            'technologies_mentioned': 'OLED, Foldable',
            'products_mentioned': 'Smartphone, IT',
            'category': 'Factory',
            'sentiment': 'Positive'
        },
        {
            'title': 'LG Display Reports Q4 Profit Recovery on OLED Demand',
            'source': 'Reuters',
            'source_url': 'https://reuters.com',
            'article_url': 'https://reuters.com/lgd-q4-earnings',
            'published_date': '2025-01-22',
            'summary': 'LG Display returned to profitability in Q4 2025 driven by strong OLED TV panel demand and improved operational efficiency. The company reported operating profit of 348 billion won.',
            'full_text': 'LG Display returned to profitability in Q4 2025 driven by strong OLED TV panel demand and improved operational efficiency. The company reported operating profit of 348 billion won, marking a significant turnaround from losses in previous quarters.',
            'suppliers_mentioned': 'LGD',
            'technologies_mentioned': 'OLED',
            'products_mentioned': 'TV',
            'category': 'Financials',
            'sentiment': 'Positive'
        },
        {
            'title': 'MicroLED Technology Advances with New Manufacturing Process',
            'source': 'LEDs Magazine',
            'source_url': 'https://ledsmagazine.com',
            'article_url': 'https://ledsmagazine.com/microled-breakthrough',
            'published_date': '2025-01-20',
            'summary': 'Researchers have developed a new mass transfer process for MicroLED displays that could significantly reduce manufacturing costs. The technology enables placement of 10,000 LEDs per second.',
            'full_text': 'Researchers have developed a new mass transfer process for MicroLED displays that could significantly reduce manufacturing costs. The technology enables placement of 10,000 LEDs per second, a 10x improvement over current methods.',
            'suppliers_mentioned': 'Samsung',
            'technologies_mentioned': 'MicroLED',
            'products_mentioned': 'TV, Wearable',
            'category': 'Technology',
            'sentiment': 'Positive'
        },
        {
            'title': 'Automotive Display Market to Reach $25B by 2028',
            'source': 'IHS Markit',
            'source_url': 'https://ihsmarkit.com',
            'article_url': 'https://ihsmarkit.com/automotive-display-forecast',
            'published_date': '2025-01-18',
            'summary': 'The automotive display market is projected to reach $25 billion by 2028, driven by larger screen sizes and adoption of OLED technology in premium vehicles.',
            'full_text': 'The automotive display market is projected to reach $25 billion by 2028, driven by larger screen sizes and adoption of OLED technology in premium vehicles. Key suppliers include BOE, LGD, and Sharp.',
            'suppliers_mentioned': 'BOE, LGD, Sharp',
            'technologies_mentioned': 'OLED, LCD',
            'products_mentioned': 'Automotive',
            'category': 'Investment',
            'sentiment': 'Positive'
        },
        {
            'title': 'Apple Diversifies OLED Supply Chain with New Suppliers',
            'source': 'DigiTimes',
            'source_url': 'https://digitimes.com',
            'article_url': 'https://digitimes.com/apple-oled-suppliers',
            'published_date': '2025-01-15',
            'summary': 'Apple is reportedly expanding its OLED supplier base to include BOE and possibly Visionox for future iPhone and iPad models, reducing dependence on Samsung and LG Display.',
            'full_text': 'Apple is reportedly expanding its OLED supplier base to include BOE and possibly Visionox for future iPhone and iPad models, reducing dependence on Samsung and LG Display. This diversification strategy aims to improve supply chain resilience.',
            'suppliers_mentioned': 'Samsung, BOE, LGD, Visionox',
            'technologies_mentioned': 'OLED',
            'products_mentioned': 'Smartphone, Tablet',
            'category': 'Supply Chain',
            'sentiment': 'Mixed'
        }
    ]

    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    for article in sample_articles:
        try:
            # Check if article already exists
            cursor = conn.execute("SELECT id FROM news WHERE title = ?", (article['title'],))
            if cursor.fetchone() is None:
                conn.execute("""
                    INSERT INTO news (title, source, source_url, article_url, published_date,
                                    summary, full_text, suppliers_mentioned, technologies_mentioned,
                                    products_mentioned, category, sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article['title'], article['source'], article['source_url'],
                    article['article_url'], article['published_date'], article['summary'],
                    article['full_text'], article['suppliers_mentioned'],
                    article['technologies_mentioned'], article['products_mentioned'],
                    article['category'], article['sentiment']
                ))
                inserted += 1
        except:
            pass
    conn.commit()
    conn.close()
    return inserted

# Initialize table
init_news_table()

# =============================================================================
# Page Header
# =============================================================================

st.markdown("""
    <h1>📰 Industry News</h1>
    <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
        Latest updates, market news, and industry developments
    </p>
""", unsafe_allow_html=True)

# Get theme
theme = get_plotly_theme()

# =============================================================================
# Main Tabs
# =============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["News Feed", "Add Article", "AI Analysis", "Market Trends"])

# =============================================================================
# Tab 1: News Feed
# =============================================================================

with tab1:
    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")

        # Supplier filter
        supplier_filter = st.selectbox(
            "Supplier",
            options=["All"] + SUPPLIERS,
            key="news_supplier"
        )

        # Source filter
        sources = get_unique_sources()
        source_filter = st.selectbox(
            "Source",
            options=["All"] + sources,
            key="news_source"
        )

        # Category filter
        category_filter = st.selectbox(
            "Category",
            options=["All"] + CATEGORIES,
            key="news_category"
        )

        # Sentiment filter
        sentiment_filter = st.selectbox(
            "Sentiment",
            options=["All"] + SENTIMENTS,
            key="news_sentiment"
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

        st.divider()

        # Search
        search_query = st.text_input(
            "Search",
            placeholder="Search articles...",
            key="news_search"
        )

        st.divider()

        # Fetch from web sources
        st.markdown("**Web Scraping**")
        if st.button("Fetch Latest (Korea)", use_container_width=True, type="primary"):
            with st.spinner("Scanning sources..."):
                results = scrape_all_korea_sources()

            # Show results
            st.markdown("**Results:**")
            for source, data in results['sources'].items():
                if 'error' in data:
                    st.error(f"{source}: Error - {data['error'][:30]}")
                else:
                    st.markdown(f"- **{source}**: {data['found']} found, {data['saved']} new, {data['duplicates']} duplicates")

            if results['total_saved'] > 0:
                st.success(f"Saved {results['total_saved']} new articles!")
                st.rerun()
            elif results['total_relevant'] > 0:
                st.info("No new articles (all duplicates)")
            else:
                st.warning("No relevant articles found")

        st.caption("Sources: The Elec, Display Daily, Korea Times")

        # AI Summary generation
        st.markdown("**AI Processing**")
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            key="anthropic_key",
            help="Required for AI summaries"
        )

        if st.button("Generate AI Summaries", use_container_width=True):
            if not api_key:
                st.warning("Enter API key above")
            else:
                with st.spinner("Generating summaries..."):
                    results = update_all_articles_with_ai(api_key)
                st.success(f"Updated {results['sentiments_updated']} articles")
                if results['summaries_generated'] > 0:
                    st.info(f"Generated {results['summaries_generated']} AI summaries")
                st.rerun()

        st.divider()

        # Insert sample data button
        if st.button("Load Sample Data", use_container_width=True):
            count = insert_sample_data()
            if count > 0:
                st.success(f"Inserted {count} sample articles")
                st.rerun()
            else:
                st.info("Sample data already loaded")

    # Get statistics
    stats = get_news_stats()

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Articles", format_integer(stats['total']))

    with col2:
        top_supplier = stats.get('top_supplier', 'N/A')
        top_count = stats.get('top_supplier_count', 0)
        st.metric("Top Supplier", top_supplier, f"{top_count} mentions" if top_count else None)

    with col3:
        latest = stats.get('latest_date', 'N/A')
        if latest and latest != 'N/A':
            try:
                latest = datetime.strptime(str(latest)[:10], '%Y-%m-%d').strftime('%b %d')
            except:
                pass
        st.metric("Latest Article", latest if latest else "N/A")

    with col4:
        positive = stats.get('by_sentiment', {}).get('Positive', 0)
        negative = stats.get('by_sentiment', {}).get('Negative', 0)
        st.metric("Sentiment", f"{positive} Pos / {negative} Neg")

    st.divider()

    # Pagination
    page_size = 20
    total_count = get_news_count(
        supplier=supplier_filter,
        source=source_filter,
        category=category_filter,
        sentiment=sentiment_filter,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        search=search_query if search_query else None
    )
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    if 'news_page' not in st.session_state:
        st.session_state.news_page = 1

    current_page = st.session_state.news_page
    offset = (current_page - 1) * page_size

    # Load articles
    news_df = get_news_articles(
        supplier=supplier_filter,
        source=source_filter,
        category=category_filter,
        sentiment=sentiment_filter,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        search=search_query if search_query else None,
        limit=page_size,
        offset=offset
    )

    if len(news_df) > 0:
        st.markdown(f"### Latest News ({total_count} articles)")

        for _, row in news_df.iterrows():
            # Sentiment color
            sentiment_colors = {
                'Positive': '#34C759',
                'Negative': '#FF3B30',
                'Neutral': '#86868B',
                'Mixed': '#FF9500'
            }
            sentiment_color = sentiment_colors.get(row.get('sentiment', 'Neutral'), '#86868B')

            # Format date
            pub_date = row.get('published_date', '')
            if pub_date:
                try:
                    pub_date = datetime.strptime(str(pub_date)[:10], '%Y-%m-%d').strftime('%B %d, %Y')
                except:
                    pub_date = str(pub_date)[:10]

            # Build tags
            tags_html = ""
            if row.get('suppliers_mentioned'):
                for supplier in str(row['suppliers_mentioned']).split(',')[:3]:
                    supplier = supplier.strip()
                    if supplier:
                        tags_html += f'<span style="background: #007AFF15; color: #007AFF; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.7rem; margin-right: 0.25rem;">{supplier}</span>'

            if row.get('technologies_mentioned'):
                for tech in str(row['technologies_mentioned']).split(',')[:2]:
                    tech = tech.strip()
                    if tech:
                        tags_html += f'<span style="background: #5856D615; color: #5856D6; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.7rem; margin-right: 0.25rem;">{tech}</span>'

            # Article card
            # Get article URL for link
            article_url = row.get('article_url', '#')
            title_text = row.get('title', 'Untitled')
            summary_text = str(row.get('summary', '')) if row.get('summary') else ''

            # Build product tags
            product_tags = ""
            if row.get('products_mentioned'):
                for product in str(row['products_mentioned']).split(',')[:2]:
                    product = product.strip()
                    if product:
                        product_tags += f'<span style="background: #34C75915; color: #34C759; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.7rem; margin-right: 0.25rem;">{product}</span>'

            # Build summary HTML
            if summary_text:
                summary_html = f'<p style="color: #515154; font-size: 0.9rem; line-height: 1.6; margin-bottom: 0.75rem; font-style: italic;">{summary_text[:300]}{"..." if len(summary_text) > 300 else ""}</p>'
            else:
                summary_html = '<p style="color: #86868B; font-size: 0.85rem; font-style: italic; margin-bottom: 0.75rem;">No summary available</p>'

            st.markdown(f"""
<div style="background: white; border: 1px solid #E5E5E7; border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <span style="background: {sentiment_color}15; color: {sentiment_color}; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 500;">{row.get('sentiment', 'Neutral')}</span>
            <span style="background: #F5F5F7; color: #86868B; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem;">{row.get('category', 'General')}</span>
        </div>
        <span style="color: #86868B; font-size: 0.75rem;">{pub_date}</span>
    </div>
    <h3 style="font-size: 1.15rem; font-weight: 600; color: #1D1D1F; margin-bottom: 0.5rem; line-height: 1.4;"><a href="{article_url}" target="_blank" style="color: #1D1D1F; text-decoration: none;">{title_text}</a></h3>
    <p style="color: #86868B; font-size: 0.8rem; margin-bottom: 0.75rem;">{row.get('source', 'Unknown')}</p>
    {summary_html}
    <div style="display: flex; gap: 0.25rem; flex-wrap: wrap; margin-bottom: 0.75rem;">{tags_html}{product_tags}</div>
    <div style="padding-top: 0.75rem; border-top: 1px solid #F5F5F7;"><a href="{article_url}" target="_blank" style="color: #007AFF; font-size: 0.85rem; font-weight: 500; text-decoration: none;">Read Full Article →</a></div>
</div>
            """, unsafe_allow_html=True)

        # Pagination controls
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if current_page > 1:
                if st.button("← Previous"):
                    st.session_state.news_page = current_page - 1
                    st.rerun()

        with col2:
            st.markdown(f"<p style='text-align: center; color: #86868B;'>Page {current_page} of {total_pages}</p>", unsafe_allow_html=True)

        with col3:
            if current_page < total_pages:
                if st.button("Next →"):
                    st.session_state.news_page = current_page + 1
                    st.rerun()

        # Export
        st.divider()
        all_news = get_news_articles(
            supplier=supplier_filter,
            source=source_filter,
            category=category_filter,
            sentiment=sentiment_filter,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            search=search_query if search_query else None,
            limit=10000
        )
        csv = all_news.to_csv(index=False)
        st.download_button("Download CSV", csv, "news_export.csv", "text/csv")

    else:
        st.info("No articles found. Use the **Add Article** tab or click **Load Sample Data** in the sidebar.")

# =============================================================================
# Tab 2: Add Article
# =============================================================================

with tab2:
    st.markdown("### Add News Article")

    with st.form("add_article_form"):
        title = st.text_input("Title *", placeholder="Article headline")

        col1, col2 = st.columns(2)
        with col1:
            source = st.text_input("Source *", placeholder="e.g., Display Daily")
            source_url = st.text_input("Source URL", placeholder="https://...")
        with col2:
            article_url = st.text_input("Article URL", placeholder="https://...")
            published_date = st.date_input("Published Date", value=date.today())

        summary = st.text_area("Summary *", placeholder="Brief summary of the article...", height=100)
        full_text = st.text_area("Full Text", placeholder="Full article text (optional)...", height=150)

        st.markdown("#### Tags")
        col1, col2, col3 = st.columns(3)
        with col1:
            suppliers = st.multiselect("Suppliers Mentioned", options=SUPPLIERS)
        with col2:
            technologies = st.multiselect("Technologies Mentioned", options=TECHNOLOGIES)
        with col3:
            products = st.multiselect("Products Mentioned", options=PRODUCTS)

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", options=CATEGORIES)
        with col2:
            sentiment = st.selectbox("Sentiment", options=SENTIMENTS)

        submitted = st.form_submit_button("Save Article", type="primary")

        if submitted:
            if not title or not source or not summary:
                st.error("Please fill in required fields: Title, Source, Summary")
            else:
                article = {
                    'title': title,
                    'source': source,
                    'source_url': source_url if source_url else None,
                    'article_url': article_url if article_url else None,
                    'published_date': published_date.strftime("%Y-%m-%d"),
                    'summary': summary,
                    'full_text': full_text if full_text else None,
                    'suppliers_mentioned': ', '.join(suppliers) if suppliers else None,
                    'technologies_mentioned': ', '.join(technologies) if technologies else None,
                    'products_mentioned': ', '.join(products) if products else None,
                    'category': category,
                    'sentiment': sentiment
                }

                success, error = save_news_article(article)
                if success:
                    st.success(f"✅ Article saved: {title}")
                    st.rerun()
                else:
                    st.error(f"Error saving article: {error}")

# =============================================================================
# Tab 3: AI Analysis (Placeholder)
# =============================================================================

with tab3:
    st.markdown("### AI-Powered News Analysis")

    st.markdown("""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #F5F5F7 0%, #E5E5E7 100%);
        border-radius: 20px;
        margin-top: 1rem;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🤖</div>
        <h2 style="color: #1D1D1F; margin-bottom: 0.5rem;">Coming in Phase 3</h2>
        <p style="color: #86868B; max-width: 500px; margin: 0 auto; line-height: 1.6;">
            AI-powered analysis will automatically extract insights, identify trends,
            and generate summaries from news articles. Features include:
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 📊 Trend Detection
        Automatically identify emerging trends across suppliers, technologies, and markets.
        """)

    with col2:
        st.markdown("""
        #### 🔍 Entity Extraction
        Auto-extract mentioned companies, products, and financial figures from articles.
        """)

    with col3:
        st.markdown("""
        #### 📈 Sentiment Analysis
        Advanced sentiment scoring with confidence levels and key phrase extraction.
        """)

# =============================================================================
# Tab 4: Market Trends (Placeholder)
# =============================================================================

with tab4:
    st.markdown("### Market Trend Analysis")

    st.markdown("""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #F5F5F7 0%, #E5E5E7 100%);
        border-radius: 20px;
        margin-top: 1rem;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📈</div>
        <h2 style="color: #1D1D1F; margin-bottom: 0.5rem;">Coming in Phase 3</h2>
        <p style="color: #86868B; max-width: 500px; margin: 0 auto; line-height: 1.6;">
            Market trend visualizations based on news frequency, sentiment shifts,
            and topic clustering. Features include:
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 📅 Timeline View
        Visual timeline of key events by supplier or technology category.
        """)

    with col2:
        st.markdown("""
        #### 🗺️ Topic Clusters
        Interactive visualization of related news topics and their connections.
        """)

    with col3:
        st.markdown("""
        #### 📊 Sentiment Trends
        Track sentiment changes over time for specific suppliers or technologies.
        """)
