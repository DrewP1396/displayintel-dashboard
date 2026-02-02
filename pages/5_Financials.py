"""
Financials Page - Display Intelligence Dashboard
Company financials with automated PDF extraction from IR reports.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import sqlite3
import re
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import get_css, get_plotly_theme, apply_chart_theme
from utils.database import DatabaseManager, format_currency, format_percent, format_integer

# Page config
st.set_page_config(
    page_title="Financials - Display Intelligence",
    page_icon="💰",
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

# PDF directory with fallback logic for local vs Streamlit Cloud
def get_pdf_directory():
    """Get PDF directory path with fallback for different environments."""
    # Try local path first (expanded ~)
    local_path = Path.home() / "displayintel" / "source_data" / "financials"
    if local_path.exists():
        return local_path

    # Try relative path (works in both environments)
    relative_path = Path(__file__).parent.parent / "source_data" / "financials"
    if relative_path.exists():
        return relative_path

    # Try Streamlit Cloud path
    cloud_path = Path("/mount/src/displayintel-dashboard/source_data/financials")
    if cloud_path.exists():
        return cloud_path

    # Return relative path as default (will show "not found" message)
    return relative_path

PDF_DIR = get_pdf_directory()

# =============================================================================
# Database Schema
# =============================================================================

def init_financials_table():
    """Create financials table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS company_financials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            year INTEGER NOT NULL,
            quarter TEXT NOT NULL,
            total_revenue_m REAL,
            operating_income_m REAL,
            operating_margin_pct REAL,
            display_revenue_m REAL,
            capex_m REAL,
            ebitda_m REAL,
            notes TEXT,
            source_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company, year, quarter)
        )
    """)
    conn.commit()
    conn.close()

# Initialize table
init_financials_table()

# =============================================================================
# Currency Conversion
# =============================================================================

KRW_TO_USD = 1300  # 1 USD = 1,300 KRW

def convert_krw_to_usd(amount, unit='trillion'):
    """Convert KRW to USD millions."""
    if amount is None:
        return None
    if unit == 'trillion':
        krw_value = amount * 1e12
    elif unit == 'billion':
        krw_value = amount * 1e9
    else:
        krw_value = amount
    usd_value = krw_value / KRW_TO_USD
    return usd_value / 1e6  # Return in millions

# =============================================================================
# PDF Extraction Functions
# =============================================================================

def extract_samsung_financials(pdf_path):
    """Extract financial data from Samsung earnings PDF."""
    try:
        import pdfplumber
    except ImportError:
        return None, "pdfplumber not installed"

    try:
        results = {
            'company': 'Samsung Display',
            'source_file': os.path.basename(pdf_path)
        }

        # Parse filename for quarter/year
        filename = os.path.basename(pdf_path)
        match = re.search(r'Q(\d)[\s_]*(\d{4})', filename, re.IGNORECASE)
        if match:
            results['quarter'] = f"Q{match.group(1)}"
            results['year'] = int(match.group(2))
        else:
            match = re.search(r'(\d{4}).*Q(\d)', filename, re.IGNORECASE)
            if match:
                results['year'] = int(match.group(1))
                results['quarter'] = f"Q{match.group(2)}"

        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages[:15]:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            # Look for SDC section - pattern: SDC followed by sales numbers
            # From Samsung PDF: SDC 8.1 8.1 9.5 (4Q24, 3Q25, 4Q25)
            sdc_pattern = r'SDC\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+[\d%\w↑↓]+\s+[\d%\w↑↓]+.*?([\d.]+)\s+([\d.]+)\s+([\d.]+)'
            sdc_match = re.search(sdc_pattern, full_text, re.DOTALL)

            if sdc_match:
                # Last value in sales group, last value in OP group
                current_q_sales = float(sdc_match.group(3))
                current_q_op = float(sdc_match.group(6))

                results['display_revenue_m'] = convert_krw_to_usd(current_q_sales, 'trillion')
                results['total_revenue_m'] = results['display_revenue_m']
                results['operating_income_m'] = convert_krw_to_usd(current_q_op, 'trillion')

                if results['total_revenue_m'] and results['total_revenue_m'] > 0:
                    results['operating_margin_pct'] = (results['operating_income_m'] / results['total_revenue_m']) * 100

            # Fallback: Look for SDC in simpler format
            if 'display_revenue_m' not in results or results.get('display_revenue_m') is None:
                # Pattern for "SDC ... Sales X.X" and "OP X.X"
                lines = full_text.split('\n')
                for i, line in enumerate(lines):
                    if 'SDC' in line and ('Sales' in line or 'OP' in line):
                        # Extract numbers from this section
                        numbers = re.findall(r'(\d+\.?\d*)', line)
                        if len(numbers) >= 2:
                            results['display_revenue_m'] = convert_krw_to_usd(float(numbers[-2]), 'trillion')
                            results['total_revenue_m'] = results['display_revenue_m']
                            results['operating_income_m'] = convert_krw_to_usd(float(numbers[-1]), 'trillion')
                            if results['total_revenue_m'] and results['total_revenue_m'] > 0:
                                results['operating_margin_pct'] = (results['operating_income_m'] / results['total_revenue_m']) * 100
                            break

            # CapEx from cash flow section
            capex_pattern = r'Purchase of PP&E.*?([\d.]+)'
            capex_match = re.search(capex_pattern, full_text)
            if capex_match:
                annual_capex = float(capex_match.group(1))
                results['capex_m'] = convert_krw_to_usd(annual_capex / 4, 'trillion')

        return results, None

    except Exception as e:
        return None, str(e)

def extract_lgd_financials(pdf_path):
    """Extract financial data from LG Display PDF."""
    try:
        import pdfplumber
    except ImportError:
        return None, "pdfplumber not installed"

    try:
        results = {
            'company': 'LG Display',
            'source_file': os.path.basename(pdf_path)
        }

        # Parse filename for quarter/year
        filename = os.path.basename(pdf_path)
        match = re.search(r'Q(\d)[\s_]*(\d{4})', filename, re.IGNORECASE)
        if match:
            results['quarter'] = f"Q{match.group(1)}"
            results['year'] = int(match.group(2))

        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages[:30]:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            # Look for Financial highlights section
            # Revenue pattern in millions of Won
            revenue_pattern = r'Revenue\s+([\d,]+)\s+'
            revenue_match = re.search(revenue_pattern, full_text)

            if revenue_match:
                cumulative_revenue = float(revenue_match.group(1).replace(',', ''))
                # Q3 report has 9 months data, estimate quarterly
                if 'Q3' in results.get('quarter', ''):
                    quarterly_revenue = cumulative_revenue / 3
                else:
                    quarterly_revenue = cumulative_revenue
                # Convert from million Won to USD millions
                results['total_revenue_m'] = (quarterly_revenue * 1e6) / KRW_TO_USD / 1e6
                results['display_revenue_m'] = results['total_revenue_m']

            # Operating profit/loss
            op_pattern = r'Operating profit \(loss\)\s+([\d,\-]+)'
            op_match = re.search(op_pattern, full_text)

            if op_match:
                op_str = op_match.group(1).replace(',', '')
                cumulative_op = float(op_str)
                if 'Q3' in results.get('quarter', ''):
                    quarterly_op = cumulative_op / 3
                else:
                    quarterly_op = cumulative_op
                results['operating_income_m'] = (quarterly_op * 1e6) / KRW_TO_USD / 1e6

                if results.get('total_revenue_m') and results['total_revenue_m'] != 0:
                    results['operating_margin_pct'] = (results['operating_income_m'] / results['total_revenue_m']) * 100

            # CapEx
            capex_pattern = r'capital expenditures.*?W([\d.]+)\s*trillion'
            capex_match = re.search(capex_pattern, full_text, re.IGNORECASE)
            if capex_match:
                annual_capex = float(capex_match.group(1))
                results['capex_m'] = convert_krw_to_usd(annual_capex / 4, 'trillion')

        return results, None

    except Exception as e:
        return None, str(e)

def extract_financials_from_pdf(pdf_path):
    """Extract financial data from PDF based on company."""
    filename = os.path.basename(pdf_path).lower()

    if 'samsung' in filename or 'sdc' in filename:
        return extract_samsung_financials(pdf_path)
    elif 'lg' in filename or 'lgd' in filename:
        return extract_lgd_financials(pdf_path)
    else:
        return None, f"Unknown company in filename: {filename}"

def scan_pdf_directory():
    """Scan the PDF directory and return list of PDF files."""
    if not PDF_DIR.exists():
        return []
    return list(PDF_DIR.glob("*.pdf"))

# =============================================================================
# Database Functions
# =============================================================================

def save_financial_record(record):
    """Save a financial record to the database."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            INSERT OR REPLACE INTO company_financials
            (company, year, quarter, total_revenue_m, operating_income_m,
             operating_margin_pct, display_revenue_m, capex_m, ebitda_m, notes, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get('company'),
            record.get('year'),
            record.get('quarter'),
            record.get('total_revenue_m'),
            record.get('operating_income_m'),
            record.get('operating_margin_pct'),
            record.get('display_revenue_m'),
            record.get('capex_m'),
            record.get('ebitda_m'),
            record.get('notes'),
            record.get('source_file')
        ))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_financials():
    """Get all financial records from database."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("""
            SELECT * FROM company_financials
            ORDER BY year DESC, quarter DESC, company
        """, conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def delete_financial_record(record_id):
    """Delete a financial record."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM company_financials WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

