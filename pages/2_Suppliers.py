"""
Suppliers Page - Display Intelligence Dashboard
Equipment vendors, purchase orders, and supply chain analytics.
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
    page_title="Suppliers - Display Intelligence",
    page_icon="🔧",
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
    <h1>🔧 Supplier Intelligence</h1>
    <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
        Equipment vendors, purchase orders, and supply chain analytics
    </p>
""", unsafe_allow_html=True)

# Filters in sidebar
with st.sidebar:
    st.markdown("### Filters")

    manufacturer = st.selectbox(
        "Manufacturer",
        options=DatabaseManager.get_manufacturers(),
        key="supplier_manufacturer"
    )

    vendor = st.selectbox(
        "Vendor",
        options=DatabaseManager.get_vendors(),
        key="supplier_vendor"
    )

    equipment_type = st.selectbox(
        "Equipment Type",
        options=DatabaseManager.get_equipment_types(),
        key="supplier_equipment"
    )

    st.divider()

    st.markdown("### Date Range")
    min_date, max_date = DatabaseManager.get_date_range()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start",
            value=date(2020, 1, 1),
            key="supplier_start"
        )
    with col2:
        end_date = st.date_input(
            "End",
            value=date.today(),
            key="supplier_end"
        )

# Load equipment orders data
orders_df = DatabaseManager.get_equipment_orders(
    start_date=start_date.strftime("%Y-%m-%d"),
    end_date=end_date.strftime("%Y-%m-%d"),
    manufacturer=manufacturer,
    vendor=vendor,
    equipment_type=equipment_type
)

theme = get_plotly_theme()

# Main content tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Vendor Analysis", "Order Details"])

