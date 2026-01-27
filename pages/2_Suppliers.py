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

from utils.styling import (
    get_css, get_plotly_theme, apply_chart_theme,
    format_currency, format_with_commas, format_percent, format_integer, format_units,
    get_process_step, get_process_step_number, get_process_step_name, PROCESS_STEP_MAPPING
)
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


# Get factory list for filter
@st.cache_data(ttl=300)
def get_factory_list():
    """Get list of factories with equipment orders."""
    import sqlite3
    conn = sqlite3.connect(Path(__file__).parent.parent / "displayintel.db")
    result = pd.read_sql('''
        SELECT DISTINCT manufacturer || ' ' || factory as factory_display,
               manufacturer, factory
        FROM equipment_orders
        WHERE factory IS NOT NULL AND factory != ''
        ORDER BY manufacturer, factory
    ''', conn)
    conn.close()
    return ['All'] + result['factory_display'].tolist()


# Filters in sidebar
with st.sidebar:
    st.markdown("### Filters")

    manufacturer = st.selectbox(
        "Manufacturer",
        options=DatabaseManager.get_manufacturers(),
        key="supplier_manufacturer"
    )

    # Factory filter
    factory_options = get_factory_list()
    selected_factory = st.selectbox(
        "Factory",
        options=factory_options,
        key="supplier_factory"
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
            options=list(range(2018, 2029)),
            index=0,
            key="supplier_start_year"
        )
    with col2:
        end_year = st.selectbox(
            "End Year",
            options=list(range(2018, 2029)),
            index=8,
            key="supplier_end_year"
        )


# Parse factory selection
factory_filter = None
factory_mfr = None
if selected_factory and selected_factory != 'All':
    parts = selected_factory.split(' ', 1)
    if len(parts) == 2:
        factory_mfr, factory_filter = parts


# Load equipment orders data
orders_df = DatabaseManager.get_equipment_orders(
    start_year=start_year,
    end_year=end_year,
    manufacturer=manufacturer if not factory_mfr else factory_mfr,
    vendor=vendor,
    equipment_type=equipment_type
)

# Apply factory filter if selected
if factory_filter:
    orders_df = orders_df[orders_df['factory'] == factory_filter]


# Add process step columns
if len(orders_df) > 0:
    orders_df['process_step_num'] = orders_df['equipment_type'].apply(get_process_step_number)
    orders_df['process_step_name'] = orders_df['equipment_type'].apply(get_process_step_name)
    orders_df['process_step'] = orders_df.apply(
        lambda x: f"{x['process_step_num']}. {x['process_step_name']}", axis=1
    )


# Get theme colors
theme = get_plotly_theme()
colors = theme['color_discrete_sequence']


# Factory-specific summary view
if factory_filter and len(orders_df) > 0:
    st.markdown(f"### {factory_mfr} {factory_filter} Equipment Summary")

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        total_orders = len(orders_df)
        st.metric("Total Orders", format_with_commas(total_orders))

    with col2:
        total_spend = orders_df['amount_usd'].sum()
        st.metric("Total Capex", format_currency(total_spend))

    with col3:
        total_units = orders_df['units'].sum() if orders_df['units'].notna().any() else 0
        st.metric("Total Equipment Units", format_with_commas(total_units) if total_units > 0 else '-')

    st.divider()

    # Process step summary table
    st.markdown("#### By Process Step")

    # Calculate summary by process step
    process_summary = orders_df.groupby(['process_step_num', 'process_step_name']).agg({
        'amount_usd': 'sum',
        'id': 'count',
        'units': 'sum',
        'vendor': lambda x: x.value_counts().index[0] if len(x) > 0 else 'Unknown'
    }).reset_index()

    # Get top vendor with count for each process step
    def get_top_vendor_info(df, step_num):
        step_data = df[df['process_step_num'] == step_num]
        if len(step_data) == 0:
            return '-'
        vendor_counts = step_data[step_data['vendor'].notna() & (step_data['vendor'] != 'Unknown')]['vendor'].value_counts()
        if len(vendor_counts) == 0:
            return '-'
        top_vendor = vendor_counts.index[0]
        top_count = vendor_counts.iloc[0]
        return f"{top_vendor} ({top_count})"

    process_summary['top_vendor'] = process_summary['process_step_num'].apply(
        lambda x: get_top_vendor_info(orders_df, x)
    )

    process_summary = process_summary.sort_values('process_step_num')
    process_summary.columns = ['Step', 'Process', 'Amount', 'Orders', 'Qty', 'vendor_raw', 'Top Supplier']

    # Format for display
    display_df = process_summary[['Step', 'Process', 'Amount', 'Orders', 'Qty', 'Top Supplier']].copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Step": st.column_config.NumberColumn("Step", width="small", format="%d"),
            "Process": st.column_config.TextColumn("Process", width="medium"),
            "Amount": st.column_config.NumberColumn("Amount", format="$%.1fM", width="small"),
            "Orders": st.column_config.NumberColumn("Orders", format="%d", width="small"),
            "Qty": st.column_config.NumberColumn("Qty", format="%d", width="small"),
            "Top Supplier": st.column_config.TextColumn("Top Supplier", width="medium")
        }
    )

    # Convert Amount to millions for display
    display_df['Amount'] = display_df['Amount'] / 1e6

    st.divider()


# Main content tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Vendor Analysis", "Order Details"])

