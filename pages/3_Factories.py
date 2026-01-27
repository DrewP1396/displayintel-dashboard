"""
Factories Page - Display Intelligence Dashboard
Factory database, utilization tracking, and capacity analysis.
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
    page_title="Factories - Display Intelligence",
    page_icon="🏭",
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
    <h1>🏭 Factory Intelligence</h1>
    <p style="color: #86868B; font-size: 1.1rem; margin-bottom: 2rem;">
        Comprehensive database of display manufacturing facilities worldwide
    </p>
""", unsafe_allow_html=True)

# Filters in sidebar
with st.sidebar:
    st.markdown("### Filters")

    manufacturer = st.selectbox(
        "Manufacturer",
        options=DatabaseManager.get_manufacturers(),
        key="factory_manufacturer"
    )

    technology = st.selectbox(
        "Technology",
        options=DatabaseManager.get_technologies(),
        key="factory_technology"
    )

    region = st.selectbox(
        "Region",
        options=DatabaseManager.get_regions(),
        key="factory_region"
    )

    status_options = ["All", "operating", "constructing", "planned", "closed"]
    status = st.selectbox(
        "Status",
        options=status_options,
        key="factory_status"
    )

    st.divider()

    # Date range for utilization
    st.markdown("### Utilization Date Range")
    min_date, max_date = DatabaseManager.get_date_range()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start",
            value=date(2023, 1, 1),
            min_value=datetime.strptime(min_date, "%Y-%m-%d").date(),
            max_value=datetime.strptime(max_date, "%Y-%m-%d").date(),
            key="util_start"
        )
    with col2:
        end_date = st.date_input(
            "End",
            value=datetime.strptime(max_date, "%Y-%m-%d").date(),
            min_value=datetime.strptime(min_date, "%Y-%m-%d").date(),
            max_value=datetime.strptime(max_date, "%Y-%m-%d").date(),
            key="util_end"
        )

# Main content tabs
tab1, tab2, tab3 = st.tabs(["Factory Database", "Utilization Analysis", "Capacity Overview"])

# Tab 1: Factory Database
with tab1:
    # Load factory data
    factories_df = DatabaseManager.get_factories(
        manufacturer=manufacturer,
        technology=technology,
        region=region,
        status=status
    )

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Factories", len(factories_df))

    with col2:
        operating = len(factories_df[factories_df['status'] == 'operating'])
        st.metric("Operating", operating)

    with col3:
        unique_mfrs = factories_df['manufacturer'].nunique()
        st.metric("Manufacturers", unique_mfrs)

    with col4:
        unique_regions = factories_df['region'].nunique()
        st.metric("Regions", unique_regions)

    st.divider()

    # Charts row
    col1, col2 = st.columns(2)

    theme = get_plotly_theme()

    with col1:
        st.markdown("#### Factories by Manufacturer")
        # Handle NULL/None manufacturer values
        mfr_df = factories_df.copy()
        mfr_df['manufacturer'] = mfr_df['manufacturer'].fillna('Unknown').replace('', 'Unknown')
        mfr_counts = mfr_df['manufacturer'].value_counts().head(15)

        fig = px.bar(
            x=mfr_counts.values,
            y=mfr_counts.index,
            orientation='h',
            color_discrete_sequence=theme['color_discrete_sequence']
        )
        fig.update_layout(
            **theme['layout'],
            showlegend=False,
            xaxis_title="Number of Factories",
            yaxis_title="",
            height=400
        )
        fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Factories by Technology")
        # Handle NULL/None technology values
        tech_df = factories_df.copy()
        tech_df['technology'] = tech_df['technology'].fillna('Unknown').replace('', 'Unknown')
        tech_counts = tech_df['technology'].value_counts()

        fig = px.pie(
            values=tech_counts.values,
            names=tech_counts.index,
            color_discrete_sequence=theme['color_discrete_sequence'],
            hole=0.4
        )
        fig.update_layout(
            **theme['layout'],
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Data table
    st.markdown("#### Factory Database")

    # Select display columns
    display_cols = [
        'factory_id', 'manufacturer', 'factory_name', 'location', 'region',
        'technology', 'generation', 'application_category', 'status'
    ]
    available_cols = [c for c in display_cols if c in factories_df.columns]

    st.dataframe(
        factories_df[available_cols],
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "factory_id": st.column_config.TextColumn("Factory ID", width="medium"),
            "manufacturer": st.column_config.TextColumn("Manufacturer", width="small"),
            "factory_name": st.column_config.TextColumn("Factory Name", width="medium"),
            "location": st.column_config.TextColumn("Location", width="medium"),
            "region": st.column_config.TextColumn("Region", width="small"),
            "technology": st.column_config.TextColumn("Tech", width="small"),
            "generation": st.column_config.TextColumn("Gen", width="small"),
            "application_category": st.column_config.TextColumn("Application", width="small"),
            "status": st.column_config.TextColumn("Status", width="small")
        }
    )

    # Export buttons
    st.markdown("<br>", unsafe_allow_html=True)
    create_download_buttons(factories_df, "factories", "Factory Database Report")