# Tab 1: Overview
with tab1:
    if len(orders_df) > 0:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_orders = len(orders_df)
            st.metric("Total Orders", f"{total_orders:,}")

        with col2:
            total_spend = orders_df['amount_usd'].sum()
            if total_spend >= 1_000_000_000:
                spend_str = f"${total_spend/1_000_000_000:.1f}B"
            elif total_spend >= 1_000_000:
                spend_str = f"${total_spend/1_000_000:.0f}M"
            else:
                spend_str = f"${total_spend:,.0f}"
            st.metric("Total Spend", spend_str)

        with col3:
            total_units = orders_df['units'].sum()
            st.metric("Total Units", f"{total_units:,}")

        with col4:
            unique_vendors = orders_df['vendor'].nunique()
            st.metric("Unique Vendors", unique_vendors)

        st.divider()

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Equipment Spend by Year")

            orders_df['year'] = pd.to_datetime(orders_df['po_date']).dt.year
            spend_by_year = orders_df.groupby('year')['amount_usd'].sum().reset_index()

            fig = px.bar(
                spend_by_year,
                x='year',
                y='amount_usd',
                color_discrete_sequence=theme['color_discrete_sequence']
            )
            fig.update_layout(
                **theme['layout'],
                showlegend=False,
                xaxis_title="Year",
                yaxis_title="Spend (USD)",
                height=350
            )
            fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Orders by Equipment Type")

            type_counts = orders_df.groupby('equipment_type').agg({
                'amount_usd': 'sum',
                'id': 'count'
            }).reset_index()
            type_counts.columns = ['Equipment Type', 'Total Spend', 'Order Count']
            type_counts = type_counts.nlargest(10, 'Total Spend')

            fig = px.pie(
                type_counts,
                values='Total Spend',
                names='Equipment Type',
                color_discrete_sequence=theme['color_discrete_sequence'],
                hole=0.4
            )
            fig.update_layout(
                **theme['layout'],
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Spend over time trend
        st.markdown("#### Equipment Spending Trend")

        orders_df['po_month'] = pd.to_datetime(orders_df['po_date']).dt.to_period('M').astype(str)
        monthly_spend = orders_df.groupby('po_month')['amount_usd'].sum().reset_index()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_spend['po_month'],
            y=monthly_spend['amount_usd'],
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color=theme['color_discrete_sequence'][0], width=2),
            fillcolor='rgba(0, 122, 255, 0.1)',
            marker=dict(size=4)
        ))
        fig.update_layout(
            **theme['layout'],
            xaxis_title="Month",
            yaxis_title="Spend (USD)",
            height=350,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No equipment order data available for the selected filters.")


# Tab 2: Vendor Analysis
with tab2:
    if len(orders_df) > 0:
        # Vendor spend ranking
        st.markdown("#### Top Vendors by Total Spend")

        vendor_spend = DatabaseManager.get_equipment_spend_by_vendor(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )

        if len(vendor_spend) > 0:
            top_vendors = vendor_spend.head(15)

            fig = px.bar(
                top_vendors,
                x='total_spend',
                y='vendor',
                orientation='h',
                color_discrete_sequence=theme['color_discrete_sequence']
            )
            fig.update_layout(
                **theme['layout'],
                showlegend=False,
                xaxis_title="Total Spend (USD)",
                yaxis_title="",
                height=500
            )
            fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Vendor metrics table
            st.markdown("#### Vendor Performance Metrics")

            vendor_display = vendor_spend.copy()
            vendor_display['avg_order_value'] = vendor_display['total_spend'] / vendor_display['order_count']

            st.dataframe(
                vendor_display.head(20),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "vendor": st.column_config.TextColumn("Vendor", width="medium"),
                    "total_spend": st.column_config.NumberColumn("Total Spend", format="$%.0f"),
                    "total_units": st.column_config.NumberColumn("Total Units", format="%.0f"),
                    "order_count": st.column_config.NumberColumn("Orders", format="%.0f"),
                    "avg_order_value": st.column_config.NumberColumn("Avg Order Value", format="$%.0f")
                }
            )

            create_download_buttons(vendor_spend, "vendor_analysis", "Vendor Analysis Report")

        # Vendor market share
        st.divider()
        st.markdown("#### Vendor Market Share")

        col1, col2 = st.columns(2)

        with col1:
            if len(vendor_spend) > 0:
                top_10_vendors = vendor_spend.head(10)
                other_spend = vendor_spend.iloc[10:]['total_spend'].sum() if len(vendor_spend) > 10 else 0

                pie_data = pd.concat([
                    top_10_vendors[['vendor', 'total_spend']],
                    pd.DataFrame({'vendor': ['Other'], 'total_spend': [other_spend]})
                ]) if other_spend > 0 else top_10_vendors[['vendor', 'total_spend']]

                fig = px.pie(
                    pie_data,
                    values='total_spend',
                    names='vendor',
                    color_discrete_sequence=theme['color_discrete_sequence'],
                    hole=0.4
                )
                fig.update_layout(
                    **theme['layout'],
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("##### Key Insights")
            if len(vendor_spend) > 0:
                top_vendor = vendor_spend.iloc[0]
                total_market = vendor_spend['total_spend'].sum()
                top_share = (top_vendor['total_spend'] / total_market * 100) if total_market > 0 else 0

                st.markdown(f"""
                <div style="background: #F5F5F7; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
                    <p style="color: #86868B; margin-bottom: 0.5rem;">Top Vendor</p>
                    <p style="font-size: 1.5rem; font-weight: 600; color: #1D1D1F;">{top_vendor['vendor']}</p>
                    <p style="color: #007AFF;">{top_share:.1f}% market share</p>
                </div>
                """, unsafe_allow_html=True)

                top_3_share = vendor_spend.head(3)['total_spend'].sum() / total_market * 100 if total_market > 0 else 0
                st.markdown(f"""
                <div style="background: #F5F5F7; border-radius: 12px; padding: 1.5rem;">
                    <p style="color: #86868B; margin-bottom: 0.5rem;">Market Concentration</p>
                    <p style="font-size: 1.5rem; font-weight: 600; color: #1D1D1F;">{top_3_share:.1f}%</p>
                    <p style="color: #86868B;">Top 3 vendors share</p>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.info("No vendor data available for the selected filters.")


# Tab 3: Order Details
with tab3:
    if len(orders_df) > 0:
        st.markdown("#### Equipment Purchase Orders")

        # Display columns
        display_cols = [
            'po_date', 'manufacturer', 'factory', 'vendor',
            'equipment_type', 'tool_category', 'units', 'amount_usd'
        ]
        available_cols = [c for c in display_cols if c in orders_df.columns]

        st.dataframe(
            orders_df[available_cols].head(500),
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "po_date": st.column_config.TextColumn("PO Date", width="small"),
                "manufacturer": st.column_config.TextColumn("Manufacturer", width="small"),
                "factory": st.column_config.TextColumn("Factory", width="medium"),
                "vendor": st.column_config.TextColumn("Vendor", width="medium"),
                "equipment_type": st.column_config.TextColumn("Equipment", width="medium"),
                "tool_category": st.column_config.TextColumn("Category", width="small"),
                "units": st.column_config.NumberColumn("Units", format="%.0f"),
                "amount_usd": st.column_config.NumberColumn("Amount (USD)", format="$%.0f")
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)
        create_download_buttons(orders_df, "equipment_orders", "Equipment Orders Report")

        # Summary by manufacturer
        st.divider()
        st.markdown("#### Orders by Manufacturer")

        mfr_summary = orders_df.groupby('manufacturer').agg({
            'amount_usd': 'sum',
            'units': 'sum',
            'id': 'count'
        }).reset_index()
        mfr_summary.columns = ['Manufacturer', 'Total Spend', 'Total Units', 'Order Count']
        mfr_summary = mfr_summary.sort_values('Total Spend', ascending=False)

        fig = px.bar(
            mfr_summary.head(15),
            x='Manufacturer',
            y='Total Spend',
            color_discrete_sequence=theme['color_discrete_sequence']
        )
        fig.update_layout(
            **theme['layout'],
            showlegend=False,
            xaxis_title="",
            yaxis_title="Total Spend (USD)",
            height=350
        )
        fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No order data available for the selected filters.")
