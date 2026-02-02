"""
News Scraper for Display Intelligence Dashboard
Scrapes display panel industry news from Korean sources.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import sqlite3
from pathlib import Path
import re
import time

# Database path
DB_PATH = Path(__file__).parent.parent / "displayintel.db"

# =============================================================================
# Relevance Filtering
# =============================================================================

# Company names to look for
DISPLAY_COMPANIES = [
    'samsung display', 'lg display', 'lgd', 'sdc',
    'boe', 'csot', 'tcl csot', 'china star',
    'auo', 'au optronics', 'innolux',
    'sharp', 'sharp display',
    'jdi', 'japan display',
    'tianma', 'visionox', 'everdisplay', 'edo',
    'panel maker', 'display maker', 'display manufacturer'
]

# Display industry keywords
DISPLAY_KEYWORDS = [
    # Technologies
    'oled', 'amoled', 'lcd', 'qd-oled', 'woled', 'qned',
    'ltpo', 'ltps', 'igzo', 'a-si',
    'microled', 'micro-led', 'micro led',
    'miniled', 'mini-led', 'mini led',
    'foldable display', 'flexible display', 'rollable display',
    'tandem oled', 'blue pholed',

    # Manufacturing
    'display panel', 'panel production', 'panel shipment',
    'gen 6', 'gen 8', 'gen 10', 'g6', 'g8', 'g8.5', 'g8.7', 'g10.5',
    'fab', 'fabrication', 'mass production',
    'utilization', 'capacity', 'substrate',
    'evaporator', 'encapsulation', 'backplane',
    'deposition', 'lithography', 'tft',

    # Business terms
    'display investment', 'display expansion',
    'panel price', 'display revenue',
    'display order', 'panel order',
    'display supply', 'panel supply'
]

# Keywords that indicate non-display content (negative filter)
EXCLUDE_KEYWORDS = [
    'galaxy s2', 'galaxy z', 'iphone review', 'phone review',
    'tv review', 'monitor review', 'laptop review',
    'home appliance', 'refrigerator', 'washing machine',
    'battery cell', 'ev battery', 'battery pack',
    'semiconductor fab', 'chip fab', 'memory chip',
    'autonomous driving', 'robot vacuum'
]


def is_display_relevant(title: str, text: str = "") -> bool:
    """
    Check if article is relevant to display panel industry.

    Args:
        title: Article title
        text: Article summary or full text (optional)

    Returns:
        True if article is about display industry
    """
    # Combine title and text for searching
    content = f"{title} {text}".lower()

    # First check exclusions - skip if clearly not about displays
    for exclude in EXCLUDE_KEYWORDS:
        if exclude in content:
            # But allow if also contains strong display signals
            has_display_signal = any(
                kw in content for kw in ['display', 'oled', 'lcd', 'panel']
            )
            if not has_display_signal:
                return False

    # Check for company names
    for company in DISPLAY_COMPANIES:
        if company in content:
            return True

    # Check for display keywords
    keyword_matches = sum(1 for kw in DISPLAY_KEYWORDS if kw in content)

    # Require at least 1 keyword match
    return keyword_matches >= 1


def parse_date(date_str: str) -> str:
    """Parse various date formats to YYYY-MM-DD."""
    if not date_str:
        return date.today().isoformat()

    date_str = date_str.strip()

    # Common formats
    formats = [
        '%Y-%m-%d',
        '%Y.%m.%d',
        '%Y/%m/%d',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str[:20], fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue

    # Try to extract date with regex
    match = re.search(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})', date_str)
    if match:
        return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"

    return date.today().isoformat()


def extract_suppliers_from_text(text: str) -> str:
    """Extract mentioned suppliers from article text."""
    text_lower = text.lower()
    suppliers = []

    supplier_map = {
        'samsung display': 'Samsung',
        'samsung': 'Samsung',
        'sdc': 'Samsung',
        'lg display': 'LGD',
        'lgd': 'LGD',
        'boe': 'BOE',
        'csot': 'CSOT',
        'tcl csot': 'CSOT',
        'china star': 'CSOT',
        'auo': 'AUO',
        'au optronics': 'AUO',
        'innolux': 'Innolux',
        'sharp': 'Sharp',
        'jdi': 'JDI',
        'japan display': 'JDI',
        'tianma': 'Tianma',
        'visionox': 'Visionox',
        'everdisplay': 'EDO',
        'edo': 'EDO'
    }

    for keyword, supplier in supplier_map.items():
        if keyword in text_lower and supplier not in suppliers:
            suppliers.append(supplier)

    return ', '.join(suppliers) if suppliers else None


def extract_technologies_from_text(text: str) -> str:
    """Extract mentioned technologies from article text."""
    text_lower = text.lower()
    technologies = []

    tech_map = {
        'oled': 'OLED',
        'amoled': 'OLED',
        'qd-oled': 'QD-OLED',
        'woled': 'OLED',
        'lcd': 'LCD',
        'ltpo': 'LTPO',
        'microled': 'MicroLED',
        'micro-led': 'MicroLED',
        'miniled': 'MiniLED',
        'mini-led': 'MiniLED',
        'foldable': 'Foldable',
        'flexible display': 'Foldable'
    }

    for keyword, tech in tech_map.items():
        if keyword in text_lower and tech not in technologies:
            technologies.append(tech)

    return ', '.join(technologies) if technologies else None


def extract_products_from_text(text: str) -> str:
    """Extract mentioned products from article text."""
    text_lower = text.lower()
    products = []

    product_map = {
        'smartphone': 'Smartphone',
        'mobile': 'Smartphone',
        'phone': 'Smartphone',
        'tablet': 'Tablet',
        'ipad': 'Tablet',
        'tv': 'TV',
        'television': 'TV',
        'monitor': 'Monitor',
        'laptop': 'IT',
        'notebook': 'IT',
        'it panel': 'IT',
        'automotive': 'Automotive',
        'car display': 'Automotive',
        'vehicle': 'Automotive',
        'wearable': 'Wearable',
        'watch': 'Wearable'
    }

    for keyword, product in product_map.items():
        if keyword in text_lower and product not in products:
            products.append(product)

    return ', '.join(products) if products else None


def categorize_article(title: str, text: str) -> str:
    """Categorize article based on content."""
    content = f"{title} {text}".lower()

    if any(kw in content for kw in ['invest', 'billion', 'million', 'funding', 'capex']):
        return 'Investment'
    elif any(kw in content for kw in ['factory', 'fab', 'production', 'mass production', 'facility']):
        return 'Factory'
    elif any(kw in content for kw in ['revenue', 'profit', 'earnings', 'quarterly', 'financial']):
        return 'Financials'
    elif any(kw in content for kw in ['acquire', 'merger', 'acquisition', 'deal', 'partnership']):
        return 'M&A'
    elif any(kw in content for kw in ['supply', 'order', 'shipment', 'demand']):
        return 'Supply Chain'
    elif any(kw in content for kw in ['launch', 'release', 'announce', 'new product', 'unveil']):
        return 'Product Launch'
    else:
        return 'Technology'


# =============================================================================
# Scrapers
# =============================================================================

def get_headers():
    """Return headers for requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }


