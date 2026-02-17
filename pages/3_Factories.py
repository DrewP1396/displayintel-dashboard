"""
Factories Page - Display Intelligence Dashboard
Factory database, utilization tracking, and capacity analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import get_css, get_plotly_theme, apply_chart_theme, format_with_commas, format_percent
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

# Check authentication (restore session from cookie if available)

if not st.session_state.get("password_correct", False):
    st.warning("Please login from the main page.")
    st.stop()


def natural_sort_key(s):
    """Sort strings with embedded numbers naturally (B1, B2, B10 not B1, B10, B2)."""
    if pd.isna(s):
        return []
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


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

    # Factory-specific filter (depends on manufacturer selection)
    factory_options = DatabaseManager.get_factory_names(manufacturer)
    selected_factory = st.selectbox(
        "Factory",
        options=factory_options,
        key="factory_specific"
    )

    st.divider()

    # Only show these filters in "All Factories" view
    if selected_factory == "All Factories":
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
    else:
        # Set defaults when viewing specific factory
        technology = "All"
        region = "All"
        status = "All"

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
        # Default end date to today (not max DB date which may be years in the future)
        default_end = min(date.today(), datetime.strptime(max_date, "%Y-%m-%d").date())
        end_date = st.date_input(
            "End",
            value=default_end,
            min_value=datetime.strptime(min_date, "%Y-%m-%d").date(),
            max_value=datetime.strptime(max_date, "%Y-%m-%d").date(),
            key="util_end"
        )

# Get theme colors
theme = get_plotly_theme()
colors = theme['color_discrete_sequence']

# =============================================================================
# Factory Detail View (when specific factory is selected)
# =============================================================================
if selected_factory != "All Factories":
    # Get factory data (may have multiple entries for different backplanes)
    factory_df = DatabaseManager.get_factory_by_name(selected_factory)

    if factory_df is not None and len(factory_df) > 0:
        # Use first entry for general info
        factory = factory_df.iloc[0]

        # Get all backplane types for this factory
        backplanes = factory_df['backplane'].dropna().unique().tolist()
        backplane_str = ", ".join(backplanes) if backplanes else "-"

        # Get MP Ramp dates by backplane from factories table
        def format_quarter(date_val):
            """Format date as quarter (e.g., CQ1'19)."""
            if pd.isna(date_val) or not date_val:
                return None
            try:
                if isinstance(date_val, str):
                    if len(date_val) == 4:  # Just year like "2015"
                        return f"CQ1'{date_val[2:]}"
                    date_val = pd.to_datetime(date_val)
                q = (date_val.month - 1) // 3 + 1
                return f"CQ{q}'{str(date_val.year)[2:]}"
            except:
                return str(date_val)[:10] if date_val else None

        ramp_by_bp = {}
        for _, row in factory_df.iterrows():
            bp = row.get('backplane', 'Unknown')
            mp_ramp = row.get('mp_ramp_date')
            if mp_ramp and bp:
                ramp_by_bp[bp] = format_quarter(mp_ramp)

        # Get earliest ramp date for display
        ramp_dates = [r for r in ramp_by_bp.values() if r]
        ramp_date = min(ramp_dates) if ramp_dates else None

        # Header with back context
        tech = factory.get('technology', 'Unknown') or 'Unknown'
        gen = factory.get('generation', '') or ''
        st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <span style="color: #86868B; font-size: 0.9rem;">
                    {factory.get('manufacturer', 'Unknown')} &gt; {selected_factory}
                </span>
                <span style="background: {'#007AFF' if tech == 'OLED' else '#34C759'}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin-left: 8px;">
                    {tech} {gen}
                </span>
            </div>
        """, unsafe_allow_html=True)

        # Factory Summary Card
        st.markdown("### Factory Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Factory", selected_factory)
            st.metric("Generation", factory.get('generation', '-') or "-")

        with col2:
            st.metric("Location", factory.get('location', '-') or "-")
            st.metric("Technology", factory.get('technology', '-') or "-")

        with col3:
            st.metric("Region", factory.get('region', '-') or "-")
            st.metric("Backplanes", backplane_str)

        with col4:
            st.metric("Status", (factory.get('status', '-') or "-").title())
            st.metric("First Ramp", ramp_date or "Not yet")

        st.divider()

        # Capacity by Backplane Technology
        st.markdown("### Capacity by Backplane Technology")

        # Get capacity data for this factory and related production lines
        backplane_df = DatabaseManager.get_capacity_by_backplane(
            manufacturer=factory.get('manufacturer'),
            factory_name=selected_factory
        )

        if len(backplane_df) > 0:
            # Group by backplane and sum capacity
            bp_summary = backplane_df.groupby('backplane').agg({
                'capacity_ksheets': 'sum',
                'actual_input_ksheets': 'sum',
                'factory_name': 'count'
            }).reset_index()
            bp_summary.columns = ['Backplane', 'Capacity (K/mo)', 'Input (K/mo)', 'Lines']

            # Calculate total
            total_capacity = bp_summary['Capacity (K/mo)'].sum()
            total_input = bp_summary['Input (K/mo)'].sum()

            # Display metrics with ramp dates
            cols = st.columns(len(bp_summary) + 1)

            # Total column
            with cols[0]:
                st.metric("Total Capacity", f"{total_capacity:,.1f}K/mo")

            # Per-backplane columns with ramp date
            for i, row in bp_summary.iterrows():
                with cols[i + 1]:
                    bp_name = row['Backplane'] or 'Unknown'
                    bp_ramp = ramp_by_bp.get(bp_name, '')
                    label = f"{bp_name}" + (f" ({bp_ramp})" if bp_ramp else "")
                    st.metric(label, f"{row['Capacity (K/mo)']:,.1f}K/mo")

            # Show detailed breakdown table
            with st.expander("View Production Lines"):
                bp_display = backplane_df[['factory_name', 'backplane', 'generation', 'capacity_ksheets', 'actual_input_ksheets', 'utilization_pct']].copy()
                bp_display['capacity_ksheets'] = bp_display['capacity_ksheets'].apply(lambda x: f"{x:,.1f}" if pd.notna(x) else "-")
                bp_display['actual_input_ksheets'] = bp_display['actual_input_ksheets'].apply(lambda x: f"{x:,.1f}" if pd.notna(x) else "-")
                bp_display['utilization_pct'] = bp_display['utilization_pct'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")

                st.dataframe(
                    bp_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "factory_name": st.column_config.TextColumn("Line", width="medium"),
                        "backplane": st.column_config.TextColumn("Backplane", width="small"),
                        "generation": st.column_config.TextColumn("Gen", width="small"),
                        "capacity_ksheets": st.column_config.TextColumn("Capacity (K/mo)", width="small"),
                        "actual_input_ksheets": st.column_config.TextColumn("Input (K/mo)", width="small"),
                        "utilization_pct": st.column_config.TextColumn("Util %", width="small")
                    }
                )
        else:
            st.info("No capacity data available.")

        # Capacity Installments by Quarter
        st.markdown("### Capacity Installments by Quarter")

        # Get full utilization history to show capacity additions
        full_util_df = DatabaseManager.get_utilization(factory_name=selected_factory)

        if len(full_util_df) > 0:
            # Group by quarter and backplane, get capacity
            full_util_df['quarter'] = pd.to_datetime(full_util_df['date']).dt.to_period('Q').astype(str)

            # Get capacity per quarter per backplane
            quarterly_cap = full_util_df.groupby(['quarter', 'backplane']).agg({
                'capacity_ksheets': 'max'  # Use max capacity for each quarter
            }).reset_index()

            # Calculate capacity additions (difference from previous quarter)
            quarterly_cap = quarterly_cap.sort_values(['backplane', 'quarter'])
            quarterly_cap['capacity_change'] = quarterly_cap.groupby('backplane')['capacity_ksheets'].diff().fillna(quarterly_cap['capacity_ksheets'])

            # Only show quarters with capacity additions
            additions = quarterly_cap[quarterly_cap['capacity_change'] > 0.5].copy()

            if len(additions) > 0:
                # Sort additions chronologically
                additions = additions.sort_values('quarter')

                # Get all quarters in sorted order for x-axis
                all_quarters = sorted(additions['quarter'].unique())

                # Create stacked bar chart
                fig = go.Figure()

                for bp in additions['backplane'].unique():
                    bp_data = additions[additions['backplane'] == bp]
                    fig.add_trace(go.Bar(
                        x=bp_data['quarter'].tolist(),
                        y=bp_data['capacity_change'].tolist(),
                        name=bp,
                        hovertemplate=f'{bp}<br>%{{x}}<br>+%{{y:,.1f}}K/mo<extra></extra>'
                    ))

                apply_chart_theme(fig)
                fig.update_layout(
                    xaxis_title="Quarter",
                    yaxis_title="Capacity Added (K/mo)",
                    height=300,
                    barmode='group',
                    showlegend=True,
                    xaxis={'categoryorder': 'array', 'categoryarray': all_quarters}
                )
                st.plotly_chart(fig, use_container_width=True)

                # Show table of additions
                with st.expander("View Capacity Addition Details"):
                    additions_display = additions[['quarter', 'backplane', 'capacity_change', 'capacity_ksheets']].copy()
                    additions_display = additions_display.sort_values('quarter')
                    additions_display.columns = ['Quarter', 'Backplane', 'Added (K/mo)', 'Total (K/mo)']
                    additions_display['Added (K/mo)'] = additions_display['Added (K/mo)'].apply(lambda x: f"{x:,.1f}")
                    additions_display['Total (K/mo)'] = additions_display['Total (K/mo)'].apply(lambda x: f"{x:,.1f}")
                    st.dataframe(additions_display, use_container_width=True, hide_index=True)
            else:
                st.info("No capacity additions found in the data.")
        else:
            st.info("No capacity history available.")

        st.divider()

        # Get utilization data for this factory (all backplane variants)
        util_df = DatabaseManager.get_utilization(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            factory_name=selected_factory
        )

        # Filter out future quarters with no actual data (all 0%)
        if len(util_df) > 0:
            current_quarter_end = pd.Timestamp.today().to_period('Q').end_time.strftime("%Y-%m-%d")
            util_df = util_df[util_df['date'] <= current_quarter_end]

        # Current metrics from latest utilization with actual data (not projections)
        if len(util_df) > 0:
            # Get latest date with actual input > 0
            util_with_data = util_df[util_df['actual_input_ksheets'] > 0]
            if len(util_with_data) > 0:
                latest_date = util_with_data['date'].max()
            else:
                latest_date = util_df['date'].max()
            latest_data = util_df[util_df['date'] == latest_date]

            total_capacity = latest_data['capacity_ksheets'].sum()
            total_input = latest_data['actual_input_ksheets'].sum()
            avg_util = (total_input / total_capacity * 100) if total_capacity > 0 else 0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Utilization", f"{avg_util:.1f}%")
            with col2:
                st.metric("Total Capacity (K/mo)", f"{total_capacity:,.1f}")
            with col3:
                st.metric("Total Input (K/mo)", f"{total_input:,.1f}")

            st.divider()

            # Utilization Timeline by Backplane
            st.markdown("### Utilization Timeline by Backplane")

            fig = go.Figure()

            # Group by date and backplane
            backplanes_in_data = sorted(util_df['backplane'].dropna().unique())

            for i, bp in enumerate(backplanes_in_data):
                bp_data = util_df[util_df['backplane'] == bp].groupby('date').agg({
                    'capacity_ksheets': 'sum',
                    'actual_input_ksheets': 'sum'
                }).reset_index()
                bp_data['utilization_pct'] = (bp_data['actual_input_ksheets'] / bp_data['capacity_ksheets'] * 100)

                fig.add_trace(go.Scatter(
                    x=bp_data['date'].tolist(),
                    y=bp_data['utilization_pct'].tolist(),
                    mode='lines+markers',
                    name=f'{bp} ({bp_data["capacity_ksheets"].iloc[-1]:,.0f}K cap)',
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=6),
                    hovertemplate=f'{bp}<br>%{{x}}<br>Utilization: %{{y:.1f}}%<br>Capacity: {bp_data["capacity_ksheets"].iloc[-1]:,.1f}K/mo<extra></extra>'
                ))

            # Note if utilization rates are identical across backplanes
            if len(backplanes_in_data) > 1:
                # Check if util % is the same across backplanes on shared dates
                shared_dates = util_df.groupby('date').filter(lambda x: x['backplane'].nunique() > 1)
                if len(shared_dates) > 0:
                    util_spread = shared_dates.groupby('date')['utilization_pct'].std().mean()
                    if util_spread < 0.1:
                        st.caption("Note: Source data applies the same utilization rate across backplane lines. "
                                   "Lines overlap on the chart. See Capacity vs Input below for per-backplane breakdown.")

            # Add ramp date annotation if available
            if ramp_date and ramp_date in util_df['date'].values:
                fig.add_vline(
                    x=ramp_date,
                    line_dash="dash",
                    line_color="green",
                    annotation_text="First Ramp",
                    annotation_position="top"
                )

            apply_chart_theme(fig)
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Utilization (%)",
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Capacity and Input Chart - total factory snapshot
            st.markdown("### Monthly Capacity vs Actual Input")

            # Aggregate across all backplanes for factory-level view
            factory_totals = util_df.groupby('date').agg({
                'capacity_ksheets': 'sum',
                'actual_input_ksheets': 'sum'
            }).reset_index()
            factory_totals['utilization_pct'] = (
                factory_totals['actual_input_ksheets'] / factory_totals['capacity_ksheets'] * 100
            ).round(1)

            fig2 = go.Figure()

            fig2.add_trace(go.Bar(
                x=factory_totals['date'].tolist(),
                y=factory_totals['capacity_ksheets'].tolist(),
                name='Total Capacity',
                marker_color=colors[0],
                opacity=0.7,
                hovertemplate='Capacity: %{y:,.1f}K/mo<extra></extra>'
            ))

            fig2.add_trace(go.Scatter(
                x=factory_totals['date'].tolist(),
                y=factory_totals['actual_input_ksheets'].tolist(),
                mode='lines+markers',
                name='Actual Input',
                line=dict(color=colors[1], width=2),
                hovertemplate='Input: %{y:,.1f}K/mo<extra></extra>'
            ))

            apply_chart_theme(fig2)
            fig2.update_layout(
                xaxis_title="Date",
                yaxis_title="K Sheets / Month",
                height=350,
                barmode='overlay',
                hovermode='x unified'
            )

            st.plotly_chart(fig2, use_container_width=True)

        else:
            st.info("No utilization data available for this factory in the selected date range.")

        st.divider()

        # Equipment Orders for this factory (get orders for all backplane variants)
        st.markdown("### Equipment Orders")

        # Get all factory_ids for this factory name
        factory_ids = factory_df['factory_id'].tolist()
        equip_dfs = [DatabaseManager.get_equipment_orders_for_factory(fid) for fid in factory_ids]
        equip_df = pd.concat(equip_dfs, ignore_index=True) if equip_dfs else pd.DataFrame()

        if len(equip_df) > 0:
            # Summary metrics
            total_orders = len(equip_df)
            total_value = equip_df['amount_usd'].sum() if 'amount_usd' in equip_df.columns else 0
            total_units = equip_df['units'].sum() if 'units' in equip_df.columns else 0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Orders", format_with_commas(total_orders))
            with col2:
                if total_value and total_value > 0:
                    st.metric("Total Value", f"${total_value/1e6:.1f}M" if total_value < 1e9 else f"${total_value/1e9:.2f}B")
                else:
                    st.metric("Total Value", "-")
            with col3:
                st.metric("Total Units", format_with_commas(total_units) if total_units else "-")

            # Equipment orders table - format for display
            display_cols = ['po_year', 'po_quarter', 'vendor', 'equipment_type', 'units', 'amount_usd']
            available_cols = [c for c in display_cols if c in equip_df.columns]

            equip_display = equip_df[available_cols].head(100).copy()

            # Format columns for cleaner display
            if 'units' in equip_display.columns:
                equip_display['units'] = equip_display['units'].apply(lambda x: f"{int(x):,}" if pd.notna(x) and x > 0 else "-")
            if 'amount_usd' in equip_display.columns:
                equip_display['amount_usd'] = equip_display['amount_usd'].apply(
                    lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "-"
                )

            st.dataframe(
                equip_display,
                use_container_width=True,
                hide_index=True,
                height=300,
                column_config={
                    "po_year": st.column_config.TextColumn("Year", width="small"),
                    "po_quarter": st.column_config.TextColumn("Qtr", width="small"),
                    "vendor": st.column_config.TextColumn("Vendor", width="medium"),
                    "equipment_type": st.column_config.TextColumn("Equipment", width="medium"),
                    "units": st.column_config.TextColumn("Units", width="small"),
                    "amount_usd": st.column_config.TextColumn("Value", width="medium")
                }
            )
        else:
            st.info("No equipment orders found for this factory.")

    else:
        st.error(f"Factory '{selected_factory}' not found.")

else:
    # =============================================================================
    # All Factories View (original tabs)
    # =============================================================================

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Factory Database", "Utilization Analysis", "Capacity Overview", "Factory Comparison"])

    # Tab 1: Factory Database
    with tab1:
        # Load factory data
        try:
            factories_df = DatabaseManager.get_factories(
                manufacturer=manufacturer,
                technology=technology,
                region=region,
                status=status
            )
        except Exception as e:
            st.error(f"Error loading factory data: {str(e)}")
            st.stop()

        # Add ramp dates to factories
        ramp_dates = DatabaseManager.get_all_factory_ramp_dates()
        factories_df['ramp_date'] = factories_df['factory_id'].map(ramp_dates)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Factories", format_with_commas(len(factories_df)))

        with col2:
            operating = len(factories_df[factories_df['status'] == 'operating'])
            st.metric("Operating", format_with_commas(operating))

        with col3:
            unique_mfrs = factories_df['manufacturer'].nunique()
            st.metric("Manufacturers", format_with_commas(unique_mfrs))

        with col4:
            unique_regions = factories_df['region'].nunique()
            st.metric("Regions", format_with_commas(unique_regions))

        st.divider()

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Factories by Manufacturer")
            # Filter out NULL/empty values and get counts
            mfr_data = factories_df[factories_df['manufacturer'].notna() & (factories_df['manufacturer'] != '')]
            mfr_counts = mfr_data['manufacturer'].value_counts().head(15)

            if len(mfr_counts) > 0:
                fig = px.bar(
                    x=mfr_counts.values.tolist(),
                    y=mfr_counts.index.tolist(),
                    orientation='h',
                    labels={'x': 'Number of Factories', 'y': 'Manufacturer'}
                )
                fig.update_traces(marker_color=colors[0], hovertemplate='%{y}: %{x} factories<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Number of Factories",
                    yaxis_title="",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No manufacturer data available")

        with col2:
            st.markdown("#### Factories by Technology")
            # Filter out NULL/empty values
            tech_data = factories_df[factories_df['technology'].notna() & (factories_df['technology'] != '')]
            tech_counts = tech_data['technology'].value_counts()

            if len(tech_counts) > 0:
                fig = px.pie(
                    values=tech_counts.values.tolist(),
                    names=tech_counts.index.tolist(),
                    color_discrete_sequence=colors,
                    hole=0.4
                )
                fig.update_traces(hovertemplate='%{label}: %{value} factories (%{percent})<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No technology data available")

        st.divider()

        # Data table
        st.markdown("#### Factory Database")

        # Select display columns with ramp_date
        display_cols = [
            'factory_id', 'manufacturer', 'factory_name', 'location', 'region',
            'technology', 'generation', 'application_category', 'status', 'ramp_date'
        ]
        available_cols = [c for c in display_cols if c in factories_df.columns]

        # Sort naturally by factory_name
        display_df = factories_df[available_cols].copy()
        if 'factory_name' in display_df.columns:
            display_df = display_df.iloc[display_df['factory_name'].map(natural_sort_key).argsort()]

        column_config = {
            "factory_id": st.column_config.TextColumn("Factory ID", width="medium"),
            "manufacturer": st.column_config.TextColumn("Manufacturer", width="small"),
            "factory_name": st.column_config.TextColumn("Factory Name", width="medium"),
            "location": st.column_config.TextColumn("Location", width="medium"),
            "region": st.column_config.TextColumn("Region", width="small"),
            "technology": st.column_config.TextColumn("Tech", width="small"),
            "generation": st.column_config.TextColumn("Gen", width="small"),
            "application_category": st.column_config.TextColumn("Application", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "ramp_date": st.column_config.TextColumn("Ramp Date", width="small")
        }

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config=column_config
        )

        # Export buttons
        st.markdown("<br>", unsafe_allow_html=True)
        create_download_buttons(factories_df, "factories", "Factory Database Report")


    # Tab 2: Utilization Analysis
    with tab2:
        # Load utilization data
        try:
            util_df = DatabaseManager.get_utilization(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                manufacturer=manufacturer if manufacturer != "All" else None
            )
        except Exception as e:
            st.error(f"Error loading utilization data: {str(e)}")
            st.stop()

        # Filter out future quarters with no actual data
        if len(util_df) > 0:
            current_quarter_end = pd.Timestamp.today().to_period('Q').end_time.strftime("%Y-%m-%d")
            util_df = util_df[util_df['date'] <= current_quarter_end]

        if len(util_df) > 0:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_util = util_df['utilization_pct'].mean()
                st.metric("Avg Utilization", format_percent(avg_util))

            with col2:
                max_util = util_df['utilization_pct'].max()
                st.metric("Max Utilization", format_percent(max_util))

            with col3:
                total_capacity = util_df.groupby('date')['capacity_ksheets'].sum().mean()
                st.metric("Avg Monthly Capacity", f"{total_capacity:,.0f}K/mo")

            with col4:
                factories_count = util_df['factory_id'].nunique()
                st.metric("Factories Tracked", format_with_commas(factories_count))

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
                x=util_by_date['date'].tolist(),
                y=util_by_date['utilization_pct'].tolist(),
                mode='lines+markers',
                name='Utilization %',
                line=dict(color=colors[0], width=2),
                marker=dict(size=6),
                hovertemplate='%{x}<br>Utilization: %{y:.1f}%<extra></extra>'
            ))

            apply_chart_theme(fig)
            fig.update_layout(
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

                # Filter out NULL/empty manufacturers
                util_mfr_df = util_df[util_df['manufacturer'].notna() & (util_df['manufacturer'] != '')]
                util_by_mfr = util_mfr_df.groupby('manufacturer')['utilization_pct'].mean().sort_values(ascending=True)

                if len(util_by_mfr) > 0:
                    fig = px.bar(
                        x=util_by_mfr.values.tolist(),
                        y=util_by_mfr.index.tolist(),
                        orientation='h'
                    )
                    fig.update_traces(marker_color=colors[0], hovertemplate='%{y}: %{x:.1f}%<extra></extra>')
                    apply_chart_theme(fig)
                    fig.update_layout(
                        showlegend=False,
                        xaxis_title="Average Utilization (%)",
                        yaxis_title="",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### Utilization Distribution")

                fig = px.histogram(
                    util_df,
                    x='utilization_pct',
                    nbins=30
                )
                fig.update_traces(marker_color=colors[0])
                apply_chart_theme(fig)
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Utilization (%)",
                    yaxis_title="Count",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Detailed utilization table
            st.markdown("#### Monthly Utilization Details")

            util_display_cols = [
                'date', 'manufacturer', 'factory_name', 'technology', 'utilization_pct',
                'capacity_ksheets', 'actual_input_ksheets'
            ]
            available_cols = [c for c in util_display_cols if c in util_df.columns]

            # Format for display
            util_display = util_df[available_cols].head(500).copy()
            if 'utilization_pct' in util_display.columns:
                util_display['utilization_pct'] = util_display['utilization_pct'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
            if 'capacity_ksheets' in util_display.columns:
                util_display['capacity_ksheets'] = util_display['capacity_ksheets'].apply(lambda x: f"{x:,.1f}" if pd.notna(x) else "-")
            if 'actual_input_ksheets' in util_display.columns:
                util_display['actual_input_ksheets'] = util_display['actual_input_ksheets'].apply(lambda x: f"{x:,.1f}" if pd.notna(x) else "-")

            st.dataframe(
                util_display,
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    "date": st.column_config.TextColumn("Date", width="small"),
                    "manufacturer": st.column_config.TextColumn("Mfr", width="small"),
                    "factory_name": st.column_config.TextColumn("Factory", width="medium"),
                    "technology": st.column_config.TextColumn("Tech", width="small"),
                    "utilization_pct": st.column_config.TextColumn("Util %", width="small"),
                    "capacity_ksheets": st.column_config.TextColumn("Capacity (K/mo)", width="small"),
                    "actual_input_ksheets": st.column_config.TextColumn("Input (K/mo)", width="small")
                }
            )

            create_download_buttons(util_df, "utilization", "Utilization Report")

        else:
            st.info("No utilization data available for the selected filters.")


    # Tab 3: Capacity Overview
    with tab3:
        # Load utilization data for capacity analysis
        try:
            util_df = DatabaseManager.get_utilization(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
        except Exception as e:
            st.error(f"Error loading capacity data: {str(e)}")
            st.stop()

        # Filter out future quarters with no actual data
        if len(util_df) > 0:
            current_quarter_end = pd.Timestamp.today().to_period('Q').end_time.strftime("%Y-%m-%d")
            util_df = util_df[util_df['date'] <= current_quarter_end]

        if len(util_df) > 0:
            st.markdown("#### Total Industry Capacity Over Time")

            capacity_by_date = util_df.groupby('date').agg({
                'capacity_ksheets': 'sum',
                'actual_input_ksheets': 'sum',
                'capacity_sqm_k': 'sum'
            }).reset_index()

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=capacity_by_date['date'].tolist(),
                y=capacity_by_date['capacity_ksheets'].tolist(),
                mode='lines',
                name='Total Capacity',
                fill='tozeroy',
                line=dict(color=colors[0], width=2),
                fillcolor='rgba(0, 122, 255, 0.1)',
                hovertemplate='Capacity: %{y:,.0f}K<extra></extra>'
            ))

            fig.add_trace(go.Scatter(
                x=capacity_by_date['date'].tolist(),
                y=capacity_by_date['actual_input_ksheets'].tolist(),
                mode='lines',
                name='Actual Input',
                line=dict(color=colors[1], width=2),
                hovertemplate='Input: %{y:,.0f}K<extra></extra>'
            ))

            apply_chart_theme(fig)
            fig.update_layout(
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
                # Filter out NULL/empty manufacturers
                capacity_df = util_df[(util_df['date'] == latest_date) &
                                       util_df['manufacturer'].notna() &
                                       (util_df['manufacturer'] != '')]
                latest_capacity = capacity_df.groupby('manufacturer')['capacity_ksheets'].sum()

                if len(latest_capacity) > 0:
                    fig = px.pie(
                        values=latest_capacity.values.tolist(),
                        names=latest_capacity.index.tolist(),
                        color_discrete_sequence=colors,
                        hole=0.4
                    )
                    fig.update_traces(hovertemplate='%{label}: %{value:,.0f}K (%{percent})<extra></extra>')
                    apply_chart_theme(fig)
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### Capacity by Technology")

                # Filter out NULL/empty technologies
                tech_util_df = util_df[util_df['technology'].notna() & (util_df['technology'] != '')]
                capacity_by_tech = tech_util_df.groupby('technology')['capacity_ksheets'].sum()

                if len(capacity_by_tech) > 0:
                    fig = px.bar(
                        x=capacity_by_tech.index.tolist(),
                        y=capacity_by_tech.values.tolist()
                    )
                    fig.update_traces(marker_color=colors[0], hovertemplate='%{x}: %{y:,.0f}K<extra></extra>')
                    apply_chart_theme(fig)
                    fig.update_layout(
                        showlegend=False,
                        xaxis_title="Technology",
                        yaxis_title="Total Capacity (K Sheets)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Regional capacity breakdown
            st.divider()
            st.markdown("#### Regional Capacity Distribution")

            # Filter out NULL/empty regions
            region_df = util_df[util_df['region'].notna() & (util_df['region'] != '')]
            capacity_by_region = region_df.groupby('region')['capacity_ksheets'].sum().sort_values(ascending=False)

            if len(capacity_by_region) > 0:
                fig = px.bar(
                    x=capacity_by_region.index.tolist(),
                    y=capacity_by_region.values.tolist()
                )
                fig.update_traces(marker_color=colors[0], hovertemplate='%{x}: %{y:,.0f}K<extra></extra>')
                apply_chart_theme(fig)
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Region",
                    yaxis_title="Total Capacity (K Sheets)",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No capacity data available for the selected date range.")

    # Tab 4: Factory Comparison
    with tab4:
        # Depreciation rules by region
        DEPRECIATION_YEARS = {
            "S Korea": 5, "China": 7, "Taiwan": 7, "Japan": 5,
            "Singapore": 5, "India": 7,
        }

        def _format_mp_ramp(val):
            """Format MP ramp date for display."""
            if not val or pd.isna(val):
                return "-"
            s = str(val).strip()
            if s.lower().startswith("before"):
                return "2014 or earlier"
            try:
                dt = pd.to_datetime(s)
                q = (dt.month - 1) // 3 + 1
                return f"Q{q} {dt.year}"
            except Exception:
                return s[:10]

        # Build factory options list
        all_factories = DatabaseManager.get_factories()
        if len(all_factories) == 0:
            st.info("No factory data available.")
            st.stop()

        # Group by manufacturer + factory_name for display
        factory_groups = (
            all_factories
            .groupby(["manufacturer", "factory_name"])
            .first()
            .reset_index()
        )
        factory_groups["label"] = factory_groups.apply(
            lambda r: f"{r['manufacturer']} - {r['factory_name']} ({r.get('location') or r.get('region', '')})",
            axis=1,
        )
        label_to_name = dict(zip(factory_groups["label"], factory_groups["factory_name"]))

        st.markdown("#### Select Factories to Compare")
        st.caption("Choose 2-4 factories for side-by-side comparison.")

        selected_labels = st.multiselect(
            "Factories",
            options=sorted(factory_groups["label"].tolist(), key=natural_sort_key),
            max_selections=4,
            key="compare_factories",
            label_visibility="collapsed",
        )

        if len(selected_labels) < 2:
            st.info("Select at least 2 factories above to begin comparing.")
        else:
            # ── Gather data for each selected factory ──
            compare_data = []
            for label in selected_labels:
                fname = label_to_name[label]
                fdf = DatabaseManager.get_factory_by_name(fname)
                if fdf is None or len(fdf) == 0:
                    continue

                info = fdf.iloc[0]
                backplanes = fdf["backplane"].dropna().unique().tolist()
                region = info.get("region", "-") or "-"

                # Latest utilization
                util = DatabaseManager.get_utilization(factory_name=fname)
                latest_cap, latest_input, latest_util = 0.0, 0.0, 0.0
                if len(util) > 0:
                    util_actual = util[util["actual_input_ksheets"] > 0]
                    if len(util_actual) > 0:
                        ld = util_actual["date"].max()
                    else:
                        ld = util["date"].max()
                    latest = util[util["date"] == ld]
                    latest_cap = latest["capacity_ksheets"].sum()
                    latest_input = latest["actual_input_ksheets"].sum()
                    latest_util = (latest_input / latest_cap * 100) if latest_cap > 0 else 0

                # Equipment orders
                factory_ids = fdf["factory_id"].tolist()
                equip_dfs = [DatabaseManager.get_equipment_orders_for_factory(fid) for fid in factory_ids]
                equip = pd.concat(equip_dfs, ignore_index=True) if equip_dfs else pd.DataFrame()
                # Deduplicate by all columns (same order can match multiple factory_id patterns)
                if len(equip) > 0:
                    equip = equip.drop_duplicates()
                total_investment = equip["amount_usd"].sum() if len(equip) > 0 and "amount_usd" in equip.columns else 0

                # MP ramp dates per backplane
                ramp_by_bp = {}
                for _, row in fdf.iterrows():
                    bp = row.get("backplane", "Unknown")
                    mp = row.get("mp_ramp_date")
                    if mp and bp:
                        ramp_by_bp[bp] = _format_mp_ramp(mp)

                earliest_ramp = "-"
                for _, row in fdf.iterrows():
                    mp = row.get("mp_ramp_date")
                    if mp and str(mp).strip().lower().startswith("before"):
                        earliest_ramp = "2014 or earlier"
                        break
                    try:
                        dt = pd.to_datetime(mp)
                        if earliest_ramp == "-" or dt < pd.to_datetime(earliest_ramp.replace("Q", "").replace(" ", "-01-")):
                            earliest_ramp = _format_mp_ramp(mp)
                    except Exception:
                        pass

                dep_years = DEPRECIATION_YEARS.get(region, 5)

                compare_data.append({
                    "label": label,
                    "factory_name": fname,
                    "manufacturer": info.get("manufacturer", "-"),
                    "location": info.get("location", "-") or "-",
                    "region": region,
                    "technology": info.get("technology", "-") or "-",
                    "backplanes": backplanes,
                    "generation": info.get("generation", "-") or "-",
                    "application": info.get("application_category", "-") or "-",
                    "status": (info.get("status", "-") or "-").title(),
                    "probability": info.get("probability", "-") or "-",
                    "substrate": info.get("substrate", "-") or "-",
                    "capacity": latest_cap,
                    "input": latest_input,
                    "utilization": latest_util,
                    "total_investment": total_investment,
                    "ramp_by_bp": ramp_by_bp,
                    "earliest_ramp": earliest_ramp,
                    "dep_years": dep_years,
                    "factory_df": fdf,
                    "util_df": util,
                    "equip_df": equip,
                })

            if len(compare_data) < 2:
                st.warning("Could not load data for enough factories.")
            else:
                # ── Comparison Cards ──
                n = len(compare_data)
                cols = st.columns(n)

                for i, d in enumerate(compare_data):
                    with cols[i]:
                        tech = d["technology"]
                        tech_color = "#007AFF" if tech == "OLED" else "#34C759"

                        st.markdown(f"""
                        <div style="background:#fff;border:1px solid #E5E5EA;border-radius:12px;padding:16px 18px 12px;margin-bottom:8px;">
                            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                                <span style="font-size:1.15rem;font-weight:700;">{d['manufacturer']} {d['factory_name']}</span>
                                <span style="background:{tech_color};color:#fff;padding:1px 7px;border-radius:4px;font-size:0.7rem;font-weight:600;">{tech}</span>
                            </div>
                            <div style="color:#86868B;font-size:0.82rem;margin-bottom:10px;">{d['location']}, {d['region']} &nbsp;|&nbsp; {d['generation']} &nbsp;|&nbsp; {d['application']}</div>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;font-size:0.85rem;">
                                <div><span style="color:#86868B;">Capacity</span><br><b>{d['capacity']:,.1f}</b> K/mo</div>
                                <div><span style="color:#86868B;">Utilization</span><br><b>{d['utilization']:.1f}%</b></div>
                                <div><span style="color:#86868B;">Backplane</span><br><b>{', '.join(d['backplanes']) or '-'}</b></div>
                                <div><span style="color:#86868B;">Substrate</span><br><b>{d['substrate']}</b></div>
                                <div><span style="color:#86868B;">First Ramp</span><br><b>{d['earliest_ramp']}</b></div>
                                <div><span style="color:#86868B;">Status</span><br><b>{d['status']}</b> ({d['probability']})</div>
                            </div>
                            <div style="border-top:1px solid #E5E5EA;margin-top:10px;padding-top:8px;display:flex;justify-content:space-between;font-size:0.82rem;">
                                <span><span style="color:#86868B;">Depreciation:</span> <b>{d['dep_years']}yr</b> ({d['region']})</span>
                                <span><span style="color:#86868B;">Invest:</span> <b>{'${:,.0f}M'.format(d['total_investment']/1e6) if d['total_investment'] > 0 else '-'}</b></span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # ── Investment Timeline (expandable per factory) ──
                st.divider()
                st.markdown("#### Investment Timeline")

                timeline_cols = st.columns(n)
                for i, d in enumerate(compare_data):
                    with timeline_cols[i]:
                        equip = d["equip_df"]
                        if len(equip) > 0 and "po_year" in equip.columns:
                            yearly = equip.groupby("po_year").agg(
                                total_usd=("amount_usd", "sum"),
                                order_count=("amount_usd", "count"),
                                equip_types=("equipment_type", lambda x: ", ".join(sorted(x.dropna().unique())[:3])),
                            ).reset_index().sort_values("po_year")

                            with st.expander(f"{d['manufacturer']} {d['factory_name']} — {len(yearly)} years"):
                                for _, yr in yearly.iterrows():
                                    amt = yr["total_usd"]
                                    amt_str = f"${amt/1e6:,.0f}M" if amt and amt > 0 else "-"
                                    types_str = yr["equip_types"] if yr["equip_types"] else ""
                                    ramp_info = ""
                                    # Check if any backplane ramp matches this year
                                    for bp, ramp_str in d["ramp_by_bp"].items():
                                        if str(int(yr["po_year"])) in str(ramp_str):
                                            ramp_info = f" → MP {ramp_str}"
                                    st.markdown(
                                        f"**{int(yr['po_year'])}** &nbsp; {amt_str} &nbsp; "
                                        f"({yr['order_count']} orders){ramp_info}  \n"
                                        f"<span style='color:#86868B;font-size:0.8rem;'>{types_str}</span>",
                                        unsafe_allow_html=True,
                                    )

                                if d["total_investment"] > 0:
                                    st.markdown(
                                        f"---\n**Cumulative:** ${d['total_investment']/1e6:,.0f}M"
                                    )
                        else:
                            st.caption(f"{d['manufacturer']} {d['factory_name']}: No equipment order data")

                # ── Utilization Comparison Chart ──
                st.divider()
                st.markdown("#### Utilization Comparison")

                fig_util = go.Figure()
                for i, d in enumerate(compare_data):
                    util = d["util_df"]
                    if len(util) == 0:
                        continue
                    # Aggregate across backplanes per date
                    agg = util.groupby("date").agg(
                        capacity=("capacity_ksheets", "sum"),
                        input=("actual_input_ksheets", "sum"),
                    ).reset_index()
                    agg["util_pct"] = (agg["input"] / agg["capacity"] * 100).round(1)
                    # Only show dates with actual production
                    agg = agg[agg["input"] > 0]

                    fig_util.add_trace(go.Scatter(
                        x=agg["date"].tolist(),
                        y=agg["util_pct"].tolist(),
                        mode="lines+markers",
                        name=f"{d['manufacturer']} {d['factory_name']}",
                        line=dict(color=colors[i % len(colors)], width=2),
                        marker=dict(size=5),
                        hovertemplate=(
                            f"{d['manufacturer']} {d['factory_name']}<br>"
                            "%{x}<br>Utilization: %{y:.1f}%<extra></extra>"
                        ),
                    ))

                apply_chart_theme(fig_util)
                fig_util.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Utilization (%)",
                    height=400,
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                )
                st.plotly_chart(fig_util, use_container_width=True)

                # ── Capacity Comparison Chart ──
                st.markdown("#### Capacity Comparison")

                fig_cap = go.Figure()
                for i, d in enumerate(compare_data):
                    util = d["util_df"]
                    if len(util) == 0:
                        continue
                    agg = util.groupby("date").agg(
                        capacity=("capacity_ksheets", "sum"),
                    ).reset_index()
                    agg = agg[agg["capacity"] > 0]

                    fig_cap.add_trace(go.Scatter(
                        x=agg["date"].tolist(),
                        y=agg["capacity"].tolist(),
                        mode="lines",
                        name=f"{d['manufacturer']} {d['factory_name']}",
                        line=dict(color=colors[i % len(colors)], width=2),
                        hovertemplate=(
                            f"{d['manufacturer']} {d['factory_name']}<br>"
                            "%{x}<br>Capacity: %{y:,.1f}K/mo<extra></extra>"
                        ),
                    ))

                apply_chart_theme(fig_cap)
                fig_cap.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Capacity (K sheets/mo)",
                    height=350,
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                )
                st.plotly_chart(fig_cap, use_container_width=True)

                # ── Summary Comparison Table ──
                st.markdown("#### Summary Table")
                summary_rows = []
                for d in compare_data:
                    summary_rows.append({
                        "Factory": f"{d['manufacturer']} {d['factory_name']}",
                        "Location": f"{d['location']}, {d['region']}",
                        "Tech": d["technology"],
                        "Gen": d["generation"],
                        "Backplane": ", ".join(d["backplanes"]),
                        "Capacity (K/mo)": f"{d['capacity']:,.1f}",
                        "Utilization": f"{d['utilization']:.1f}%",
                        "First Ramp": d["earliest_ramp"],
                        "Depreciation": f"{d['dep_years']}yr",
                        "Total Investment": f"${d['total_investment']/1e6:,.0f}M" if d["total_investment"] > 0 else "-",
                        "Status": d["status"],
                    })
                st.dataframe(
                    pd.DataFrame(summary_rows),
                    use_container_width=True,
                    hide_index=True,
                )

