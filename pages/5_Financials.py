"""
Financials Page - Display Intelligence Dashboard
Company financials, revenue analysis, and financial metrics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import get_css, get_plotly_theme
from utils.database import DatabaseManager
from utils.exports import create_download_buttons

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

# Page header
st.markdown("""
    <h1>💰 Financial Intelligence</h1>
    <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
        Company financials, revenue trends, and profitability analysis
    </p>
""", unsafe_allow_html=True)

# Filters in sidebar
with st.sidebar:
    st.markdown("### Filters")

    manufacturer = st.selectbox(
        "Manufacturer",
        options=DatabaseManager.get_manufacturers(),
        key="fin_manufacturer"
    )

    st.divider()

    st.markdown("### Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start",
            value=date(2020, 1, 1),
            key="fin_start"
        )
    with col2:
        end_date = st.date_input(
            "End",
            value=date.today(),
            key="fin_end"
        )

# Load financial data
financials_df = DatabaseManager.get_financials(
    start_date=start_date.strftime("%Y-%m-%d"),
    end_date=end_date.strftime("%Y-%m-%d"),
    manufacturer=manufacturer
)

theme = get_plotly_theme()

# Main content
if len(financials_df) > 0:
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Profitability", "Company Details"])

    # Tab 1: Overview
    with tab1:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_revenue = financials_df['revenue_m'].sum()
            if total_revenue >= 1000:
                rev_str = f"${total_revenue/1000:.1f}B"
            else:
                rev_str = f"${total_revenue:.0f}M"
            st.metric("Total Revenue", rev_str)

        with col2:
            total_ebitda = financials_df['ebitda_m'].sum() if 'ebitda_m' in financials_df.columns else 0
            if total_ebitda >= 1000:
                ebitda_str = f"${total_ebitda/1000:.1f}B"
            else:
                ebitda_str = f"${total_ebitda:.0f}M"
            st.metric("Total EBITDA", ebitda_str)

        with col3:
            avg_margin = financials_df['operating_margin_pct'].mean() if 'operating_margin_pct' in financials_df.columns else 0
            st.metric("Avg Operating Margin", f"{avg_margin:.1f}%")

        with col4:
            total_capex = financials_df['capex_m'].sum() if 'capex_m' in financials_df.columns else 0
            if total_capex >= 1000:
                capex_str = f"${total_capex/1000:.1f}B"
            else:
                capex_str = f"${total_capex:.0f}M"
            st.metric("Total CapEx", capex_str)

        st.divider()

        # Revenue over time
        st.markdown("#### Revenue Trends")

        revenue_by_quarter = financials_df.groupby(['date', 'manufacturer'])['revenue_m'].sum().reset_index()

        fig = px.bar(
            revenue_by_quarter,
            x='date',
            y='revenue_m',
            color='manufacturer',
            color_discrete_sequence=theme['color_discrete_sequence']
        )
        fig.update_layout(
            **theme['layout'],
            xaxis_title="Quarter",
            yaxis_title="Revenue ($M)",
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            barmode='stack'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Revenue by manufacturer
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Revenue by Manufacturer")

            mfr_revenue = financials_df.groupby('manufacturer')['revenue_m'].sum().sort_values(ascending=False)

            fig = px.pie(
                values=mfr_revenue.values,
                names=mfr_revenue.index,
                color_discrete_sequence=theme['color_discrete_sequence'],
                hole=0.4
            )
            fig.update_layout(
                **theme['layout'],
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Revenue Rankings")

            mfr_table = financials_df.groupby('manufacturer').agg({
                'revenue_m': 'sum',
                'ebitda_m': 'sum',
                'operating_margin_pct': 'mean'
            }).reset_index()
            mfr_table.columns = ['Manufacturer', 'Revenue ($M)', 'EBITDA ($M)', 'Avg Margin (%)']
            mfr_table = mfr_table.sort_values('Revenue ($M)', ascending=False)

            st.dataframe(
                mfr_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Manufacturer": st.column_config.TextColumn("Manufacturer", width="medium"),
                    "Revenue ($M)": st.column_config.NumberColumn("Revenue ($M)", format="$%.0f"),
                    "EBITDA ($M)": st.column_config.NumberColumn("EBITDA ($M)", format="$%.0f"),
                    "Avg Margin (%)": st.column_config.NumberColumn("Margin (%)", format="%.1f")
                }
            )

    # Tab 2: Profitability
    with tab2:
        st.markdown("#### Operating Margin Trends")

        if 'operating_margin_pct' in financials_df.columns:
            margin_trends = financials_df.groupby(['date', 'manufacturer'])['operating_margin_pct'].mean().reset_index()

            fig = px.line(
                margin_trends,
                x='date',
                y='operating_margin_pct',
                color='manufacturer',
                color_discrete_sequence=theme['color_discrete_sequence'],
                markers=True
            )
            fig.update_layout(
                **theme['layout'],
                xaxis_title="Quarter",
                yaxis_title="Operating Margin (%)",
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02)
            )
            # Add break-even line
            fig.add_hline(y=0, line_dash="dash", line_color="#FF3B30", annotation_text="Break-even")
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### EBITDA by Manufacturer")

            if 'ebitda_m' in financials_df.columns:
                ebitda_by_mfr = financials_df.groupby('manufacturer')['ebitda_m'].sum().sort_values(ascending=True)

                fig = px.bar(
                    x=ebitda_by_mfr.values,
                    y=ebitda_by_mfr.index,
                    orientation='h',
                    color_discrete_sequence=theme['color_discrete_sequence']
                )
                fig.update_layout(
                    **theme['layout'],
                    showlegend=False,
                    xaxis_title="EBITDA ($M)",
                    yaxis_title="",
                    height=400
                )
                fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Margin Distribution")

            if 'operating_margin_pct' in financials_df.columns:
                fig = px.box(
                    financials_df,
                    x='manufacturer',
                    y='operating_margin_pct',
                    color='manufacturer',
                    color_discrete_sequence=theme['color_discrete_sequence']
                )
                fig.update_layout(
                    **theme['layout'],
                    showlegend=False,
                    xaxis_title="",
                    yaxis_title="Operating Margin (%)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

        # Profitability metrics table
        st.divider()
        st.markdown("#### Profitability Metrics by Company")

        profit_metrics = financials_df.groupby('manufacturer').agg({
            'revenue_m': ['sum', 'mean'],
            'ebitda_m': ['sum', 'mean'],
            'operating_margin_pct': ['mean', 'min', 'max']
        }).reset_index()

        profit_metrics.columns = [
            'Manufacturer', 'Total Revenue', 'Avg Quarterly Revenue',
            'Total EBITDA', 'Avg Quarterly EBITDA',
            'Avg Margin', 'Min Margin', 'Max Margin'
        ]

        st.dataframe(
            profit_metrics,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Manufacturer": st.column_config.TextColumn("Manufacturer"),
                "Total Revenue": st.column_config.NumberColumn("Total Rev ($M)", format="$%.0f"),
                "Avg Quarterly Revenue": st.column_config.NumberColumn("Avg Qtr Rev ($M)", format="$%.0f"),
                "Total EBITDA": st.column_config.NumberColumn("Total EBITDA ($M)", format="$%.0f"),
                "Avg Quarterly EBITDA": st.column_config.NumberColumn("Avg Qtr EBITDA ($M)", format="$%.0f"),
                "Avg Margin": st.column_config.NumberColumn("Avg Margin (%)", format="%.1f"),
                "Min Margin": st.column_config.NumberColumn("Min Margin (%)", format="%.1f"),
                "Max Margin": st.column_config.NumberColumn("Max Margin (%)", format="%.1f")
            }
        )

    # Tab 3: Company Details
    with tab3:
        st.markdown("#### Detailed Financial Records")

        display_cols = [
            'date', 'manufacturer', 'revenue_m', 'ebitda_m',
            'operating_margin_pct', 'capex_m'
        ]
        available_cols = [c for c in display_cols if c in financials_df.columns]

        st.dataframe(
            financials_df[available_cols],
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "date": st.column_config.TextColumn("Date", width="small"),
                "manufacturer": st.column_config.TextColumn("Manufacturer", width="medium"),
                "revenue_m": st.column_config.NumberColumn("Revenue ($M)", format="$%.0f"),
                "ebitda_m": st.column_config.NumberColumn("EBITDA ($M)", format="$%.0f"),
                "operating_margin_pct": st.column_config.NumberColumn("Margin (%)", format="%.1f"),
                "capex_m": st.column_config.NumberColumn("CapEx ($M)", format="$%.0f")
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)
        create_download_buttons(financials_df, "financials", "Financial Intelligence Report")

        # CapEx analysis
        if 'capex_m' in financials_df.columns:
            st.divider()
            st.markdown("#### Capital Expenditure Trends")

            capex_trends = financials_df.groupby('date')['capex_m'].sum().reset_index()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=capex_trends['date'],
                y=capex_trends['capex_m'],
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color=theme['color_discrete_sequence'][0], width=2),
                fillcolor='rgba(0, 122, 255, 0.1)'
            ))
            fig.update_layout(
                **theme['layout'],
                xaxis_title="Quarter",
                yaxis_title="CapEx ($M)",
                height=350,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

else:
    # Empty state - show placeholder content
    st.markdown("""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: #F5F5F7;
        border-radius: 20px;
        margin-top: 2rem;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">💰</div>
        <h2 style="color: #1D1D1F; margin-bottom: 0.5rem;">No Financial Data Yet</h2>
        <p style="color: #86868B; max-width: 400px; margin: 0 auto;">
            Financial data will appear here as it is added to the database.
            This section will include revenue, EBITDA, operating margins, and CapEx data.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show sample layout
    st.divider()
    st.markdown("### Sample Financial Layout")
    st.info("The following shows how financial data will be displayed when available:")

    # Sample metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style="background: #F5F5F7; border-radius: 16px; padding: 1.25rem; opacity: 0.6;">
            <p style="color: #86868B; font-size: 0.875rem; margin-bottom: 0.25rem;">Total Revenue</p>
            <p style="font-size: 2rem; font-weight: 700; color: #1D1D1F;">$24.5B</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #F5F5F7; border-radius: 16px; padding: 1.25rem; opacity: 0.6;">
            <p style="color: #86868B; font-size: 0.875rem; margin-bottom: 0.25rem;">Total EBITDA</p>
            <p style="font-size: 2rem; font-weight: 700; color: #1D1D1F;">$3.2B</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: #F5F5F7; border-radius: 16px; padding: 1.25rem; opacity: 0.6;">
            <p style="color: #86868B; font-size: 0.875rem; margin-bottom: 0.25rem;">Avg Margin</p>
            <p style="font-size: 2rem; font-weight: 700; color: #1D1D1F;">12.8%</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div style="background: #F5F5F7; border-radius: 16px; padding: 1.25rem; opacity: 0.6;">
            <p style="color: #86868B; font-size: 0.875rem; margin-bottom: 0.25rem;">Total CapEx</p>
            <p style="font-size: 2rem; font-weight: 700; color: #1D1D1F;">$8.7B</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Sample company table
    sample_data = pd.DataFrame({
        'Manufacturer': ['BOE', 'Samsung Display', 'LG Display', 'AUO', 'Innolux'],
        'Revenue ($M)': [12500, 8200, 5800, 3200, 2800],
        'EBITDA ($M)': [1800, 950, 420, 280, 190],
        'Margin (%)': [14.4, 11.6, 7.2, 8.8, 6.8]
    })

    st.markdown("#### Sample Company Financials")
    st.dataframe(
        sample_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Manufacturer": st.column_config.TextColumn("Manufacturer"),
            "Revenue ($M)": st.column_config.NumberColumn("Revenue ($M)", format="$%.0f"),
            "EBITDA ($M)": st.column_config.NumberColumn("EBITDA ($M)", format="$%.0f"),
            "Margin (%)": st.column_config.NumberColumn("Margin (%)", format="%.1f")
        }
    )