def fetch_article_details(url: str) -> dict:
    """
    Fetch article page to get date, content, and summary.

    Args:
        url: Article URL

    Returns:
        Dict with 'date', 'content', 'summary' keys
    """
    result = {'date': None, 'content': None, 'summary': None}

    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return result

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract date - look for date patterns
        for el in soup.select('div.info-text, span.dated, em.dated, time, .article-date, .view-date, em'):
            text = el.get_text(strip=True)
            match = re.search(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})', text)
            if match:
                result['date'] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                break

        # Extract content
        for sel in ['#article-view-content-div', '.article-body', '.article-content', 'article', 'main']:
            el = soup.select_one(sel)
            if el:
                for unwanted in el.select('script, style, nav, aside'):
                    unwanted.decompose()
                text = el.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    result['content'] = text[:3000]
                    break

        # Generate summary from content
        if result['content']:
            sentences = re.split(r'(?<=[.!?])\s+', result['content'])
            summary_sentences = [s.strip() for s in sentences if 40 < len(s.strip()) < 300][:2]
            if summary_sentences:
                result['summary'] = ' '.join(summary_sentences)

    except Exception:
        pass

    return result


def scrape_the_elec() -> list:
    """
    Scrape The Elec (thelec.net) for display industry news.

    Returns:
        List of article dicts
    """
    articles = []
    seen_urls = set()
    base_url = "https://thelec.net"

    # Sections to scrape - Display Panel is S1N4
    urls_to_try = [
        f"{base_url}/news/articleList.html?sc_section_code=S1N4&view_type=sm",  # Display Panel
        f"{base_url}/news/articleList.html?sc_section_code=S1N1&view_type=sm",  # Latest Stories
    ]

    for url in urls_to_try:
        try:
            response = requests.get(url, headers=get_headers(), timeout=15)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all article links with articleView in href
            links = soup.select('a[href*="articleView"]')

            for link in links:
                try:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)

                    # Skip if no title or too short (likely a "read more" link)
                    if not title or len(title) < 15:
                        continue

                    # Skip duplicates
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)

                    # Build full URL
                    if href.startswith('/'):
                        article_url = base_url + href
                    else:
                        article_url = href

                    # The Elec is focused on display/semiconductor, so most articles are relevant
                    # But still apply filter for non-display content
                    if not is_display_relevant(title, ""):
                        continue

                    # Fetch article details (date, content, summary)
                    details = fetch_article_details(article_url)
                    pub_date = details['date'] or date.today().isoformat()
                    summary = details['summary']
                    content = details['content'] or ""

                    articles.append({
                        'title': title,
                        'source': 'The Elec',
                        'source_url': 'https://thelec.net',
                        'article_url': article_url,
                        'published_date': pub_date,
                        'summary': summary[:500] if summary else None,
                        'full_text': content,
                        'suppliers_mentioned': extract_suppliers_from_text(f"{title} {content}"),
                        'technologies_mentioned': extract_technologies_from_text(f"{title} {content}"),
                        'products_mentioned': extract_products_from_text(f"{title} {content}"),
                        'category': categorize_article(title, content),
                        'sentiment': analyze_sentiment(title, content)
                    })

                    time.sleep(0.2)  # Rate limiting

                except Exception:
                    continue

        except Exception:
            continue

    return articles


