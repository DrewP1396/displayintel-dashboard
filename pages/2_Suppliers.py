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

# Check authentication (restore session from cookie if available)

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

    # Factory filter - only show when manufacturer is selected
    factory = "All"
    if manufacturer != "All":
        # Get factories for this manufacturer
        factory_options = DatabaseManager.get_factory_names(manufacturer)
        factory = st.selectbox(
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

    # Process step filter
    st.divider()
    process_steps_list = ["All"] + [f"{k}: {v}" for k, v in sorted(PROCESS_STEP_NAMES.items())]
    process_step_filter = st.selectbox("Process Step", options=process_steps_list, key="supplier_process_step")

# Load equipment orders data
orders_df = DatabaseManager.get_equipment_orders(
    start_year=start_year,
    end_year=end_year,
    manufacturer=manufacturer,
    vendor=vendor,
    equipment_type=equipment_type
)

# Apply factory filter if specific factory selected
if factory != "All" and factory != "All Factories":
    orders_df = orders_df[orders_df['factory'] == factory]

# Apply process step filter
if process_step_filter != "All":
    step_num = int(process_step_filter.split(":")[0])
    orders_df['_process_step'] = orders_df['equipment_type'].apply(get_process_step)
    orders_df = orders_df[orders_df['_process_step'] == step_num]
    orders_df = orders_df.drop(columns=['_process_step'])

# Add derived columns once
if len(orders_df) > 0:
    orders_df = orders_df.copy()
    orders_df['process_step'] = orders_df['equipment_type'].apply(get_process_step_name)
    # Rename 'Others' equipment_type to 'Unknown'
    orders_df['equipment_type'] = orders_df['equipment_type'].replace({'Others': 'Unknown'})
    # Clean tool_category (strip whitespace, rename 'Other' variants)
    if 'tool_category' in orders_df.columns:
        orders_df['tool_category'] = orders_df['tool_category'].str.strip()
        orders_df['tool_category'] = orders_df['tool_category'].replace({'Other': 'Unknown', '': 'Unknown'})
        orders_df['tool_category'] = orders_df['tool_category'].fillna('Unknown')

# Get theme colors
theme = get_plotly_theme()
colors = theme['color_discrete_sequence']

# Main content tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Vendor Analysis", "Order Details"])

# Tab 1: Overview
with tab1:
    if len(orders_df) > 0:
        # Check if we're in Factory view or Manufacturer view
        is_factory_view = manufacturer != "All" and factory not in ["All", "All Factories"]
        is_manufacturer_view = manufacturer != "All" and factory in ["All", "All Factories"]

        # =================================================================
        # Factory View - specific factory selected
        # =================================================================
        if is_factory_view:
            st.markdown(f"### {manufacturer} - {factory}")

            # Metrics
            total_spend = orders_df['amount_usd'].sum()
            total_units = orders_df['units'].sum()
            total_orders = len(orders_df)
            avg_cost_eq = total_spend / total_units if total_units > 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Spend", f"${total_spend:,.0f}")
            with col2:
                st.metric("Equipment Count", f"{int(total_units):,}")
            with col3:
                st.metric("Avg Cost / EQ", f"${avg_cost_eq:,.0f}")
            with col4:
                unique_vendors = orders_df[orders_df['vendor'].notna() & (orders_df['vendor'] != '')]['vendor'].nunique()
                st.metric("Unique Vendors", f"{unique_vendors:,}")

            st.divider()

            # EQ PO table: all orders, newest first
            st.markdown("#### Equipment Purchase Orders")

            factory_orders = orders_df.sort_values(
                ['po_year', 'po_quarter'], ascending=[False, False]
            )

            # Build display table with tool_category + process_step
            display_cols_map = {
                'po_year': 'Year',
                'po_quarter': 'Qtr',
                'vendor': 'Vendor',
                'equipment_type': 'Equipment Type',
            }
            if 'tool_category' in factory_orders.columns:
                display_cols_map['tool_category'] = 'Tool Category'
            display_cols_map['process_step'] = 'Process Step'

            factory_display = factory_orders[[c for c in display_cols_map.keys() if c in factory_orders.columns]].copy()
            factory_display = factory_display.rename(columns=display_cols_map)

            # Add numeric columns with formatting
            factory_display['Units'] = factory_orders['units'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "-")
            factory_display['Order Value'] = factory_orders['amount_usd'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "-")
            factory_display['Avg Cost/EQ'] = factory_orders.apply(
                lambda r: f"${r['amount_usd'] / r['units']:,.0f}" if pd.notna(r['units']) and r['units'] > 0 else "-", axis=1
            )

            st.dataframe(
                factory_display,
                use_container_width=True,
                hide_index=True,
                height=500
            )

            st.divider()

            # Chart: top 10 vendors by spend
            st.markdown("#### Top 10 Vendors by Spend")

            vendor_spend = orders_df.groupby('vendor')['amount_usd'].sum().reset_index()
            vendor_spend.columns = ['Vendor', 'Total Spend']
            vendor_spend = vendor_spend[vendor_spend['Vendor'].notna() & (vendor_spend['Vendor'] != '')]
            vendor_spend = vendor_spend.sort_values('Total Spend', ascending=True).tail(10)

            if len(vendor_spend) > 0:
                fig = px.bar(
                    vendor_spend,
                    x='Total Spend',
                    y='Vendor',
                    orientation='h'
                )
                fig.update_traces(
                    marker_color=colors[0],
                    hovertemplate='%{y}<br>Spend: $%{x:,.0f}<extra></extra>'
                )
                apply_chart_theme(fig)
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Total Spend (USD)",
                    yaxis_title="",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

        # =================================================================
        # Manufacturer View - only manufacturer selected
        # =================================================================
        elif is_manufacturer_view:
            st.markdown(f"### {manufacturer} - All Factories")

            # Summary metrics
            total_spend = orders_df['amount_usd'].sum()
            total_units = orders_df['units'].sum()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Orders", format_with_commas(len(orders_df)))
            with col2:
                st.metric("Total Spend", f"${total_spend:,.0f}")
            with col3:
                st.metric("Equipment Count", format_with_commas(total_units))
            with col4:
                unique_vendors = orders_df[orders_df['vendor'].notna() & (orders_df['vendor'] != '')]['vendor'].nunique()
                st.metric("Unique Vendors", format_with_commas(unique_vendors))

            st.divider()

            # Table: Equipment Type × Vendor × Tool Category × Process
            st.markdown("#### Equipment Purchases by Type, Vendor & Process")

            group_cols = ['equipment_type', 'vendor', 'process_step']
            rename_cols = ['Equipment Type', 'Vendor', 'Process Step']
            if 'tool_category' in orders_df.columns:
                group_cols.insert(2, 'tool_category')
                rename_cols.insert(2, 'Tool Category')

            equipment_vendor_df = orders_df.groupby(group_cols).agg({
                'amount_usd': 'sum',
                'units': 'sum'
            }).reset_index()
            equipment_vendor_df.columns = rename_cols + ['Total Spend', 'Units']
            equipment_vendor_df = equipment_vendor_df.sort_values('Total Spend', ascending=False)

            eq_display = equipment_vendor_df.head(50).copy()
            eq_display['Total Spend'] = eq_display['Total Spend'].apply(lambda x: f"${x:,.0f}")
            eq_display['Units'] = eq_display['Units'].apply(lambda x: f"{int(x):,}")

            st.dataframe(
                eq_display,
                use_container_width=True,
                hide_index=True,
                height=500
            )

            st.divider()

            # Spend by Process Step — table with % of total + chart
            st.markdown("#### Spend by Process Step")

            step_spend = orders_df.groupby('process_step')['amount_usd'].sum().reset_index()
            step_spend.columns = ['Process Step', 'Total Spend']
            step_total = step_spend['Total Spend'].sum()
            step_spend['% of Total'] = (step_spend['Total Spend'] / step_total * 100) if step_total > 0 else 0
            step_spend = step_spend.sort_values('Total Spend', ascending=False)

            step_display = step_spend.copy()
            step_display['Total Spend'] = step_display['Total Spend'].apply(lambda x: f"${x:,.0f}")
            step_display['% of Total'] = step_display['% of Total'].apply(lambda x: f"{x:.1f}%")

            col1, col2 = st.columns([1, 1])
            with col1:
                st.dataframe(step_display, use_container_width=True, hide_index=True)
            with col2:
                chart_data = step_spend.sort_values('Total Spend', ascending=True)
                fig = px.bar(
                    chart_data,
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

        # =================================================================
        # Default View - no manufacturer selected (All)
        # =================================================================
        else:
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
                st.markdown("#### Orders by Equipment Type")

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

            # Spend by Process Step with % of total
            st.markdown("#### Spend by Process Step")

            step_spend = orders_df.groupby('process_step')['amount_usd'].sum().reset_index()
            step_spend.columns = ['Process Step', 'Total Spend']
            step_total = step_spend['Total Spend'].sum()
            step_spend['% of Total'] = (step_spend['Total Spend'] / step_total * 100) if step_total > 0 else 0
            step_spend = step_spend.sort_values('Total Spend', ascending=False)

            step_display = step_spend.copy()
            step_display['Total Spend'] = step_display['Total Spend'].apply(lambda x: f"${x:,.0f}")
            step_display['% of Total'] = step_display['% of Total'].apply(lambda x: f"{x:.1f}%")

            col1, col2 = st.columns([1, 1])
            with col1:
                st.dataframe(step_display, use_container_width=True, hide_index=True)
            with col2:
                chart_data = step_spend.sort_values('Total Spend', ascending=True).copy()
                chart_data['spend_raw'] = orders_df.groupby('process_step')['amount_usd'].sum().reindex(chart_data['Process Step']).values
                if len(chart_data) > 0:
                    fig = px.bar(
                        chart_data,
                        x='spend_raw',
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

            # Equipment Unit Economics
            st.markdown("#### Equipment Unit Economics")

            has_tool_cat = 'tool_category' in orders_df.columns
            group_cols_econ = ['equipment_type']
            if has_tool_cat:
                group_cols_econ.append('tool_category')
            group_cols_econ.append('process_step')

            unit_economics = orders_df[orders_df['units'] > 0].groupby(group_cols_econ).agg({
                'amount_usd': 'sum',
                'units': 'sum'
            }).reset_index()
            unit_economics['Avg Unit Cost'] = unit_economics['amount_usd'] / unit_economics['units']
            unit_economics = unit_economics.sort_values('Avg Unit Cost', ascending=False)

            rename_map = {'equipment_type': 'Equipment Type', 'amount_usd': 'Total Spend',
                          'units': 'Total Units', 'process_step': 'Process Step'}
            if has_tool_cat:
                rename_map['tool_category'] = 'Tool Category'
            unit_economics = unit_economics.rename(columns=rename_map)

            unit_display = unit_economics.head(25).copy()
            unit_display['Total Spend'] = unit_display['Total Spend'].apply(lambda x: f"${x:,.0f}")
            unit_display['Total Units'] = unit_display['Total Units'].apply(lambda x: f"{int(x):,}")
            unit_display['Avg Unit Cost'] = unit_display['Avg Unit Cost'].apply(lambda x: f"${x:,.0f}")

            st.dataframe(
                unit_display,
                use_container_width=True,
                hide_index=True,
                height=500
            )

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

            # Vendor Performance Metrics - grouped by Vendor + Equipment Type
            st.markdown("#### Vendor Performance by Equipment Type")

            # Group by vendor and equipment type
            vendor_equip = orders_df.groupby(['vendor', 'equipment_type']).agg({
                'amount_usd': 'sum',
                'units': 'sum',
                'id': 'count'
            }).reset_index()
            vendor_equip.columns = ['Vendor', 'Equipment Type', 'Total Spend', 'Total Units', 'Order Count']

            # Calculate average order value
            vendor_equip['Avg Order Value'] = vendor_equip['Total Spend'] / vendor_equip['Order Count']

            # Sort by total spend descending
            vendor_equip = vendor_equip.sort_values('Total Spend', ascending=False)

            # Filter out unknown vendors
            vendor_equip = vendor_equip[
                vendor_equip['Vendor'].notna() &
                (vendor_equip['Vendor'] != '') &
                (vendor_equip['Vendor'] != 'Unknown')
            ]

            # Format for display
            vendor_display = vendor_equip.head(30).copy()
            vendor_display['Total Spend'] = vendor_display['Total Spend'].apply(lambda x: f"${x:,.0f}")
            vendor_display['Avg Order Value'] = vendor_display['Avg Order Value'].apply(lambda x: f"${x:,.0f}")
            vendor_display['Total Units'] = vendor_display['Total Units'].apply(lambda x: f"{int(x):,}")
            vendor_display['Order Count'] = vendor_display['Order Count'].apply(lambda x: f"{int(x):,}")

            st.dataframe(
                vendor_display,
                use_container_width=True,
                hide_index=True,
                height=500
            )

            create_download_buttons(vendor_equip, "vendor_analysis", "Vendor Analysis Report")

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

        # Display columns — newest first
        display_cols = [
            'po_year', 'po_quarter', 'manufacturer', 'factory', 'vendor',
            'equipment_type', 'tool_category', 'process_step', 'units', 'amount_usd'
        ]
        available_cols = [c for c in display_cols if c in orders_df.columns]

        detail_df = orders_df[available_cols].sort_values(
            ['po_year', 'po_quarter'], ascending=[False, False]
        ).head(500)

        st.dataframe(
            detail_df,
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
                "tool_category": st.column_config.TextColumn("Tool Category", width="medium"),
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