# =============================================================================
# Page Header
# =============================================================================

st.markdown("""
    <h1>💰 Financial Intelligence</h1>
    <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
        Company financials with automated PDF extraction from IR reports
    </p>
""", unsafe_allow_html=True)

# Get theme colors
theme = get_plotly_theme()
colors = theme['color_discrete_sequence']

# =============================================================================
# Main Content Tabs
# =============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "PDF Processing", "Manual Entry", "Data Management"])

# =============================================================================
# Tab 1: Dashboard
# =============================================================================

with tab1:
    financials_df = get_all_financials()

    if len(financials_df) > 0:
        # Sidebar filters
        with st.sidebar:
            st.markdown("### Filters")
            selected_companies = st.multiselect(
                "Company",
                options=financials_df['company'].unique().tolist(),
                default=financials_df['company'].unique().tolist(),
                key="fin_company"
            )

            years = sorted(financials_df['year'].unique().tolist(), reverse=True)
            if len(years) > 1:
                year_range = st.select_slider(
                    "Year Range",
                    options=years,
                    value=(min(years), max(years)),
                    key="fin_year_range"
                )
            else:
                year_range = (years[0], years[0])

        # Filter data
        filtered_df = financials_df[
            (financials_df['company'].isin(selected_companies)) &
            (financials_df['year'] >= year_range[0]) &
            (financials_df['year'] <= year_range[1])
        ]

        # Summary Cards
        st.markdown("### Latest Results")
        latest = filtered_df.sort_values(['year', 'quarter'], ascending=False).groupby('company').first().reset_index()

        cols = st.columns(min(len(latest), 4))
        for i, (_, row) in enumerate(latest.iterrows()):
            with cols[i % len(cols)]:
                margin_color = "#34C759" if row.get('operating_margin_pct') and row['operating_margin_pct'] > 0 else "#FF3B30"
                rev_str = format_currency(row['total_revenue_m'] * 1e6) if pd.notna(row.get('total_revenue_m')) else 'N/A'
                margin_str = f"{row['operating_margin_pct']:.1f}%" if pd.notna(row.get('operating_margin_pct')) else 'N/A'
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FFFFFF 0%, #F5F5F7 100%);
                            border: 1px solid #E5E5E7; border-radius: 16px; padding: 1.25rem;">
                    <p style="color: #86868B; font-size: 0.9rem; margin-bottom: 0.5rem;">
                        {row['company']} {row['quarter']} {int(row['year'])}
                    </p>
                    <p style="font-size: 1.5rem; font-weight: 700; color: #1D1D1F; margin-bottom: 0.25rem;">
                        {rev_str}
                    </p>
                    <p style="color: {margin_color}; font-size: 0.9rem;">
                        Op Margin: {margin_str}
                    </p>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Revenue Trends")
            chart_df = filtered_df.copy()
            chart_df['period'] = chart_df['year'].astype(str) + ' ' + chart_df['quarter']
            chart_df = chart_df.sort_values(['year', 'quarter'])

            if len(chart_df) > 0:
                fig = px.line(chart_df, x='period', y='total_revenue_m', color='company',
                              markers=True, color_discrete_sequence=colors)
                fig.update_traces(hovertemplate='%{x}<br>Revenue: $%{y:,.0f}M<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(xaxis_title="Quarter", yaxis_title="Revenue ($M)", height=350,
                                  legend=dict(orientation='h', yanchor='bottom', y=1.02))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Operating Margin Trends")
            if len(chart_df) > 0:
                fig = px.line(chart_df, x='period', y='operating_margin_pct', color='company',
                              markers=True, color_discrete_sequence=colors)
                fig.update_traces(hovertemplate='%{x}<br>Margin: %{y:.1f}%<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(xaxis_title="Quarter", yaxis_title="Operating Margin (%)", height=350,
                                  legend=dict(orientation='h', yanchor='bottom', y=1.02))
                fig.add_hline(y=0, line_dash="dash", line_color="#FF3B30", annotation_text="Break-even")
                st.plotly_chart(fig, use_container_width=True)

        # CapEx chart
        capex_df = chart_df[chart_df['capex_m'].notna()]
        if len(capex_df) > 0:
            st.divider()
            st.markdown("#### Capital Expenditure")
            fig = px.bar(capex_df, x='period', y='capex_m', color='company',
                         barmode='group', color_discrete_sequence=colors)
            fig.update_traces(hovertemplate='%{x}<br>CapEx: $%{y:,.0f}M<extra></extra>')
            apply_chart_theme(fig)
            fig.update_layout(xaxis_title="Quarter", yaxis_title="CapEx ($M)", height=350,
                              legend=dict(orientation='h', yanchor='bottom', y=1.02))
            st.plotly_chart(fig, use_container_width=True)

        # Data table
        st.divider()
        st.markdown("#### Financial Records")
        display_df = filtered_df[['company', 'year', 'quarter', 'total_revenue_m',
                                   'operating_income_m', 'operating_margin_pct', 'capex_m', 'source_file']].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True,
            column_config={
                "company": st.column_config.TextColumn("Company"),
                "year": st.column_config.NumberColumn("Year", format="%d"),
                "quarter": st.column_config.TextColumn("Quarter"),
                "total_revenue_m": st.column_config.NumberColumn("Revenue ($M)", format="$%,.0f"),
                "operating_income_m": st.column_config.NumberColumn("Op Income ($M)", format="$%,.0f"),
                "operating_margin_pct": st.column_config.NumberColumn("Margin (%)", format="%.1f%%"),
                "capex_m": st.column_config.NumberColumn("CapEx ($M)", format="$%,.0f"),
                "source_file": st.column_config.TextColumn("Source")
            })

        csv = filtered_df.to_csv(index=False)
        st.download_button("Download CSV", csv, "financials_export.csv", "text/csv")

    else:
        st.info("No financial data available. Use the **PDF Processing** or **Manual Entry** tabs to add data.")

