"""
Market Intelligence Page - Display Intelligence Dashboard
Market insights, shipment analytics, competitive analysis, and strategic intelligence.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import get_css, get_plotly_theme, apply_chart_theme, format_with_commas, format_percent
from utils.database import DatabaseManager
from utils.exports import create_download_buttons

# Page config
st.set_page_config(
    page_title="Market Intelligence - Display Intelligence",
    page_icon="📈",
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
    <h1>📈 Market Intelligence</h1>
    <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
        Shipment analytics, market trends, and strategic insights
    </p>
""", unsafe_allow_html=True)

# Filters in sidebar
with st.sidebar:
    st.markdown("### Filters")

    panel_maker = st.selectbox(
        "Panel Maker",
        options=DatabaseManager.get_panel_makers(),
        key="intel_panel_maker"
    )

    application = st.selectbox(
        "Application",
        options=DatabaseManager.get_applications(),
        key="intel_application"
    )

    st.divider()

    st.markdown("### Year Range")
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox(
            "Start Year",
            options=list(range(2016, 2030)),
            index=6,  # Default to 2022
            key="intel_start_year"
        )
    with col2:
        end_year = st.selectbox(
            "End Year",
            options=list(range(2016, 2030)),
            index=10,  # Default to 2026
            key="intel_end_year"
        )

def format_revenue_m(value_m):
    """Format a revenue value that is already in $M."""
    if pd.isna(value_m) or value_m == 0:
        return "$0"
    if abs(value_m) >= 1_000_000:
        return f"${value_m / 1_000_000:,.1f}T"
    if abs(value_m) >= 1_000:
        return f"${value_m / 1_000:,.1f}B"
    return f"${value_m:,.1f}M"


def format_units_k(value_k):
    """Format a units value that is already in K."""
    if pd.isna(value_k) or value_k == 0:
        return "0"
    if value_k >= 1_000_000:
        return f"{value_k / 1_000_000:,.1f}B"
    if value_k >= 1_000:
        return f"{value_k / 1_000:,.1f}M"
    return f"{value_k:,.0f}K"


# Load shipment data
shipments_df = DatabaseManager.get_shipments(
    start_year=start_year,
    end_year=end_year,
    panel_maker=panel_maker,
    application=application
)

# Get theme colors
theme = get_plotly_theme()
colors = theme['color_discrete_sequence']

# Pre-compute common filtered dataframes once
if len(shipments_df) > 0:
    # Valid panel makers (exclude ALL and /Others aggregates)
    valid_makers_df = shipments_df[
        shipments_df['panel_maker'].notna() &
        (shipments_df['panel_maker'] != '') &
        (shipments_df['panel_maker'] != 'ALL') &
        (~shipments_df['panel_maker'].str.contains('/Others', na=False))
    ]
    # Valid applications
    valid_apps_df = shipments_df[shipments_df['application'].notna() & (shipments_df['application'] != '')]
    # Time series base (exclude annual aggregates)
    ts_df = shipments_df[~shipments_df['date'].str.contains('ALL', na=False)].copy()
    ts_df['period'] = ts_df['date'].str.split(' ').str[0]

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["Market Overview", "Supplier Analysis", "Application Analysis", "Detailed Data"])

