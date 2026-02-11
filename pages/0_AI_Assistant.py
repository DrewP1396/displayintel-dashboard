"""
AI Assistant - Display Intelligence Dashboard
Chat with AI about display industry data using Google Gemini.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
import json
import time
import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import get_css
from utils.database import format_integer

# Page config
st.set_page_config(
    page_title="AI Assistant - Display Intelligence",
    page_icon="🤖",
    layout="wide"
)

# Apply styling
st.markdown(get_css(), unsafe_allow_html=True)

# Check authentication (restore session from cookie if available)

if not st.session_state.get("password_correct", False):
    st.warning("Please login from the main page.")
    st.stop()

# Database path
DB_PATH = Path(__file__).parent.parent / "displayintel.db"

# =============================================================================
# Constants
# =============================================================================

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
DAILY_LIMIT = 1500
WARNING_THRESHOLD = 1400

# Example questions
EXAMPLE_QUESTIONS = [
    "What are the latest news about Samsung Display?",
    "How many factories does BOE operate?",
    "What's the average utilization rate for OLED fabs?",
    "Show me recent equipment orders over $100M",
    "Which companies are investing in Gen 8.6 OLED?",
    "What's the sentiment breakdown of recent news?",
    "Compare LG Display and Samsung Display financials",
    "What technologies are trending in the news?",
]

# Database schema context for the AI
DATABASE_SCHEMA = """
You have access to a SQLite database with the following tables:

1. news - Industry news articles
   - id, title, source, article_url, published_date, summary, full_text
   - suppliers_mentioned, technologies_mentioned, products_mentioned
   - category, sentiment, created_at

2. factories - Display manufacturing facilities
   - id, manufacturer, factory_name, location, country, generation
   - technology (LCD/OLED), substrate_size, capacity_k_per_month
   - status (Operating/Ramping/Planned), start_year

3. utilization - Monthly factory utilization rates
   - id, factory_id, year, month, utilization_percent

4. equipment_orders - Equipment purchase orders
   - id, order_date, customer, supplier, equipment_type, process_step
   - quantity, value_usd, factory_destination, delivery_date, status

5. shipments - Panel shipment data
   - id, year, quarter, manufacturer, technology, application
   - units_millions, revenue_millions, market_share_percent

6. company_financials - Company financial data
   - id, company, year, quarter, revenue_krw_billions, operating_profit_krw_billions
   - revenue_usd_millions, operating_profit_usd_millions, segment