# =============================================================================
# Tab 2: PDF Processing
# =============================================================================

with tab2:
    st.markdown("### PDF Extraction")
    st.markdown(f"**PDF Directory:** `{PDF_DIR}`")
    st.caption(f"Directory exists: {PDF_DIR.exists()}")

    pdf_files = scan_pdf_directory()

    if pdf_files:
        st.success(f"Found {len(pdf_files)} PDF file(s)")
        for pdf in pdf_files:
            st.markdown(f"- `{pdf.name}`")

        st.divider()

        if st.button("🔍 Extract Data from PDFs", type="primary"):
            results = []
            errors = []
            progress = st.progress(0)
            status = st.empty()

            for i, pdf_path in enumerate(pdf_files):
                status.markdown(f"Processing: `{pdf_path.name}`...")
                progress.progress((i + 1) / len(pdf_files))
                data, error = extract_financials_from_pdf(str(pdf_path))
                if data and 'year' in data and 'quarter' in data:
                    results.append(data)
                else:
                    errors.append(f"{pdf_path.name}: {error or 'Missing year/quarter'}")

            status.empty()
            progress.empty()

            if results:
                st.markdown("### Extracted Data Preview")
                preview_df = pd.DataFrame(results)
                st.dataframe(preview_df, use_container_width=True, hide_index=True,
                    column_config={
                        "company": "Company",
                        "year": st.column_config.NumberColumn("Year", format="%d"),
                        "quarter": "Quarter",
                        "total_revenue_m": st.column_config.NumberColumn("Revenue ($M)", format="$%,.0f"),
                        "operating_income_m": st.column_config.NumberColumn("Op Income ($M)", format="$%,.0f"),
                        "operating_margin_pct": st.column_config.NumberColumn("Margin (%)", format="%.1f%%"),
                        "capex_m": st.column_config.NumberColumn("CapEx ($M)", format="$%,.0f"),
                        "source_file": "Source"
                    })

                st.session_state['extracted_financials'] = results

                if st.button("💾 Save to Database", type="primary"):
                    saved, skipped = 0, 0
                    for record in results:
                        success, _ = save_financial_record(record)
                        if success:
                            saved += 1
                        else:
                            skipped += 1
                    st.success(f"✅ {saved} records saved, {skipped} skipped")
                    st.rerun()

            if errors:
                st.warning("Some files had errors:")
                for err in errors:
                    st.markdown(f"- {err}")
    else:
        st.warning(f"No PDF files found in `{PDF_DIR}`")
        st.markdown("""
        **To add financial data:**
        1. Download quarterly earnings PDFs from Samsung and LG Display IR websites
        2. Save them to `source_data/financials/` with names like:
           - `Samsung_Q4_2025.pdf`
           - `LGD_Q3_2025.pdf`
        3. Return here and click "Extract Data from PDFs"
        """)

