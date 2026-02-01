"""
Suppliers Page - Display Intelligence Dashboard
Equipment vendors, purchase orders, and supply chain analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import get_css, get_plotly_theme, apply_chart_theme, format_with_commas
from utils.database import (
    DatabaseManager,
    format_currency,
    format_integer,
    format_units,
    get_process_step,
    get_process_step_name,
    PROCESS_STEP_NAMES
)
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

    st.markdown("### Year Range")
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox(
            "Start Year",
            options=list(range(2018, 2027)),
            index=0,
            key="supplier_start_year"
        )
    with col2:
        end_year = st.selectbox(
            "End Year",
            options=list(range(2018, 2027)),
            index=8,  # Default to 2026
            key="supplier_end_year"
        )

# Load equipment orders data
orders_df = DatabaseManager.get_equipment_orders(
    start_year=start_year,
    end_year=end_year,
    manufacturer=manufacturer,
    vendor=vendor,
    equipment_type=equipment_type
)

# Factory filter in sidebar (after loading data to get factory options)
with st.sidebar:
    st.divider()
    factories_list = ["All"] + sorted(orders_df[orders_df['factory'].notna() & (orders_df['factory'] != '')]['factory'].unique().tolist())
    factory = st.selectbox("Factory", options=factories_list, key="supplier_factory")

    # Process step filter
    process_steps_list = ["All"] + [f"{k}: {v}" for k, v in sorted(PROCESS_STEP_NAMES.items())]
    process_step_filter = st.selectbox("Process Step", options=process_steps_list, key="supplier_process_step")

# Apply factory filter
if factory != "All":
    orders_df = orders_df[orders_df['factory'] == factory]

# Apply process step filter
if process_step_filter != "All":
    step_num = int(process_step_filter.split(":")[0])
    orders_df['_process_step'] = orders_df['equipment_type'].apply(get_process_step)
    orders_df = orders_df[orders_df['_process_step'] == step_num]
    orders_df = orders_df.drop(columns=['_process_step'])

# Add process_step column once (reused in Tab 1 and Tab 3)
if len(orders_df) > 0:
    orders_df = orders_df.copy()  # Copy once here to avoid SettingWithCopyWarning
    orders_df['process_step'] = orders_df['equipment_type'].apply(get_process_step_name)

# Get theme colors
theme = get_plotly_theme()
colors = theme['color_discrete_sequence']

# Main content tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Vendor Analysis", "Order Details"])

# Tab 1: Overview
with tab1:
    if len(orders_df) > 0:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_orders = len(orders_df)
            st.metric("Total Orders", format_with_commas(total_orders))

        with col2:
            total_spend = orders_df['amount_usd'].sum()
            st.metric("Total Spend", format_currency(total_spend))

        with col3:
            total_units = orders_df['units'].sum()
            st.metric("Total Units", format_with_commas(total_units))

        with col4:
            # Filter out NULL/empty vendors before counting
            valid_vendors = orders_df[orders_df['vendor'].notna() & (orders_df['vendor'] != '') & (orders_df['vendor'] != 'Unknown')]
            unique_vendors = valid_vendors['vendor'].nunique()
            st.metric("Unique Vendors", format_with_commas(unique_vendors))

        st.divider()

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Equipment Spend by Year")

            # Filter valid years and group
            valid_years = orders_df[orders_df['po_year'].notna()]
            spend_by_year = valid_years.groupby('po_year')['amount_usd'].sum().reset_index()
            spend_by_year.columns = ['year', 'amount_usd']

            if len(spend_by_year) > 0:
                fig = px.bar(
                    spend_by_year,
                    x='year',
                    y='amount_usd'
                )
                fig.update_traces(
                    marker_color=colors[0],
                    hovertemplate='Year %{x}<br>Spend: $%{y:,.0f}<extra></extra>'
                )
                apply_chart_theme(fig)
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Year",
                    yaxis_title="Spend (USD)",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Orders by Equipment Type")

            # Filter out NULL/empty equipment types
            valid_types = orders_df[orders_df['equipment_type'].notna() & (orders_df['equipment_type'] != '')]
            type_counts = valid_types.groupby('equipment_type').agg({
                'amount_usd': 'sum',
                'id': 'count'
            }).reset_index()
            type_counts.columns = ['Equipment Type', 'Total Spend', 'Order Count']
            type_counts = type_counts.nlargest(10, 'Total Spend')

            if len(type_counts) > 0:
                fig = px.pie(
                    type_counts,
                    values='Total Spend',
                    names='Equipment Type',
                    color_discrete_sequence=colors,
                    hole=0.4
                )
                fig.update_traces(hovertemplate='%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Spend by Process Step
        st.markdown("#### Spend by Process Step")

        # process_step column already added after data load (performance optimization)
        step_spend = orders_df.groupby('process_step')['amount_usd'].sum().reset_index()
        step_spend.columns = ['Process Step', 'Total Spend']
        step_spend = step_spend.sort_values('Total Spend', ascending=True)

        if len(step_spend) > 0:
            fig = px.bar(
                step_spend,
                x='Total Spend',
                y='Process Step',
                orientation='h'
            )
            fig.update_traces(
                marker_color=colors[1],
                hovertemplate='%{y}<br>Spend: $%{x:,.0f}<extra></extra>'
            )
            apply_chart_theme(fig)
            fig.update_layout(
                showlegend=False,
                xaxis_title="Total Spend (USD)",
                yaxis_title="",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Spend over time trend
        st.markdown("#### Equipment Spending Trend by Quarter")

        # Filter valid quarters and group
        valid_quarters = orders_df[orders_df['po_year'].notna() & orders_df['po_quarter'].notna()]
        quarterly_spend = valid_quarters.groupby(['po_year', 'po_quarter'])['amount_usd'].sum().reset_index()
        quarterly_spend = quarterly_spend.sort_values(['po_year', 'po_quarter'])
        quarterly_spend['period'] = quarterly_spend['po_year'].astype(int).astype(str) + ' ' + quarterly_spend['po_quarter'].astype(str)

        if len(quarterly_spend) > 0:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=quarterly_spend['period'].tolist(),
                y=quarterly_spend['amount_usd'].tolist(),
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color=colors[0], width=2),
                fillcolor='rgba(0, 122, 255, 0.1)',
                marker=dict(size=4),
                hovertemplate='%{x}<br>Spend: $%{y:,.0f}<extra></extra>'
            ))
            apply_chart_theme(fig)
            fig.update_layout(
                xaxis_title="Quarter",
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
            start_year=start_year,
            end_year=end_year
        )

        # Filter out NULL/empty/Unknown vendors
        if len(vendor_spend) > 0:
            vendor_spend = vendor_spend[
                vendor_spend['vendor'].notna() &
                (vendor_spend['vendor'] != '') &
                (vendor_spend['vendor'] != 'Unknown')
            ]

        if len(vendor_spend) > 0:
            top_vendors = vendor_spend.head(15)

            fig = px.bar(
                top_vendors,
                x='total_spend',
                y='vendor',
                orientation='h'
            )
            fig.update_traces(
                marker_color=colors[0],
                hovertemplate='%{y}<br>Total Spend: $%{x:,.0f}<extra></extra>'
            )
            apply_chart_theme(fig)
            fig.update_layout(
                showlegend=False,
                xaxis_title="Total Spend (USD)",
                yaxis_title="",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Vendor metrics table
            st.markdown("#### Vendor Performance Metrics")

            # Add calculated column directly (no copy needed - vendor_spend not used raw after this)
            vendor_spend['avg_order_value'] = vendor_spend['total_spend'] / vendor_spend['order_count']

            st.dataframe(
                vendor_spend.head(20),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "vendor": st.column_config.TextColumn("Vendor", width="medium"),
                    "total_spend": st.column_config.NumberColumn("Total Spend", format="$%,.0f"),
                    "total_units": st.column_config.NumberColumn("Total Units", format="%,.0f"),
                    "order_count": st.column_config.NumberColumn("Orders", format="%,.0f"),
                    "avg_order_value": st.column_config.NumberColumn("Avg Order Value", format="$%,.0f")
                }
            )

            create_download_buttons(vendor_spend, "vendor_analysis", "Vendor Analysis Report")

            # Vendor market share
            st.divider()
            st.markdown("#### Vendor Market Share")

            col1, col2 = st.columns(2)

            with col1:
                top_10_vendors = vendor_spend.head(10)
                other_spend = vendor_spend.iloc[10:]['total_spend'].sum() if len(vendor_spend) > 10 else 0

                if other_spend > 0:
                    pie_data = pd.concat([
                        top_10_vendors[['vendor', 'total_spend']],
                        pd.DataFrame({'vendor': ['Other'], 'total_spend': [other_spend]})
                    ])
                else:
                    pie_data = top_10_vendors[['vendor', 'total_spend']]

                fig = px.pie(
                    pie_data,
                    values='total_spend',
                    names='vendor',
                    color_discrete_sequence=colors,
                    hole=0.4
                )
                fig.update_traces(hovertemplate='%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("##### Key Insights")
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

    else:
        st.info("No vendor data available for the selected filters.")


# Tab 3: Order Details
with tab3:
    if len(orders_df) > 0:
        st.markdown("#### Equipment Purchase Orders")

        # process_step column already added after data load (performance optimization)

        # Display columns - use po_year instead of po_date
        display_cols = [
            'po_year', 'po_quarter', 'manufacturer', 'factory', 'vendor',
            'equipment_type', 'process_step', 'units', 'amount_usd'
        ]
        available_cols = [c for c in display_cols if c in orders_df.columns]

        st.dataframe(
            orders_df[available_cols].head(500),
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "po_year": st.column_config.NumberColumn("Year", format="%d"),
                "po_quarter": st.column_config.TextColumn("Quarter", width="small"),
                "manufacturer": st.column_config.TextColumn("Manufacturer", width="small"),
                "factory": st.column_config.TextColumn("Factory", width="medium"),
                "vendor": st.column_config.TextColumn("Vendor", width="medium"),
                "equipment_type": st.column_config.TextColumn("Equipment", width="medium"),
                "process_step": st.column_config.TextColumn("Process Step", width="medium"),
                "units": st.column_config.NumberColumn("Units", format="%,.0f"),
                "amount_usd": st.column_config.NumberColumn("Amount (USD)", format="$%,.0f")
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)
        create_download_buttons(orders_df, "equipment_orders", "Equipment Orders Report")

        # Summary by manufacturer
        st.divider()
        st.markdown("#### Orders by Manufacturer")

        # Filter out NULL/empty manufacturers
        valid_mfr = orders_df[orders_df['manufacturer'].notna() & (orders_df['manufacturer'] != '')]
        mfr_summary = valid_mfr.groupby('manufacturer').agg({
            'amount_usd': 'sum',
            'units': 'sum',
            'id': 'count'
        }).reset_index()
        mfr_summary.columns = ['Manufacturer', 'Total Spend', 'Total Units', 'Order Count']
        mfr_summary = mfr_summary.sort_values('Total Spend', ascending=False)

        if len(mfr_summary) > 0:
            fig = px.bar(
                mfr_summary.head(15),
                x='Manufacturer',
                y='Total Spend'
            )
            fig.update_traces(
                marker_color=colors[0],
                hovertemplate='%{x}<br>Spend: $%{y:,.0f}<extra></extra>'
            )
            apply_chart_theme(fig)
            fig.update_layout(
                showlegend=False,
                xaxis_title="",
                yaxis_title="Total Spend (USD)",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No order data available for the selected filters.")