# Tab 2: Utilization Analysis
with tab2:
    # Load utilization data
    util_df = DatabaseManager.get_utilization(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        manufacturer=manufacturer if manufacturer != "All" else None
    )

    if len(util_df) > 0:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_util = util_df['utilization_pct'].mean()
            st.metric("Avg Utilization", f"{avg_util:.1f}%")

        with col2:
            max_util = util_df['utilization_pct'].max()
            st.metric("Max Utilization", f"{max_util:.1f}%")

        with col3:
            total_capacity = util_df.groupby('date')['capacity_ksheets'].sum().mean()
            st.metric("Avg Capacity", f"{total_capacity:,.0f}K sheets")

        with col4:
            factories_count = util_df['factory_id'].nunique()
            st.metric("Factories Tracked", factories_count)

        st.divider()

        # Utilization over time
        st.markdown("#### Utilization Trends Over Time")

        util_by_date = util_df.groupby('date').agg({
            'utilization_pct': 'mean',
            'capacity_ksheets': 'sum',
            'actual_input_ksheets': 'sum'
        }).reset_index()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=util_by_date['date'],
            y=util_by_date['utilization_pct'],
            mode='lines+markers',
            name='Utilization %',
            line=dict(color=theme['color_discrete_sequence'][0], width=2),
            marker=dict(size=6)
        ))

        fig.update_layout(
            **theme['layout'],
            xaxis_title="Date",
            yaxis_title="Utilization (%)",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Utilization by manufacturer
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Utilization by Manufacturer")

            # Handle NULL/None manufacturer values
            util_mfr_df = util_df.copy()
            util_mfr_df['manufacturer'] = util_mfr_df['manufacturer'].fillna('Unknown').replace('', 'Unknown')
            util_by_mfr = util_mfr_df.groupby('manufacturer')['utilization_pct'].mean().sort_values(ascending=True)

            fig = px.bar(
                x=util_by_mfr.values,
                y=util_by_mfr.index,
                orientation='h',
                color_discrete_sequence=theme['color_discrete_sequence']
            )
            fig.update_layout(
                **theme['layout'],
                showlegend=False,
                xaxis_title="Average Utilization (%)",
                yaxis_title="",
                height=400
            )
            fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Utilization Distribution")

            fig = px.histogram(
                util_df,
                x='utilization_pct',
                nbins=30,
                color_discrete_sequence=theme['color_discrete_sequence']
            )
            fig.update_layout(
                **theme['layout'],
                showlegend=False,
                xaxis_title="Utilization (%)",
                yaxis_title="Count",
                height=400
            )
            fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Detailed utilization table
        st.markdown("#### Utilization Details")

        util_display_cols = [
            'date', 'manufacturer', 'factory_name', 'utilization_pct',
            'capacity_ksheets', 'actual_input_ksheets', 'technology'
        ]
        available_cols = [c for c in util_display_cols if c in util_df.columns]

        st.dataframe(
            util_df[available_cols].head(500),
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "date": st.column_config.TextColumn("Date", width="small"),
                "manufacturer": st.column_config.TextColumn("Manufacturer", width="small"),
                "factory_name": st.column_config.TextColumn("Factory", width="medium"),
                "utilization_pct": st.column_config.NumberColumn("Utilization %", format="%.1f"),
                "capacity_ksheets": st.column_config.NumberColumn("Capacity (K)", format="%.0f"),
                "actual_input_ksheets": st.column_config.NumberColumn("Input (K)", format="%.0f"),
                "technology": st.column_config.TextColumn("Tech", width="small")
            }
        )

        create_download_buttons(util_df, "utilization", "Utilization Report")

    else:
        st.info("No utilization data available for the selected filters.")