def scrape_display_daily() -> list:
    """
    Scrape Display Daily for display industry news.

    Returns:
        List of article dicts
    """
    articles = []
    seen_urls = set()
    base_url = "https://displaydaily.com"

    try:
        response = requests.get(base_url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return articles

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find article links - Display Daily uses various formats
        all_links = soup.select('a[href]')

        for link in all_links:
            try:
                href = link.get('href', '')
                title = link.get_text(strip=True)

                # Skip navigation, short titles, and non-article links
                if not title or len(title) < 20:
                    continue

                # Must be a displaydaily.com article
                if not href.startswith(base_url) and not href.startswith('/'):
                    continue

                # Skip common non-article pages
                if any(skip in href.lower() for skip in ['about', 'contact', 'privacy', 'category', 'tag', 'author', '#']):
                    continue

                # Build full URL
                if href.startswith('/'):
                    article_url = base_url + href
                else:
                    article_url = href

                # Skip duplicates
                if article_url in seen_urls:
                    continue
                seen_urls.add(article_url)

                # Check relevance
                if not is_display_relevant(title, ""):
                    continue

                articles.append({
                    'title': title,
                    'source': 'Display Daily',
                    'source_url': base_url,
                    'article_url': article_url,
                    'published_date': date.today().isoformat(),
                    'summary': None,
                    'suppliers_mentioned': extract_suppliers_from_text(title),
                    'technologies_mentioned': extract_technologies_from_text(title),
                    'products_mentioned': extract_products_from_text(title),
                    'category': categorize_article(title, "")
                })

            except Exception:
                continue

    except Exception:
        pass

    return articles


def scrape_korea_times() -> list:
    """
    Scrape Korea Times business section for Samsung Display / LG Display news.

    Returns:
        List of article dicts
    """
    articles = []
    seen_urls = set()
    base_url = "https://www.koreatimes.co.kr"

    # Scrape business/tech sections
    urls_to_try = [
        f"{base_url}/www/biz/",  # Business section
        f"{base_url}/www/nation/",  # Nation section (sometimes has industry news)
    ]

    for url in urls_to_try:
        try:
            response = requests.get(url, headers=get_headers(), timeout=15)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all article links
            all_links = soup.select('a[href*="/www/"]')

            for link in all_links:
                try:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)

                    # Skip short titles and non-article links
                    if not title or len(title) < 20:
                        continue

                    # Must be an article URL with numbers (article IDs)
                    if not re.search(r'/\d+', href):
                        continue

                    # Build full URL
                    if href.startswith('/'):
                        article_url = base_url + href
                    elif not href.startswith('http'):
                        article_url = base_url + '/' + href
                    else:
                        article_url = href

                    # Skip duplicates
                    if article_url in seen_urls:
                        continue
                    seen_urls.add(article_url)

                    # Check relevance - Korea Times has general news so filter strictly
                    if not is_display_relevant(title, ""):
                        continue

                    articles.append({
                        'title': title,
                        'source': 'Korea Times',
                        'source_url': base_url,
                        'article_url': article_url,
                        'published_date': date.today().isoformat(),
                        'summary': None,
                        'suppliers_mentioned': extract_suppliers_from_text(title),
                        'technologies_mentioned': extract_technologies_from_text(title),
                        'products_mentioned': extract_products_from_text(title),
                        'category': categorize_article(title, "")
                    })

                except Exception:
                    continue

            time.sleep(0.3)  # Be polite between requests

        except Exception:
            continue

    return articles