# =============================================================================
# Tab 1: Market Overview
# =============================================================================
with tab1:
    if len(shipments_df) > 0:
        # Summary metrics row
        col1, col2, col3, col4 = st.columns(4)

        total_revenue = shipments_df['revenue_m'].sum()
        total_units = shipments_df['units_k'].sum()

        with col1:
            st.metric(f"Total Revenue ({start_year}-{end_year})", format_revenue_m(total_revenue))

        with col2:
            st.metric(f"Total Units ({start_year}-{end_year})", format_units_k(total_units))

        with col3:
            # Average ASP: revenue_m * 1000 / units_k gives $ per unit
            avg_asp = (total_revenue * 1000 / total_units) if total_units > 0 else 0
            st.metric("Avg ASP", f"${avg_asp:,.0f}")

        with col4:
            unique_suppliers = valid_makers_df['panel_maker'].nunique()
            st.metric("Active Suppliers", format_with_commas(unique_suppliers))

        st.divider()

        # OLED Market Trends - quarterly revenue + units dual-axis
        st.markdown("#### OLED Market Trends")

        quarterly = ts_df.groupby('period').agg({
            'units_k': 'sum',
            'revenue_m': 'sum'
        }).reset_index().sort_values('period')

        if len(quarterly) > 0:
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=quarterly['period'].tolist(),
                y=quarterly['units_k'].tolist(),
                name='Units (K)',
                marker_color=colors[0],
                opacity=0.7,
                hovertemplate='%{x}<br>Units: %{y:,.0f}K<extra></extra>'
            ))

            fig.add_trace(go.Scatter(
                x=quarterly['period'].tolist(),
                y=quarterly['revenue_m'].tolist(),
                name='Revenue ($M)',
                mode='lines+markers',
                yaxis='y2',
                line=dict(color=colors[1], width=3),
                marker=dict(size=6),
                hovertemplate='%{x}<br>Revenue: $%{y:,.0f}M<extra></extra>'
            ))

            apply_chart_theme(fig)
            fig.update_layout(
                xaxis_title="Quarter",
                yaxis=dict(title="Units (K)", side='left'),
                yaxis2=dict(title="Revenue ($M)", overlaying='y', side='right'),
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                barmode='overlay'
            )

            st.plotly_chart(fig, use_container_width=True)

        # Side-by-side pies: Revenue by Application | Revenue by Supplier
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Revenue by Application")

            app_revenue = valid_apps_df.groupby('application')['revenue_m'].sum().sort_values(ascending=False)

            if len(app_revenue) > 0:
                fig = px.pie(
                    values=app_revenue.values.tolist(),
                    names=app_revenue.index.tolist(),
                    color_discrete_sequence=colors,
                    hole=0.4
                )
                fig.update_traces(hovertemplate='%{label}<br>$%{value:,.0f}M (%{percent})<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Revenue by Supplier")

            maker_revenue = valid_makers_df.groupby('panel_maker')['revenue_m'].sum().sort_values(ascending=False)

            if len(maker_revenue) > 0:
                top_5 = maker_revenue.head(5)
                others = maker_revenue.iloc[5:].sum() if len(maker_revenue) > 5 else 0

                pie_names = top_5.index.tolist() + (['Others'] if others > 0 else [])
                pie_values = top_5.values.tolist() + ([others] if others > 0 else [])

                fig = px.pie(
                    values=pie_values,
                    names=pie_names,
                    color_discrete_sequence=colors,
                    hole=0.4
                )
                fig.update_traces(hovertemplate='%{label}<br>$%{value:,.0f}M (%{percent})<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No shipment data available for the selected filters.")


# =============================================================================
# Tab 2: Supplier Analysis
# =============================================================================
with tab2:
    if len(shipments_df) > 0:
        # --- Top Suppliers Table ---
        st.markdown("#### Top Suppliers")

        maker_agg = valid_makers_df.groupby('panel_maker').agg({
            'revenue_m': 'sum',
            'units_k': 'sum'
        }).reset_index().sort_values('revenue_m', ascending=False)

        total_market_revenue = maker_agg['revenue_m'].sum()
        maker_agg['Market Share %'] = (maker_agg['revenue_m'] / total_market_revenue * 100) if total_market_revenue > 0 else 0

        # Find top application per supplier
        maker_app = valid_makers_df.groupby(['panel_maker', 'application'])['revenue_m'].sum().reset_index()
        top_app_per_maker = maker_app.loc[maker_app.groupby('panel_maker')['revenue_m'].idxmax()][['panel_maker', 'application']]
        top_app_per_maker.columns = ['panel_maker', 'Top Application']

        maker_table = maker_agg.merge(top_app_per_maker, on='panel_maker', how='left')
        maker_table.columns = ['Supplier', 'Revenue ($M)', 'Units (K)', 'Market Share %', 'Top Application']

        st.dataframe(
            maker_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Supplier": st.column_config.TextColumn("Supplier", width="medium"),
                "Revenue ($M)": st.column_config.NumberColumn("Revenue ($M)", format="$%,.0f"),
                "Units (K)": st.column_config.NumberColumn("Units (K)", format="%,.0f"),
                "Market Share %": st.column_config.NumberColumn("Market Share %", format="%.1f%%"),
                "Top Application": st.column_config.TextColumn("Top Application", width="medium")
            }
        )

        st.divider()

        # --- Supplier Revenue Trends (top 5) ---
        st.markdown("#### Supplier Revenue Trends")

        top_5_suppliers = maker_agg.head(5)['Supplier'].tolist()
        maker_ts = ts_df[
            ts_df['panel_maker'].isin(top_5_suppliers)
        ].groupby(['period', 'panel_maker'])['revenue_m'].sum().reset_index().sort_values('period')

        if len(maker_ts) > 0:
            fig = px.line(
                maker_ts,
                x='period',
                y='revenue_m',
                color='panel_maker',
                color_discrete_sequence=colors,
                markers=True
            )
            fig.update_traces(hovertemplate='%{x}<br>$%{y:,.0f}M<extra></extra>')
            apply_chart_theme(fig)
            fig.update_layout(
                xaxis_title="Quarter",
                yaxis_title="Revenue ($M)",
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- Market Concentration Card ---
        col1, col2, col3 = st.columns(3)

        maker_revenue_series = maker_agg.set_index('Supplier')['Revenue ($M)']

        with col1:
            top_maker = maker_revenue_series.index[0] if len(maker_revenue_series) > 0 else "N/A"
            top_maker_share = (maker_revenue_series.iloc[0] / total_market_revenue * 100) if total_market_revenue > 0 else 0
            st.markdown(f"""
            <div style="background: #F5F5F7; border-radius: 12px; padding: 1.5rem;">
                <p style="color: #86868B; margin-bottom: 0.5rem;">Market Leader</p>
                <p style="font-size: 1.5rem; font-weight: 600; color: #1D1D1F;">{top_maker}</p>
                <p style="color: #007AFF;">{top_maker_share:.1f}% market share</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            top_3_share = (maker_revenue_series.head(3).sum() / total_market_revenue * 100) if total_market_revenue > 0 else 0
            st.markdown(f"""
            <div style="background: #F5F5F7; border-radius: 12px; padding: 1.5rem;">
                <p style="color: #86868B; margin-bottom: 0.5rem;">Top 3 Share</p>
                <p style="font-size: 1.5rem; font-weight: 600; color: #1D1D1F;">{top_3_share:.1f}%</p>
                <p style="color: #86868B;">Combined revenue share</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            hhi = sum((r / total_market_revenue * 100) ** 2 for r in maker_revenue_series.values) if total_market_revenue > 0 else 0
            concentration = "High" if hhi > 2500 else "Moderate" if hhi > 1500 else "Low"
            st.markdown(f"""
            <div style="background: #F5F5F7; border-radius: 12px; padding: 1.5rem;">
                <p style="color: #86868B; margin-bottom: 0.5rem;">HHI Index</p>
                <p style="font-size: 1.5rem; font-weight: 600; color: #1D1D1F;">{hhi:,.0f}</p>
                <p style="color: #86868B;">{concentration} concentration</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # --- Supplier Drill-down ---
        st.markdown("#### Supplier Drill-down")

        supplier_list = maker_agg['Supplier'].tolist()
        selected_supplier = st.selectbox(
            "Select a supplier",
            options=supplier_list,
            key="supplier_drilldown"
        )

        if selected_supplier:
            supplier_data = valid_makers_df[valid_makers_df['panel_maker'] == selected_supplier]
            supplier_app = supplier_data.groupby('application').agg({
                'revenue_m': 'sum',
                'units_k': 'sum'
            }).reset_index().sort_values('revenue_m', ascending=False)

            if len(supplier_app) > 0:
                col1, col2 = st.columns(2)

                with col1:
                    fig = px.bar(
                        supplier_app,
                        x='application',
                        y='revenue_m',
                        color='application',
                        color_discrete_sequence=colors
                    )
                    fig.update_traces(hovertemplate='%{x}<br>$%{y:,.0f}M<extra></extra>')
                    apply_chart_theme(fig)
                    fig.update_layout(
                        title=f"{selected_supplier} — Revenue by Application",
                        showlegend=False,
                        xaxis_title="Application",
                        yaxis_title="Revenue ($M)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    supplier_app_display = supplier_app.copy()
                    supplier_app_display['ASP ($)'] = (
                        supplier_app_display['revenue_m'] * 1000 / supplier_app_display['units_k']
                    ).where(supplier_app_display['units_k'] > 0, 0)
                    supplier_app_display.columns = ['Application', 'Revenue ($M)', 'Units (K)', 'ASP ($)']

                    st.dataframe(
                        supplier_app_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Application": st.column_config.TextColumn("Application", width="medium"),
                            "Revenue ($M)": st.column_config.NumberColumn("Revenue ($M)", format="$%,.0f"),
                            "Units (K)": st.column_config.NumberColumn("Units (K)", format="%,.0f"),
                            "ASP ($)": st.column_config.NumberColumn("ASP ($)", format="$%,.0f")
                        }
                    )
            else:
                st.info(f"No application breakdown data for {selected_supplier}.")

    else:
        st.info("No supplier data available for the selected filters.")


# =============================================================================
# Tab 3: Application Analysis
# =============================================================================
with tab3:
    if len(shipments_df) > 0:
        # --- Application Summary Table ---
        st.markdown("#### Application Summary")

        app_summary = valid_apps_df.groupby('application').agg({
            'units_k': 'sum',
            'revenue_m': 'sum'
        }).reset_index()
        app_summary['ASP ($)'] = (app_summary['revenue_m'] * 1000 / app_summary['units_k']).where(
            app_summary['units_k'] > 0, 0
        )

        # Top supplier per application
        app_maker = valid_apps_df[
            valid_apps_df['panel_maker'].notna() &
            (valid_apps_df['panel_maker'] != '') &
            (valid_apps_df['panel_maker'] != 'ALL') &
            (~valid_apps_df['panel_maker'].str.contains('/Others', na=False))
        ].groupby(['application', 'panel_maker'])['revenue_m'].sum().reset_index()

        if len(app_maker) > 0:
            top_supplier_per_app = app_maker.loc[
                app_maker.groupby('application')['revenue_m'].idxmax()
            ][['application', 'panel_maker']]
            top_supplier_per_app.columns = ['application', 'Top Supplier']
            app_summary = app_summary.merge(top_supplier_per_app, on='application', how='left')
        else:
            app_summary['Top Supplier'] = 'N/A'

        app_summary = app_summary.sort_values('revenue_m', ascending=False)
        app_summary.columns = ['Application', 'Units (K)', 'Revenue ($M)', 'ASP ($)', 'Top Supplier']

        st.dataframe(
            app_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Application": st.column_config.TextColumn("Application", width="medium"),
                "Units (K)": st.column_config.NumberColumn("Units (K)", format="%,.0f"),
                "Revenue ($M)": st.column_config.NumberColumn("Revenue ($M)", format="$%,.0f"),
                "ASP ($)": st.column_config.NumberColumn("ASP ($)", format="$%,.0f"),
                "Top Supplier": st.column_config.TextColumn("Top Supplier", width="medium")
            }
        )

        st.divider()

        # --- Application Revenue Trends (top 5) ---
        st.markdown("#### Application Trends")

        app_revenue_totals = valid_apps_df.groupby('application')['revenue_m'].sum().sort_values(ascending=False)
        top_5_apps = app_revenue_totals.head(5).index.tolist()

        app_ts = ts_df[
            ts_df['application'].isin(top_5_apps) &
            ts_df['application'].notna() &
            (ts_df['application'] != '')
        ].groupby(['period', 'application'])['revenue_m'].sum().reset_index().sort_values('period')

        if len(app_ts) > 0:
            fig = px.line(
                app_ts,
                x='period',
                y='revenue_m',
                color='application',
                color_discrete_sequence=colors,
                markers=True
            )
            fig.update_traces(hovertemplate='%{x}<br>$%{y:,.0f}M<extra></extra>')
            apply_chart_theme(fig)
            fig.update_layout(
                xaxis_title="Quarter",
                yaxis_title="Revenue ($M)",
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- Application Drill-down ---
        st.markdown("#### Application Drill-down")

        app_list = app_revenue_totals.index.tolist()
        selected_app = st.selectbox(
            "Select an application",
            options=app_list,
            key="app_drilldown"
        )

        if selected_app:
            app_drill_data = valid_makers_df[
                valid_makers_df['application'].notna() &
                (valid_makers_df['application'] == selected_app)
            ]
            app_supplier = app_drill_data.groupby('panel_maker').agg({
                'revenue_m': 'sum',
                'units_k': 'sum'
            }).reset_index().sort_values('revenue_m', ascending=False)

            if len(app_supplier) > 0:
                col1, col2 = st.columns(2)

                with col1:
                    fig = px.bar(
                        app_supplier,
                        x='panel_maker',
                        y='revenue_m',
                        color='panel_maker',
                        color_discrete_sequence=colors
                    )
                    fig.update_traces(hovertemplate='%{x}<br>$%{y:,.0f}M<extra></extra>')
                    apply_chart_theme(fig)
                    fig.update_layout(
                        title=f"{selected_app} — Revenue by Supplier",
                        showlegend=False,
                        xaxis_title="Supplier",
                        yaxis_title="Revenue ($M)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    app_supplier_display = app_supplier.copy()
                    total_app_rev = app_supplier_display['revenue_m'].sum()
                    app_supplier_display['Share %'] = (
                        app_supplier_display['revenue_m'] / total_app_rev * 100
                    ) if total_app_rev > 0 else 0
                    app_supplier_display.columns = ['Supplier', 'Revenue ($M)', 'Units (K)', 'Share %']

                    st.dataframe(
                        app_supplier_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Supplier": st.column_config.TextColumn("Supplier", width="medium"),
                            "Revenue ($M)": st.column_config.NumberColumn("Revenue ($M)", format="$%,.0f"),
                            "Units (K)": st.column_config.NumberColumn("Units (K)", format="%,.0f"),
                            "Share %": st.column_config.NumberColumn("Share %", format="%.1f%%")
                        }
                    )
            else:
                st.info(f"No supplier data for {selected_app}.")

        # --- Size Distribution ---
        if 'size_inches' in shipments_df.columns:
            size_data = shipments_df[shipments_df['size_inches'].notna() & shipments_df['application'].notna()]
            if len(size_data) > 0:
                st.divider()
                st.markdown("#### Panel Size Distribution")

                fig = px.box(
                    size_data,
                    x='application',
                    y='size_inches',
                    color='application',
                    color_discrete_sequence=colors
                )
                apply_chart_theme(fig)
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Application",
                    yaxis_title="Panel Size (inches)",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No application data available.")


# =============================================================================
# Tab 4: Detailed Data
# =============================================================================
with tab4:
    if len(shipments_df) > 0:
        st.markdown("#### Shipment Records")

        display_cols = [
            'date', 'panel_maker', 'brand', 'model', 'size_inches',
            'technology', 'application', 'units_k', 'revenue_m'
        ]
        available_cols = [c for c in display_cols if c in shipments_df.columns]

        st.dataframe(
            shipments_df[available_cols].head(1000),
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "date": st.column_config.TextColumn("Date", width="small"),
                "panel_maker": st.column_config.TextColumn("Panel Maker", width="small"),
                "brand": st.column_config.TextColumn("Brand", width="small"),
                "model": st.column_config.TextColumn("Model", width="medium"),
                "size_inches": st.column_config.NumberColumn("Size (in)", format="%.1f"),
                "technology": st.column_config.TextColumn("Tech", width="small"),
                "application": st.column_config.TextColumn("Application", width="small"),
                "units_k": st.column_config.NumberColumn("Units (K)", format="%,.0f"),
                "revenue_m": st.column_config.NumberColumn("Revenue ($M)", format="$%,.0f")
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)
        create_download_buttons(shipments_df, "shipments", "Shipments Intelligence Report")

    else:
        st.info("No shipment data available for the selected filters.")

    # Insights section
    st.divider()
    st.markdown("#### Strategic Insights")

    insights_df = DatabaseManager.get_insights()

    if len(insights_df) > 0:
        for _, row in insights_df.head(5).iterrows():
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #F5F5F7 0%, #FFFFFF 100%);
                border-left: 4px solid #007AFF;
                border-radius: 0 12px 12px 0;
                padding: 1rem 1.5rem;
                margin-bottom: 1rem;
            ">
                <p style="font-weight: 600; color: #1D1D1F; margin-bottom: 0.5rem;">
                    {row.get('topic', 'Market Insight')}
                </p>
                <p style="color: #86868B; font-size: 0.9rem;">
                    {row.get('insight_text', 'No details available.')}
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Strategic insights will appear here as they are added to the database.")