# Tab 3: Capacity Overview
with tab3:
    # Load utilization data for capacity analysis
    util_df = DatabaseManager.get_utilization(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )

    if len(util_df) > 0:
        st.markdown("#### Total Industry Capacity Over Time")

        capacity_by_date = util_df.groupby('date').agg({
            'capacity_ksheets': 'sum',
            'actual_input_ksheets': 'sum',
            'capacity_sqm_k': 'sum'
        }).reset_index()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=capacity_by_date['date'],
            y=capacity_by_date['capacity_ksheets'],
            mode='lines',
            name='Total Capacity',
            fill='tozeroy',
            line=dict(color=theme['color_discrete_sequence'][0], width=2),
            fillcolor='rgba(0, 122, 255, 0.1)'
        ))

        fig.add_trace(go.Scatter(
            x=capacity_by_date['date'],
            y=capacity_by_date['actual_input_ksheets'],
            mode='lines',
            name='Actual Input',
            line=dict(color=theme['color_discrete_sequence'][1], width=2)
        ))

        fig.update_layout(
            **theme['layout'],
            xaxis_title="Date",
            yaxis_title="K Sheets",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Capacity by manufacturer
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Capacity Share by Manufacturer")

            latest_date = util_df['date'].max()
            # Handle NULL/None manufacturer values
            capacity_df = util_df[util_df['date'] == latest_date].copy()
            capacity_df['manufacturer'] = capacity_df['manufacturer'].fillna('Unknown').replace('', 'Unknown')
            latest_capacity = capacity_df.groupby('manufacturer')['capacity_ksheets'].sum()

            fig = px.pie(
                values=latest_capacity.values,
                names=latest_capacity.index,
                color_discrete_sequence=theme['color_discrete_sequence'],
                hole=0.4
            )
            fig.update_layout(
                **theme['layout'],
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Capacity by Technology")

            # Handle NULL/None technology values
            tech_util_df = util_df.copy()
            tech_util_df['technology'] = tech_util_df['technology'].fillna('Unknown').replace('', 'Unknown')
            capacity_by_tech = tech_util_df.groupby('technology')['capacity_ksheets'].sum()

            fig = px.bar(
                x=capacity_by_tech.index,
                y=capacity_by_tech.values,
                color_discrete_sequence=theme['color_discrete_sequence']
            )
            fig.update_layout(
                **theme['layout'],
                showlegend=False,
                xaxis_title="Technology",
                yaxis_title="Total Capacity (K Sheets)",
                height=400
            )
            fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
            st.plotly_chart(fig, use_container_width=True)

        # Regional capacity breakdown
        st.divider()
        st.markdown("#### Regional Capacity Distribution")

        # Handle NULL/None region values
        region_df = util_df.copy()
        region_df['region'] = region_df['region'].fillna('Unknown').replace('', 'Unknown')
        capacity_by_region = region_df.groupby('region')['capacity_ksheets'].sum().sort_values(ascending=False)

        fig = px.bar(
            x=capacity_by_region.index,
            y=capacity_by_region.values,
            color_discrete_sequence=theme['color_discrete_sequence']
        )
        fig.update_layout(
            **theme['layout'],
            showlegend=False,
            xaxis_title="Region",
            yaxis_title="Total Capacity (K Sheets)",
            height=350
        )
        fig.update_traces(marker_color=theme['color_discrete_sequence'][0])
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No capacity data available for the selected date range.")