# =============================================================================
# Database Functions
# =============================================================================

def save_articles_to_db(articles: list) -> tuple:
    """
    Save articles to database, skipping duplicates.

    Args:
        articles: List of article dicts

    Returns:
        Tuple of (saved_count, duplicate_count)
    """
    if not articles:
        return 0, 0

    conn = sqlite3.connect(DB_PATH)
    saved = 0
    duplicates = 0

    for article in articles:
        try:
            # Check for duplicate by URL
            cursor = conn.execute(
                "SELECT id FROM news WHERE article_url = ?",
                (article['article_url'],)
            )
            if cursor.fetchone():
                duplicates += 1
                continue

            # Also check by title (in case URL format changed)
            cursor = conn.execute(
                "SELECT id FROM news WHERE title = ? AND source = ?",
                (article['title'], article['source'])
            )
            if cursor.fetchone():
                duplicates += 1
                continue

            # Insert new article
            conn.execute("""
                INSERT INTO news (
                    title, source, source_url, article_url, published_date,
                    summary, full_text, suppliers_mentioned, technologies_mentioned,
                    products_mentioned, category, sentiment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article['title'],
                article['source'],
                article.get('source_url'),
                article['article_url'],
                article.get('published_date'),
                article.get('summary'),
                article.get('full_text'),
                article.get('suppliers_mentioned'),
                article.get('technologies_mentioned'),
                article.get('products_mentioned'),
                article.get('category'),
                article.get('sentiment'),
                datetime.now().isoformat()
            ))
            saved += 1

        except Exception as e:
            continue

    conn.commit()
    conn.close()

    return saved, duplicates


def scrape_all_korea_sources() -> dict:
    """
    Scrape all available sources and save to database.

    Returns:
        Dict with results summary
    """
    results = {
        'sources': {},
        'total_scanned': 0,
        'total_relevant': 0,
        'total_saved': 0,
        'total_duplicates': 0
    }

    # Scrape each source (The Elec is primary Korea source, Display Daily for broader coverage)
    scrapers = [
        ('The Elec', scrape_the_elec),
        ('Display Daily', scrape_display_daily),
        ('Korea Times', scrape_korea_times)
    ]

    for source_name, scraper_func in scrapers:
        try:
            articles = scraper_func()
            saved, duplicates = save_articles_to_db(articles)

            results['sources'][source_name] = {
                'found': len(articles),
                'saved': saved,
                'duplicates': duplicates
            }
            results['total_relevant'] += len(articles)
            results['total_saved'] += saved
            results['total_duplicates'] += duplicates

        except Exception as e:
            results['sources'][source_name] = {
                'error': str(e),
                'found': 0,
                'saved': 0,
                'duplicates': 0
            }

    return results


# =============================================================================
# AI Summary Generation
# =============================================================================

def get_anthropic_api_key():
    """Get Anthropic API key from Streamlit secrets or environment."""
    try:
        import streamlit as st
        return st.secrets.get("anthropic_api_key", None)
    except:
        pass

    import os
    return os.environ.get("ANTHROPIC_API_KEY", None)


def generate_ai_summary(title: str, full_text: str = None, api_key: str = None) -> str:
    """
    Generate AI summary using Claude Haiku.

    Args:
        title: Article title
        full_text: Article full text (optional)
        api_key: Anthropic API key

    Returns:
        2-3 sentence summary or None if failed
    """
    if not api_key:
        api_key = get_anthropic_api_key()

    if not api_key:
        return None

    content = title
    if full_text:
        content = f"Title: {title}\n\nArticle: {full_text[:2000]}"

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-haiku-3-5-20241022",
                "max_tokens": 150,
                "messages": [{
                    "role": "user",
                    "content": f"""Summarize this display industry news article in 2-3 sentences. Focus on the key business impact for display panel manufacturers.

{content}

Summary:"""
                }]
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return data['content'][0]['text'].strip()

    except Exception:
        pass

    return None


def analyze_sentiment(title: str, text: str = "") -> str:
    """
    Analyze sentiment based on keywords.

    Args:
        title: Article title
        text: Article text

    Returns:
        'Positive', 'Negative', 'Neutral', or 'Mixed'
    """
    content = f"{title} {text}".lower()

    positive_keywords = [
        'growth', 'profit', 'surge', 'increase', 'expand', 'investment',
        'breakthrough', 'success', 'milestone', 'record', 'win', 'gains',
        'strong', 'recovery', 'improve', 'boost', 'advance', 'innovation',
        'partnership', 'deal', 'order', 'contract', 'launch', 'ramp'
    ]

    negative_keywords = [
        'loss', 'decline', 'drop', 'fall', 'cut', 'layoff', 'closure',
        'halt', 'delay', 'problem', 'issue', 'concern', 'risk', 'weak',
        'slowdown', 'downturn', 'struggle', 'challenge', 'crisis', 'fail',
        'shortage', 'deficit', 'warning', 'suspend'
    ]

    positive_count = sum(1 for kw in positive_keywords if kw in content)
    negative_count = sum(1 for kw in negative_keywords if kw in content)

    if positive_count > 0 and negative_count > 0:
        if positive_count > negative_count * 2:
            return 'Positive'
        elif negative_count > positive_count * 2:
            return 'Negative'
        return 'Mixed'
    elif positive_count > 0:
        return 'Positive'
    elif negative_count > 0:
        return 'Negative'
    else:
        return 'Neutral'


def fetch_article_content(url: str) -> str:
    """
    Fetch full article content from URL.

    Args:
        url: Article URL

    Returns:
        Article text content or empty string
    """
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()

        # Try common article content selectors
        content_selectors = [
            'article', '.article-content', '.article-body', '#article-content',
            '.post-content', '.entry-content', '.content-body', 'main'
        ]

        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                text = content.get_text(separator=' ', strip=True)
                if len(text) > 200:
                    return text[:5000]

        # Fallback: get all paragraph text
        paragraphs = soup.select('p')
        text = ' '.join(p.get_text(strip=True) for p in paragraphs)
        return text[:5000] if text else ""

    except Exception:
        return ""


def update_article_with_ai(article_id: int, api_key: str = None) -> dict:
    """
    Update a single article with AI summary and enhanced tags.

    Args:
        article_id: Database article ID
        api_key: Anthropic API key

    Returns:
        Dict with update results
    """
    conn = sqlite3.connect(DB_PATH)

    # Get article
    cursor = conn.execute(
        "SELECT title, article_url, full_text, summary FROM news WHERE id = ?",
        (article_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {'error': 'Article not found'}

    title, url, full_text, existing_summary = row
    results = {'id': article_id, 'title': title[:50]}

    # Fetch content if needed
    if not full_text:
        full_text = fetch_article_content(url)
        if full_text:
            conn.execute(
                "UPDATE news SET full_text = ? WHERE id = ?",
                (full_text, article_id)
            )
            results['fetched_content'] = True

    # Generate AI summary if missing
    if not existing_summary and api_key:
        summary = generate_ai_summary(title, full_text, api_key)
        if summary:
            conn.execute(
                "UPDATE news SET summary = ? WHERE id = ?",
                (summary, article_id)
            )
            results['generated_summary'] = True

    # Update sentiment
    content = f"{title} {full_text or ''}"
    sentiment = analyze_sentiment(title, full_text or "")
    conn.execute(
        "UPDATE news SET sentiment = ? WHERE id = ?",
        (sentiment, article_id)
    )
    results['sentiment'] = sentiment

    # Update supplier/tech/product tags from full content
    suppliers = extract_suppliers_from_text(content)
    technologies = extract_technologies_from_text(content)
    products = extract_products_from_text(content)

    conn.execute("""
        UPDATE news SET
            suppliers_mentioned = COALESCE(?, suppliers_mentioned),
            technologies_mentioned = COALESCE(?, technologies_mentioned),
            products_mentioned = COALESCE(?, products_mentioned)
        WHERE id = ?
    """, (suppliers, technologies, products, article_id))

    conn.commit()
    conn.close()

    return results


def update_all_articles_with_ai(api_key: str = None) -> dict:
    """
    Update all articles with AI summaries and enhanced tags.

    Args:
        api_key: Anthropic API key

    Returns:
        Dict with summary of updates
    """
    conn = sqlite3.connect(DB_PATH)

    # Get articles needing updates
    cursor = conn.execute("""
        SELECT id, title FROM news
        WHERE summary IS NULL OR sentiment IS NULL
        ORDER BY published_date DESC
        LIMIT 50
    """)
    articles = cursor.fetchall()
    conn.close()

    results = {
        'total': len(articles),
        'summaries_generated': 0,
        'sentiments_updated': 0,
        'errors': 0
    }

    for article_id, title in articles:
        try:
            update_result = update_article_with_ai(article_id, api_key)
            if update_result.get('generated_summary'):
                results['summaries_generated'] += 1
            if update_result.get('sentiment'):
                results['sentiments_updated'] += 1
            time.sleep(0.5)  # Rate limiting
        except Exception:
            results['errors'] += 1

    return results


if __name__ == "__main__":
    # Test the scrapers
    print("Testing The Elec scraper...")
    articles = scrape_the_elec()
    print(f"Found {len(articles)} relevant articles from The Elec")
    for a in articles[:3]:
        print(f"  - {a['title'][:60]}...")

    print("\nTesting Display Daily scraper...")
    articles = scrape_display_daily()
    print(f"Found {len(articles)} relevant articles from Display Daily")
    for a in articles[:3]:
        print(f"  - {a['title'][:60]}...")

    print("\nTesting Korea Times scraper...")
    articles = scrape_korea_times()
    print(f"Found {len(articles)} relevant articles from Korea Times")
    for a in articles[:3]:
        print(f"  - {a['title'][:60]}...")
