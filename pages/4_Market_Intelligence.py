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

from utils.styling import get_css, get_plotly_theme
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

    technology = st.selectbox(
        "Technology",
        options=DatabaseManager.get_technologies(),
        key="intel_technology"
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
            index=13,  # Default to 2029
            key="intel_end_year"
        )

# Load shipment data
shipments_df = DatabaseManager.get_shipments(
    start_year=start_year,
    end_year=end_year,
    panel_maker=panel_maker,
    technology=technology,
    application=application
)

theme = get_plotly_theme()

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Market Overview", "Competitive Analysis", "Application Analysis", "Panel Makers", "Detailed Data"])

# Tab 1: Market Overview
with tab1:
    if len(shipments_df) > 0:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_units = shipments_df['units_k'].sum()
            if total_units >= 1000:
                units_str = f"{total_units/1000:.1f}M"
            else:
                units_str = f"{total_units:.0f}K"
            st.metric("Total Units", units_str)

        with col2:
            total_revenue = shipments_df['revenue_m'].sum()
            if total_revenue >= 1000:
                rev_str = f"${total_revenue/1000:.1f}B"
            else:
                rev_str = f"${total_revenue:.0f}M"
            st.metric("Total Revenue", rev_str)

        with col3:
            unique_makers = shipments_df['panel_maker'].nunique()
            st.metric("Panel Makers", unique_makers)

        with col4:
            unique_apps = shipments_df['application'].nunique()
            st.metric("Applications", unique_apps)

        st.divider()

        # Shipments over time
        st.markdown("#### Shipment Volume Trends")

        # Use date column directly as period (format: "YYYY-QX YYYY")
        # Filter out annual aggregates (ALL) for cleaner time series
        shipments_ts = shipments_df[~shipments_df['date'].str.contains('ALL', na=False)].copy()
        # Extract period for grouping (first part before space)
        shipments_ts['period'] = shipments_ts['date'].str.split(' ').str[0]
        monthly_shipments = shipments_ts.groupby('period').agg({
            'units_k': 'sum',
            'revenue_m': 'sum'
        }).reset_index()
        monthly_shipments = monthly_shipments.sort_values('period')

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=monthly_shipments['period'],
            y=monthly_shipments['units_k'],
            name='Units (K)',
            marker_color=theme['color_discrete_sequence'][0],
            opacity=0.7
        ))

        fig.add_trace(go.Scatter(
            x=monthly_shipments['period'],
            y=monthly_shipments['revenue_m'],
            name='Revenue ($M)',
            mode='lines+markers',
            yaxis='y2',
            line=dict(color=theme['color_discrete_sequence'][1], width=3),
            marker=dict(size=6)
        ))

        fig.update_layout(
            **theme['layout'],
            xaxis_title="Quarter",
            yaxis=dict(title="Units (K)", side='left'),
            yaxis2=dict(title="Revenue ($M)", overlaying='y', side='right'),
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            barmode='overlay'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Market composition
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Revenue by Application")

            app_revenue = shipments_df.groupby('application')['revenue_m'].sum().sort_values(ascending=False)

            fig = px.pie(
                values=app_revenue.values,
                names=app_revenue.index,
                color_discrete_sequence=theme['color_discrete_sequence'],
                hole=0.4
            )
            fig.update_layout(
                **theme['layout'],
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Units by Technology")

            tech_units = shipments_df.groupby('technology')['units_k'].sum()

            fig = px.pie(
                values=tech_units.values,
                names=tech_units.index,
                color_discrete_sequence=theme['color_discrete_sequence'],
                hole=0.4
            )
            fig.update_layout(
                **theme['layout'],
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No shipment data available for the selected filters.")


# Tab 2: Competitive Analysis
with tab2:
    if len(shipments_df) > 0:
        st.markdown("#### Competitive Products Analysis")
        st.markdown("""
        <p style="color: #86868B; margin-bottom: 1.5rem;">
            Compare panel makers across technologies, applications, and market performance
        </p>
        """, unsafe_allow_html=True)

        # Technology Breakdown Section
        st.markdown("##### Technology Breakdown: LCD vs OLED")

        # Handle NULL/None technology values
        tech_df = shipments_df.copy()
        tech_df['technology'] = tech_df['technology'].fillna('Unknown').replace('', 'Unknown')

        col1, col2 = st.columns(2)

        with col1:
            # Technology market share by revenue
            tech_revenue = tech_df.groupby('technology').agg({
                'revenue_m': 'sum',
                'units_k': 'sum'
            }).reset_index()
            tech_revenue['market_share'] = tech_revenue['revenue_m'] / tech_revenue['revenue_m'].sum() * 100

            fig = px.pie(
                tech_revenue,
                values='revenue_m',
                names='technology',
                title='Revenue Share by Technology',
                color_discrete_sequence=theme['color_discrete_sequence'],
                hole=0.4
            )
            fig.update_layout(
                **theme['layout'],
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Technology units comparison
            fig = px.bar(
                tech_revenue,
                x='technology',
                y='units_k',
                title='Total Units by Technology (K)',
                color='technology',
                color_discrete_sequence=theme['color_discrete_sequence']
            )
            fig.update_layout(
                **theme['layout'],
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Technology trends over time
        st.markdown("##### Technology Trends Over Time")

        tech_ts = tech_df[~tech_df['date'].str.contains('ALL', na=False)].copy()
        tech_ts['period'] = tech_ts['date'].str.split(' ').str[0]
        tech_trends = tech_ts.groupby(['period', 'technology']).agg({
            'revenue_m': 'sum',
            'units_k': 'sum'
        }).reset_index()
        tech_trends = tech_trends.sort_values('period')

        fig = px.area(
            tech_trends,
            x='period',
            y='revenue_m',
            color='technology',
            title='Revenue by Technology Over Time',
            color_discrete_sequence=theme['color_discrete_sequence']
        )
        fig.update_layout(
            **theme['layout'],
            xaxis_title="Quarter",
            yaxis_title="Revenue ($M)",
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Panel Maker Market Share Section
        st.markdown("##### Panel Maker Market Share")

        # Handle NULL/None panel_maker values
        maker_df = shipments_df.copy()
        maker_df['panel_maker'] = maker_df['panel_maker'].fillna('Unknown').replace('', 'Unknown')

        maker_share = maker_df.groupby('panel_maker').agg({
            'revenue_m': 'sum',
            'units_k': 'sum'
        }).reset_index()
        maker_share = maker_share.sort_values('revenue_m', ascending=False)
        maker_share['market_share'] = maker_share['revenue_m'] / maker_share['revenue_m'].sum() * 100

        # Top 10 panel makers
        top_10_makers = maker_share.head(10)

        fig = px.bar(
            top_10_makers,
            x='market_share',
            y='panel_maker',
            orientation='h',
            title='Top 10 Panel Makers by Market Share (%)',
            color='market_share',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            **theme['layout'],
            showlegend=False,
            xaxis_title="Market Share (%)",
            yaxis_title="",
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Panel Maker by Technology breakdown
        st.markdown("##### Panel Maker Portfolio by Technology")

        maker_tech = maker_df.groupby(['panel_maker', 'technology'])['revenue_m'].sum().reset_index()
        top_makers_list = maker_share.head(8)['panel_maker'].tolist()
        maker_tech_filtered = maker_tech[maker_tech['panel_maker'].isin(top_makers_list)]

        fig = px.bar(
            maker_tech_filtered,
            x='panel_maker',
            y='revenue_m',
            color='technology',
            title='Technology Mix by Panel Maker',
            barmode='stack',
            color_discrete_sequence=theme['color_discrete_sequence']
        )
        fig.update_layout(
            **theme['layout'],
            xaxis_title="Panel Maker",
            yaxis_title="Revenue ($M)",
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Application Trends Section
        st.markdown("##### Application Market Trends")

        # Handle NULL/None application values
        app_df = shipments_df.copy()
        app_df['application'] = app_df['application'].fillna('Unknown').replace('', 'Unknown')

        col1, col2 = st.columns(2)

        with col1:
            # Application revenue share
            app_share = app_df.groupby('application')['revenue_m'].sum().sort_values(ascending=False)
            top_apps = app_share.head(6)

            fig = px.pie(
                values=top_apps.values,
                names=top_apps.index,
                title='Revenue by Application',
                color_discrete_sequence=theme['color_discrete_sequence'],
                hole=0.4
            )
            fig.update_layout(
                **theme['layout'],
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Application units comparison
            app_units = app_df.groupby('application')['units_k'].sum().sort_values(ascending=False).head(6)

            fig = px.bar(
                x=app_units.index,
                y=app_units.values,
                title='Units by Application (K)',
                color_discrete_sequence=theme['color_discrete_sequence']
            )
            fig.update_layout(
                **theme['layout'],
                showlegend=False,
                xaxis_title="Application",
                yaxis_title="Units (K)",
                height=350
            )
            fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
            st.plotly_chart(fig, use_container_width=True)

        # Application trends over time
        app_ts = app_df[~app_df['date'].str.contains('ALL', na=False)].copy()
        app_ts['period'] = app_ts['date'].str.split(' ').str[0]
        app_trends = app_ts.groupby(['period', 'application']).agg({
            'revenue_m': 'sum'
        }).reset_index()
        app_trends = app_trends.sort_values('period')

        # Filter to top 5 applications for cleaner chart
        top_5_apps = app_share.head(5).index.tolist()
        app_trends_filtered = app_trends[app_trends['application'].isin(top_5_apps)]

        fig = px.line(
            app_trends_filtered,
            x='period',
            y='revenue_m',
            color='application',
            title='Application Revenue Trends (Top 5)',
            color_discrete_sequence=theme['color_discrete_sequence'],
            markers=True
        )
        fig.update_layout(
            **theme['layout'],
            xaxis_title="Quarter",
            yaxis_title="Revenue ($M)",
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Summary metrics table
        st.markdown("##### Competitive Summary")

        summary_data = pd.DataFrame({
            'Metric': ['Total Market Revenue', 'Total Units Shipped', 'Top Technology', 'Market Leader', 'Top Application'],
            'Value': [
                f"${maker_share['revenue_m'].sum():,.0f}M",
                f"{maker_share['units_k'].sum():,.0f}K",
                tech_revenue.loc[tech_revenue['revenue_m'].idxmax(), 'technology'] if len(tech_revenue) > 0 else 'N/A',
                maker_share.iloc[0]['panel_maker'] if len(maker_share) > 0 else 'N/A',
                app_share.index[0] if len(app_share) > 0 else 'N/A'
            ]
        })

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(
                summary_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Metric": st.column_config.TextColumn("Metric", width="medium"),
                    "Value": st.column_config.TextColumn("Value", width="medium")
                }
            )

    else:
        st.info("No competitive data available for the selected filters.")


# Tab 3: Application Analysis
with tab3:
    if len(shipments_df) > 0:
        st.markdown("#### Application Performance Over Time")

        # Application trends - filter out annual aggregates and extract period
        app_ts = shipments_df[~shipments_df['date'].str.contains('ALL', na=False)].copy()
        app_ts['period'] = app_ts['date'].str.split(' ').str[0]
        app_monthly = app_ts.groupby(['period', 'application']).agg({
            'units_k': 'sum',
            'revenue_m': 'sum'
        }).reset_index()
        app_monthly = app_monthly.sort_values('period')

        fig = px.line(
            app_monthly,
            x='period',
            y='units_k',
            color='application',
            color_discrete_sequence=theme['color_discrete_sequence'],
            markers=True
        )
        fig.update_layout(
            **theme['layout'],
            xaxis_title="Quarter",
            yaxis_title="Units (K)",
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Application breakdown table
        st.markdown("#### Application Summary")

        app_summary = shipments_df.groupby('application').agg({
            'units_k': 'sum',
            'revenue_m': 'sum',
            'id': 'count'
        }).reset_index()
        app_summary.columns = ['Application', 'Units (K)', 'Revenue ($M)', 'Records']
        app_summary['Avg Unit Price'] = app_summary['Revenue ($M)'] * 1000 / app_summary['Units (K)']
        app_summary = app_summary.sort_values('Revenue ($M)', ascending=False)

        st.dataframe(
            app_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Application": st.column_config.TextColumn("Application", width="medium"),
                "Units (K)": st.column_config.NumberColumn("Units (K)", format="%.0f"),
                "Revenue ($M)": st.column_config.NumberColumn("Revenue ($M)", format="$%.1f"),
                "Records": st.column_config.NumberColumn("Records", format="%.0f"),
                "Avg Unit Price": st.column_config.NumberColumn("Avg Price ($)", format="$%.2f")
            }
        )

        # Size distribution by application
        st.divider()
        st.markdown("#### Panel Size Distribution")

        if 'size_inches' in shipments_df.columns:
            size_dist = shipments_df.groupby(['application', 'size_inches'])['units_k'].sum().reset_index()

            fig = px.box(
                shipments_df[shipments_df['size_inches'].notna()],
                x='application',
                y='size_inches',
                color='application',
                color_discrete_sequence=theme['color_discrete_sequence']
            )
            fig.update_layout(
                **theme['layout'],
                showlegend=False,
                xaxis_title="Application",
                yaxis_title="Panel Size (inches)",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No application data available.")


# Tab 4: Panel Makers
with tab4:
    if len(shipments_df) > 0:
        st.markdown("#### Panel Maker Market Share")

        # Market share by panel maker
        maker_revenue = shipments_df.groupby('panel_maker')['revenue_m'].sum().sort_values(ascending=False)
        total_revenue = maker_revenue.sum()

        # Top panel makers bar chart
        top_makers = maker_revenue.head(15)

        fig = px.bar(
            x=top_makers.values,
            y=top_makers.index,
            orientation='h',
            color_discrete_sequence=theme['color_discrete_sequence']
        )
        fig.update_layout(
            **theme['layout'],
            showlegend=False,
            xaxis_title="Revenue ($M)",
            yaxis_title="",
            height=500
        )
        fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Market share pie
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Revenue Share")

            top_5 = maker_revenue.head(5)
            others = maker_revenue.iloc[5:].sum() if len(maker_revenue) > 5 else 0

            pie_data = pd.DataFrame({
                'Maker': list(top_5.index) + (['Others'] if others > 0 else []),
                'Revenue': list(top_5.values) + ([others] if others > 0 else [])
            })

            fig = px.pie(
                pie_data,
                values='Revenue',
                names='Maker',
                color_discrete_sequence=theme['color_discrete_sequence'],
                hole=0.4
            )
            fig.update_layout(
                **theme['layout'],
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Key Statistics")

            top_maker = maker_revenue.index[0] if len(maker_revenue) > 0 else "N/A"
            top_maker_share = (maker_revenue.iloc[0] / total_revenue * 100) if total_revenue > 0 else 0
            top_3_share = (maker_revenue.head(3).sum() / total_revenue * 100) if total_revenue > 0 else 0

            st.markdown(f"""
            <div style="background: #F5F5F7; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
                <p style="color: #86868B; margin-bottom: 0.5rem;">Market Leader</p>
                <p style="font-size: 1.5rem; font-weight: 600; color: #1D1D1F;">{top_maker}</p>
                <p style="color: #007AFF;">{top_maker_share:.1f}% market share</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: #F5F5F7; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
                <p style="color: #86868B; margin-bottom: 0.5rem;">Market Concentration</p>
                <p style="font-size: 1.5rem; font-weight: 600; color: #1D1D1F;">{top_3_share:.1f}%</p>
                <p style="color: #86868B;">Top 3 makers share</p>
            </div>
            """, unsafe_allow_html=True)

            hhi = sum((r/total_revenue*100)**2 for r in maker_revenue.values) if total_revenue > 0 else 0
            concentration = "High" if hhi > 2500 else "Moderate" if hhi > 1500 else "Low"

            st.markdown(f"""
            <div style="background: #F5F5F7; border-radius: 12px; padding: 1.5rem;">
                <p style="color: #86868B; margin-bottom: 0.5rem;">HHI Index</p>
                <p style="font-size: 1.5rem; font-weight: 600; color: #1D1D1F;">{hhi:.0f}</p>
                <p style="color: #86868B;">{concentration} concentration</p>
            </div>
            """, unsafe_allow_html=True)

        # Panel maker trends
        st.divider()
        st.markdown("#### Panel Maker Trends Over Time")

        top_5_makers = maker_revenue.head(5).index.tolist()
        maker_trends = shipments_df[shipments_df['panel_maker'].isin(top_5_makers)].copy()
        # Filter out annual aggregates and extract period
        maker_trends = maker_trends[~maker_trends['date'].str.contains('ALL', na=False)]
        maker_trends['period'] = maker_trends['date'].str.split(' ').str[0]
        maker_monthly = maker_trends.groupby(['period', 'panel_maker'])['revenue_m'].sum().reset_index()
        maker_monthly = maker_monthly.sort_values('period')

        fig = px.line(
            maker_monthly,
            x='period',
            y='revenue_m',
            color='panel_maker',
            color_discrete_sequence=theme['color_discrete_sequence'],
            markers=True
        )
        fig.update_layout(
            **theme['layout'],
            xaxis_title="Quarter",
            yaxis_title="Revenue ($M)",
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No panel maker data available.")


# Tab 5: Detailed Data
with tab5:
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
                "units_k": st.column_config.NumberColumn("Units (K)", format="%.1f"),
                "revenue_m": st.column_config.NumberColumn("Revenue ($M)", format="$%.2f")
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)
        create_download_buttons(shipments_df, "shipments", "Shipments Intelligence Report")

    else:
        st.info("No shipment data available for the selected filters.")

    # Insights section (if data exists)
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