# Tab 1: Overview
with tab1:
    if len(orders_df) > 0:
        # Summary metrics (if not already shown for factory view)
        if not factory_filter:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_orders = len(orders_df)
                st.metric("Total Orders", format_with_commas(total_orders))

            with col2:
                total_spend = orders_df['amount_usd'].sum()
                st.metric("Total Spend", format_currency(total_spend))

            with col3:
                total_units = orders_df['units'].sum() if orders_df['units'].notna().any() else 0
                st.metric("Total Units", format_with_commas(total_units) if total_units > 0 else '-')

            with col4:
                valid_vendors = orders_df[orders_df['vendor'].notna() & (orders_df['vendor'] != '') & (orders_df['vendor'] != 'Unknown')]
                unique_vendors = valid_vendors['vendor'].nunique()
                st.metric("Unique Vendors", format_with_commas(unique_vendors))

            st.divider()

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Equipment Spend by Year")

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
            st.markdown("#### Spend by Process Step")

            valid_steps = orders_df[orders_df['process_step_name'].notna()]
            step_spend = valid_steps.groupby('process_step_name')['amount_usd'].sum().reset_index()
            step_spend.columns = ['Process', 'Amount']
            step_spend = step_spend.nlargest(8, 'Amount')

            if len(step_spend) > 0:
                fig = px.pie(
                    step_spend,
                    values='Amount',
                    names='Process',
                    color_discrete_sequence=colors,
                    hole=0.4
                )
                fig.update_traces(hovertemplate='%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Spend by equipment type
        st.markdown("#### Top Equipment Types by Spend")

        valid_types = orders_df[orders_df['equipment_type'].notna() & (orders_df['equipment_type'] != '')]
        type_spend = valid_types.groupby('equipment_type').agg({
            'amount_usd': 'sum',
            'id': 'count',
            'units': 'sum',
            'process_step': 'first'
        }).reset_index()
        type_spend.columns = ['Equipment Type', 'Total Spend', 'Orders', 'Units', 'Process Step']
        type_spend = type_spend.nlargest(15, 'Total Spend')

        if len(type_spend) > 0:
            fig = px.bar(
                type_spend,
                x='Total Spend',
                y='Equipment Type',
                orientation='h',
                color='Process Step',
                color_discrete_sequence=colors
            )
            fig.update_traces(hovertemplate='%{y}<br>$%{x:,.0f}<extra></extra>')
            apply_chart_theme(fig)
            fig.update_layout(
                showlegend=True,
                xaxis_title="Total Spend (USD)",
                yaxis_title="",
                height=500,
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No equipment order data available for the selected filters.")


# Tab 2: Vendor Analysis
with tab2:
    if len(orders_df) > 0:
        st.markdown("#### Top Vendors by Total Spend")

        vendor_spend = DatabaseManager.get_equipment_spend_by_vendor(
            start_year=start_year,
            end_year=end_year
        )

        # Apply factory filter to vendor analysis
        if factory_filter:
            vendor_agg = orders_df[orders_df['vendor'].notna() & (orders_df['vendor'] != '') & (orders_df['vendor'] != 'Unknown')].groupby('vendor').agg({
                'amount_usd': 'sum',
                'units': 'sum',
                'id': 'count'
            }).reset_index()
            vendor_agg.columns = ['vendor', 'total_spend', 'total_units', 'order_count']
            vendor_agg = vendor_agg.sort_values('total_spend', ascending=False)
            vendor_spend = vendor_agg

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

            vendor_display = vendor_spend.copy()
            vendor_display['avg_order_value'] = vendor_display['total_spend'] / vendor_display['order_count']

            st.dataframe(
                vendor_display.head(20),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "vendor": st.column_config.TextColumn("Vendor", width="medium"),
                    "total_spend": st.column_config.NumberColumn("Total Spend", format="$%,.0f"),
                    "total_units": st.column_config.NumberColumn("Total Units", format="%,.0f"),
                    "order_count": st.column_config.NumberColumn("Orders", format="%d"),
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

        # Sort by process step, then amount
        display_df = orders_df.sort_values(['process_step_num', 'amount_usd'], ascending=[True, False])

        # Display columns with process step
        display_cols = [
            'po_year', 'po_quarter', 'manufacturer', 'factory', 'vendor',
            'process_step', 'equipment_type', 'units', 'amount_usd'
        ]
        available_cols = [c for c in display_cols if c in display_df.columns]

        st.dataframe(
            display_df[available_cols].head(500),
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "po_year": st.column_config.NumberColumn("Year", format="%d", width="small"),
                "po_quarter": st.column_config.TextColumn("Qtr", width="small"),
                "manufacturer": st.column_config.TextColumn("Mfr", width="small"),
                "factory": st.column_config.TextColumn("Factory", width="small"),
                "vendor": st.column_config.TextColumn("Vendor", width="medium"),
                "process_step": st.column_config.TextColumn("Process Step", width="medium"),
                "equipment_type": st.column_config.TextColumn("Equipment Type", width="medium"),
                "units": st.column_config.NumberColumn("Qty", format="%d", width="small"),
                "amount_usd": st.column_config.NumberColumn("Amount", format="$%,.0f")
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)
        create_download_buttons(orders_df, "equipment_orders", "Equipment Orders Report")

        # Summary by process step
        st.divider()
        st.markdown("#### Spend by Process Step")

        process_agg = orders_df.groupby(['process_step_num', 'process_step_name']).agg({
            'amount_usd': 'sum',
            'units': 'sum',
            'id': 'count'
        }).reset_index()
        process_agg.columns = ['Step', 'Process', 'Total Spend', 'Total Units', 'Order Count']
        process_agg = process_agg.sort_values('Step')

        if len(process_agg) > 0:
            fig = px.bar(
                process_agg,
                x='Process',
                y='Total Spend',
                color='Process',
                color_discrete_sequence=colors
            )
            fig.update_traces(
                hovertemplate='%{x}<br>Spend: $%{y:,.0f}<extra></extra>'
            )
            apply_chart_theme(fig)
            fig.update_layout(
                showlegend=False,
                xaxis_title="",
                yaxis_title="Total Spend (USD)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No order data available for the selected filters.")