# =============================================================================
# Tab 3: Manual Entry
# =============================================================================

with tab3:
    st.markdown("### Manual Data Entry")

    with st.form("manual_entry_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            company = st.selectbox("Company", ["Samsung Display", "LG Display", "BOE", "AUO", "Innolux", "Other"])
        with col2:
            year = st.selectbox("Year", list(range(2026, 2019, -1)))
        with col3:
            quarter = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"])

        col1, col2 = st.columns(2)
        with col1:
            total_revenue = st.number_input("Total Revenue ($M)", min_value=0.0, step=100.0)
            operating_income = st.number_input("Operating Income ($M)", step=100.0)
            capex = st.number_input("CapEx ($M)", min_value=0.0, step=100.0)
        with col2:
            display_revenue = st.number_input("Display Segment Revenue ($M)", min_value=0.0, step=100.0)
            ebitda = st.number_input("EBITDA ($M)", step=100.0)
            notes = st.text_input("Notes")

        if st.form_submit_button("Save Record", type="primary"):
            margin = (operating_income / total_revenue * 100) if total_revenue > 0 else None
            record = {
                'company': company, 'year': year, 'quarter': quarter,
                'total_revenue_m': total_revenue or None,
                'operating_income_m': operating_income or None,
                'operating_margin_pct': margin,
                'display_revenue_m': display_revenue or None,
                'capex_m': capex or None,
                'ebitda_m': ebitda or None,
                'notes': notes or None,
                'source_file': 'Manual Entry'
            }
            success, error = save_financial_record(record)
            if success:
                st.success(f"✅ Saved {company} {quarter} {year}")
                st.rerun()
            else:
                st.error(f"Error: {error}")

# =============================================================================
# Tab 4: Data Management
# =============================================================================

with tab4:
    st.markdown("### Data Management")
    all_data = get_all_financials()

    if len(all_data) > 0:
        st.markdown(f"**Total Records:** {len(all_data)}")
        st.dataframe(all_data, use_container_width=True, hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID"),
                "company": "Company",
                "year": st.column_config.NumberColumn("Year", format="%d"),
                "quarter": "Quarter",
                "total_revenue_m": st.column_config.NumberColumn("Revenue ($M)", format="$%,.0f"),
                "operating_income_m": st.column_config.NumberColumn("Op Income ($M)", format="$%,.0f"),
                "operating_margin_pct": st.column_config.NumberColumn("Margin (%)", format="%.1f%%"),
                "source_file": "Source"
            })

        st.divider()
        st.markdown("#### Delete Record")
        col1, col2 = st.columns([3, 1])
        with col1:
            record_id = st.selectbox("Select record",
                options=all_data['id'].tolist(),
                format_func=lambda x: f"ID {x}: {all_data[all_data['id']==x]['company'].values[0]} {all_data[all_data['id']==x]['quarter'].values[0]} {int(all_data[all_data['id']==x]['year'].values[0])}")
        with col2:
            if st.button("🗑️ Delete"):
                delete_financial_record(record_id)
                st.success("Deleted")
                st.rerun()
    else:
        st.info("No records in database.")