Key relationships:
- utilization.factory_id links to factories.id
- equipment_orders.customer often matches factories.manufacturer
"""

# =============================================================================
# Helper Functions
# =============================================================================

def get_api_key():
    """Get Gemini API key from Streamlit secrets."""
    try:
        return st.secrets.get("gemini_api_key", None)
    except:
        return None


def get_usage_key():
    """Get the usage tracking key for today."""
    return f"gemini_usage_{date.today().isoformat()}"


def get_daily_usage():
    """Get current daily usage count."""
    key = get_usage_key()
    return st.session_state.get(key, 0)


def increment_usage():
    """Increment daily usage counter."""
    key = get_usage_key()
    current = st.session_state.get(key, 0)
    st.session_state[key] = current + 1
    return current + 1


def can_make_request():
    """Check if we can make another API request."""
    return get_daily_usage() < DAILY_LIMIT


def get_database_context():
    """Get summary of database contents for context."""
    conn = sqlite3.connect(DB_PATH)

    context_parts = []

    # News summary
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM news")
        news_count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT source, COUNT(*) FROM news GROUP BY source")
        sources = dict(cursor.fetchall())
        context_parts.append(f"News: {news_count} articles from {', '.join(sources.keys())}")
    except:
        pass

    # Factories summary
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM factories")
        factory_count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT manufacturer, COUNT(*) FROM factories GROUP BY manufacturer ORDER BY COUNT(*) DESC LIMIT 5")
        top_mfrs = [f"{r[0]} ({r[1]})" for r in cursor.fetchall()]
        context_parts.append(f"Factories: {factory_count} facilities. Top: {', '.join(top_mfrs)}")
    except:
        pass

    # Equipment orders summary
    try:
        cursor = conn.execute("SELECT COUNT(*), SUM(value_usd) FROM equipment_orders")
        row = cursor.fetchone()
        if row[0]:
            context_parts.append(f"Equipment Orders: {row[0]} orders, ${row[1]/1e9:.1f}B total value")
    except:
        pass

    conn.close()
    return "\n".join(context_parts)


def execute_sql_query(query: str) -> tuple:
    """
    Safely execute a SQL query and return results.

    Returns:
        Tuple of (success: bool, result: DataFrame or error message)
    """
    # Safety checks
    query_lower = query.lower().strip()

    # Only allow SELECT queries
    if not query_lower.startswith('select'):
        return False, "Only SELECT queries are allowed for safety."

    # Block dangerous keywords
    dangerous = ['drop', 'delete', 'update', 'insert', 'alter', 'create', 'truncate', ';--']
    for keyword in dangerous:
        if keyword in query_lower:
            return False, f"Query contains forbidden keyword: {keyword}"

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Limit results
        if len(df) > 100:
            df = df.head(100)

        return True, df
    except Exception as e:
        return False, f"Query error: {str(e)}"


def call_gemini_api(prompt: str, api_key: str) -> tuple:
    """
    Call Google Gemini API with retry on 429 rate-limit errors.

    Returns:
        Tuple of (success: bool, response text or error)
    """
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    }

    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            response = requests.post(
                f"{GEMINI_API_URL}?key={api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return True, text

            if response.status_code == 429 and attempt < max_attempts - 1:
                # Parse retry delay from error response if available
                wait_seconds = 15
                try:
                    err_data = response.json()
                    details = err_data.get("error", {}).get("details", [])
                    for detail in details:
                        if "retryDelay" in detail:
                            delay_str = detail["retryDelay"]
                            # Parse e.g. "32s" or "32.5s"
                            wait_seconds = int(float(delay_str.rstrip("s")))
                            break
                except (ValueError, KeyError, json.JSONDecodeError):
                    pass
                wait_seconds = min(wait_seconds, 60)
                time.sleep(wait_seconds)
                continue

            if response.status_code == 429:
                return False, "QUOTA_EXCEEDED"

            return False, f"API Error: {response.status_code} - {response.text[:200]}"

        except Exception as e:
            return False, f"Request failed: {str(e)}"

    return False, "QUOTA_EXCEEDED"


def process_user_question(question: str, api_key: str) -> dict:
    """
    Process a user question using Gemini.

    Returns:
        Dict with 'response', 'sql_query', 'data' keys
    """
    result = {
        'response': '',
        'sql_query': None,
        'data': None
    }

    # Build the prompt
    db_context = get_database_context()

    prompt = f"""You are an AI assistant for a Display Industry Intelligence Dashboard. You help users understand data about display panel manufacturers, factories, equipment orders, and industry news.

{DATABASE_SCHEMA}

Current database contents:
{db_context}

User question: {question}

Instructions:
1. If the question requires data from the database, generate a SQL query to answer it.
2. Format your response as follows:
   - If SQL is needed, start with: SQL_QUERY: <your query here>
   - Then provide a natural language explanation
3. Keep responses concise and focused on the display industry.
4. If you're unsure, say so rather than making up data.

Response:"""

    # Call Gemini
    success, response = call_gemini_api(prompt, api_key)

    if not success:
        if response == "QUOTA_EXCEEDED":
            result['response'] = (
                "⚠️ The AI service is temporarily unavailable due to API rate limits. "
                "Google's free-tier quota has been exceeded. Please wait a minute and try again, "
                "or contact the administrator if this persists."
            )
        else:
            result['response'] = f"Sorry, I encountered an error: {response}"
        return result

    # Parse response for SQL query
    if "SQL_QUERY:" in response:
        parts = response.split("SQL_QUERY:", 1)
        if len(parts) > 1:
            # Extract SQL query (until newline or end)
            sql_part = parts[1].strip()
            # Find end of SQL (usually ends with ; or newline followed by text)
            sql_lines = []
            for line in sql_part.split('\n'):
                line = line.strip()
                if line and not line.startswith('```'):
                    sql_lines.append(line)
                    if line.endswith(';'):
                        break
                elif sql_lines:  # Non-SQL line after SQL started
                    break

            if sql_lines:
                sql_query = ' '.join(sql_lines).strip('`').strip()
                result['sql_query'] = sql_query

                # Execute the query
                success, data = execute_sql_query(sql_query)
                if success:
                    result['data'] = data
                else:
                    result['response'] = f"Query failed: {data}\n\n"

            # Get the explanation part (after SQL)
            explanation_start = response.find('\n', response.find("SQL_QUERY:"))
            if explanation_start > 0:
                explanation = response[explanation_start:].strip()
                # Clean up any remaining SQL artifacts
                explanation = explanation.replace('```sql', '').replace('```', '').strip()
                result['response'] = explanation
    else:
        result['response'] = response

    return result


# =============================================================================
# Main UI
# =============================================================================

st.markdown("""
    <h1 style="margin-bottom: 0.25rem;">🤖 AI Assistant</h1>
    <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 1.5rem;">
        Ask questions about display industry data
    </p>
""", unsafe_allow_html=True)

# Check for API key
api_key = get_api_key()

if not api_key:
    st.error("Gemini API key not configured. Please contact administrator.")
    st.info("To enable AI Assistant, add `gemini_api_key` to Streamlit secrets.")
    st.stop()

# Usage tracking
col1, col2 = st.columns([3, 1])

with col2:
    usage = get_daily_usage()
    remaining = DAILY_LIMIT - usage

    if usage >= DAILY_LIMIT:
        st.error(f"Daily limit reached ({DAILY_LIMIT})")
    elif usage >= WARNING_THRESHOLD:
        st.warning(f"⚠️ {remaining} requests left today")
    else:
        st.caption(f"📊 {usage}/{DAILY_LIMIT} requests used today")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Example questions
with st.expander("💡 Example Questions", expanded=len(st.session_state.messages) == 0):
    cols = st.columns(2)
    for i, question in enumerate(EXAMPLE_QUESTIONS):
        col = cols[i % 2]
        with col:
            if st.button(question, key=f"example_{i}", use_container_width=True):
                st.session_state.pending_question = question
                st.rerun()

st.divider()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show data table if present
        if message.get("data") is not None:
            st.dataframe(message["data"], use_container_width=True)

        # Show SQL query if present
        if message.get("sql_query"):
            with st.expander("View SQL Query"):
                st.code(message["sql_query"], language="sql")

# Handle pending question from example buttons
if "pending_question" in st.session_state:
    question = st.session_state.pending_question
    del st.session_state.pending_question

    # Check usage limit
    if not can_make_request():
        st.error("Daily request limit reached. Please try again tomorrow.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                increment_usage()
                result = process_user_question(question, api_key)

            st.markdown(result['response'])

            if result['data'] is not None:
                st.dataframe(result['data'], use_container_width=True)

            if result['sql_query']:
                with st.expander("View SQL Query"):
                    st.code(result['sql_query'], language="sql")

        # Save to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": result['response'],
            "data": result['data'],
            "sql_query": result['sql_query']
        })

        st.rerun()

# Chat input
if prompt := st.chat_input("Ask about display industry data..."):
    # Check usage limit
    if not can_make_request():
        st.error("Daily request limit reached. Please try again tomorrow.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                increment_usage()
                result = process_user_question(prompt, api_key)

            st.markdown(result['response'])

            if result['data'] is not None:
                st.dataframe(result['data'], use_container_width=True)

            if result['sql_query']:
                with st.expander("View SQL Query"):
                    st.code(result['sql_query'], language="sql")

        # Save to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": result['response'],
            "data": result['data'],
            "sql_query": result['sql_query']
        })

        st.rerun()

# Clear chat button
if st.session_state.messages:
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Footer
st.markdown("<br>", unsafe_allow_html=True)
st.caption("Powered by Google Gemini 2.5 Flash Lite • Free tier: 1,500 requests/day")
