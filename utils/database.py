"""
Database query functions for Display Intelligence Dashboard
"""

import sqlite3
import pandas as pd
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Tuple
import streamlit as st

DB_PATH = Path(__file__).parent.parent / "displayintel.db"


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class DatabaseManager:
    """Manages all database queries for the dashboard."""

    @staticmethod
    @st.cache_data(ttl=300)
    def get_factories(
        manufacturer: Optional[str] = None,
        technology: Optional[str] = None,
        region: Optional[str] = None,
        status: Optional[str] = None
    ) -> pd.DataFrame:
        """Get factories with optional filters."""
        query = "SELECT * FROM factories WHERE 1=1"
        params = []

        if manufacturer and manufacturer != "All":
            query += " AND manufacturer = ?"
            params.append(manufacturer)
        if technology and technology != "All":
            query += " AND technology = ?"
            params.append(technology)
        if region and region != "All":
            query += " AND region = ?"
            params.append(region)
        if status and status != "All":
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY manufacturer, factory_name"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_utilization(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        factory_id: Optional[str] = None,
        factory_name: Optional[str] = None,
        manufacturer: Optional[str] = None
    ) -> pd.DataFrame:
        """Get utilization data with optional filters."""
        query = """
            SELECT u.*, f.manufacturer, f.factory_name, f.technology, f.region, f.backplane
            FROM utilization u
            JOIN factories f ON u.factory_id = f.factory_id
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND u.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND u.date <= ?"
            params.append(end_date)
        if factory_id:
            query += " AND u.factory_id = ?"
            params.append(factory_id)
        if factory_name:
            query += " AND f.factory_name = ?"
            params.append(factory_name)
        if manufacturer and manufacturer != "All":
            query += " AND f.manufacturer = ?"
            params.append(manufacturer)

        query += " ORDER BY u.date, f.manufacturer, f.backplane"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_equipment_orders(
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        manufacturer: Optional[str] = None,
        vendor: Optional[str] = None,
        equipment_type: Optional[str] = None
    ) -> pd.DataFrame:
        """Get equipment orders with optional filters.

        Uses po_year for date filtering since po_date is often NULL.
        """
        query = "SELECT * FROM equipment_orders WHERE po_year IS NOT NULL"
        params = []

        if start_year:
            query += " AND po_year >= ?"
            params.append(start_year)
        if end_year:
            query += " AND po_year <= ?"
            params.append(end_year)
        if manufacturer and manufacturer != "All":
            query += " AND manufacturer = ?"
            params.append(manufacturer)
        if vendor and vendor != "All":
            query += " AND vendor = ?"
            params.append(vendor)
        if equipment_type and equipment_type != "All":
            query += " AND equipment_type = ?"
            params.append(equipment_type)

        query += " ORDER BY po_year DESC, po_quarter DESC"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_shipments(
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        panel_maker: Optional[str] = None,
        technology: Optional[str] = None,
        application: Optional[str] = None
    ) -> pd.DataFrame:
        """Get shipment data with optional filters.

        Note: date column contains period strings like '2016-Q1 2016' not actual dates.
        Filtering is done by extracting the year from the date string.
        """
        query = "SELECT * FROM shipments WHERE 1=1"
        params = []

        # Filter by year extracted from date string (first 4 chars)
        if start_year:
            query += " AND CAST(SUBSTR(date, 1, 4) AS INTEGER) >= ?"
            params.append(start_year)
        if end_year:
            query += " AND CAST(SUBSTR(date, 1, 4) AS INTEGER) <= ?"
            params.append(end_year)
        if panel_maker and panel_maker != "All":
            query += " AND panel_maker = ?"
            params.append(panel_maker)
        if technology and technology != "All":
            query += " AND technology = ?"
            params.append(technology)
        if application and application != "All":
            query += " AND application = ?"
            params.append(application)

        query += " ORDER BY date DESC"

        with get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)

        # Deduplicate: source data contains identical rows from import
        dedup_cols = ['date', 'panel_maker', 'brand', 'model', 'size_inches',
                      'technology', 'application', 'units_k', 'revenue_m']
        before = len(df)
        df = df.drop_duplicates(subset=dedup_cols)
        if before != len(df):
            print(f"[data-quality] shipments: dropped {before - len(df):,} "
                  f"duplicate rows ({before:,} → {len(df):,})")
        return df

    @staticmethod
    @st.cache_data(ttl=300)
    def get_financials(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        manufacturer: Optional[str] = None
    ) -> pd.DataFrame:
        """Get financial data with optional filters."""
        query = "SELECT * FROM financials WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if manufacturer and manufacturer != "All":
            query += " AND manufacturer = ?"
            params.append(manufacturer)

        query += " ORDER BY date DESC, manufacturer"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_news(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        impact_level: Optional[str] = None
    ) -> pd.DataFrame:
        """Get news articles with optional filters."""
        query = "SELECT * FROM news WHERE 1=1"
        params = []

        if start_date:
            query += " AND published_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND published_date <= ?"
            params.append(end_date)
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        if impact_level and impact_level != "All":
            query += " AND impact_level = ?"
            params.append(impact_level)

        query += " ORDER BY published_date DESC"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_insights(
        insight_type: Optional[str] = None,
        topic: Optional[str] = None
    ) -> pd.DataFrame:
        """Get insights with optional filters."""
        query = "SELECT * FROM insights WHERE 1=1"
        params = []

        if insight_type and insight_type != "All":
            query += " AND insight_type = ?"
            params.append(insight_type)
        if topic and topic != "All":
            query += " AND topic = ?"
            params.append(topic)

        query += " ORDER BY relevance_score DESC"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    # Filter options getters
    @staticmethod
    @st.cache_data(ttl=600)
    def get_manufacturers() -> List[str]:
        """Get list of unique manufacturers."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT manufacturer FROM factories ORDER BY manufacturer"
            )
            return ["All"] + [row[0] for row in cursor.fetchall() if row[0]]

    @staticmethod
    @st.cache_data(ttl=600)
    def get_technologies() -> List[str]:
        """Get list of unique technologies."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT technology FROM factories WHERE technology IS NOT NULL ORDER BY technology"
            )
            return ["All"] + [row[0] for row in cursor.fetchall() if row[0]]

    @staticmethod
    @st.cache_data(ttl=600)
    def get_regions() -> List[str]:
        """Get list of unique regions."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT region FROM factories WHERE region IS NOT NULL ORDER BY region"
            )
            return ["All"] + [row[0] for row in cursor.fetchall() if row[0]]

    @staticmethod
    @st.cache_data(ttl=600)
    def get_vendors() -> List[str]:
        """Get list of unique equipment vendors."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT vendor FROM equipment_orders WHERE vendor IS NOT NULL ORDER BY vendor"
            )
            return ["All"] + [row[0] for row in cursor.fetchall() if row[0]]

    @staticmethod
    @st.cache_data(ttl=600)
    def get_equipment_types() -> List[str]:
        """Get list of unique equipment types."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT equipment_type FROM equipment_orders WHERE equipment_type IS NOT NULL ORDER BY equipment_type"
            )
            return ["All"] + [row[0] for row in cursor.fetchall() if row[0]]

    @staticmethod
    @st.cache_data(ttl=600)
    def get_applications() -> List[str]:
        """Get list of unique applications."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT application FROM shipments WHERE application IS NOT NULL ORDER BY application"
            )
            return ["All"] + [row[0] for row in cursor.fetchall() if row[0]]

    @staticmethod
    @st.cache_data(ttl=600)
    def get_panel_makers() -> List[str]:
        """Get list of unique panel makers from shipments."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT panel_maker FROM shipments WHERE panel_maker IS NOT NULL ORDER BY panel_maker"
            )
            return ["All"] + [row[0] for row in cursor.fetchall() if row[0]]

    @staticmethod
    @st.cache_data(ttl=600)
    def get_date_range() -> Tuple[str, str]:
        """Get the date range available in utilization data."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT MIN(date), MAX(date) FROM utilization"
            )
            row = cursor.fetchone()
            return (row[0] or "2019-01-01", row[1] or "2026-12-31")

    @staticmethod
    @st.cache_data(ttl=600)
    def get_factory_names(manufacturer: Optional[str] = None) -> List[str]:
        """Get list of unique factory names optionally filtered by manufacturer."""
        query = """
            SELECT DISTINCT factory_name FROM factories
            WHERE factory_name IS NOT NULL
        """
        params = []
        if manufacturer and manufacturer != "All":
            query += " AND manufacturer = ?"
            params.append(manufacturer)
        query += " ORDER BY factory_name"

        with get_connection() as conn:
            cursor = conn.execute(query, params)
            # Get unique factory names (since we now have multiple entries per factory for different backplanes)
            names = sorted(set([row[0] for row in cursor.fetchall() if row[0]]))
            return ["All Factories"] + names

    @staticmethod
    @st.cache_data(ttl=300)
    def get_factory_by_name(factory_name: str) -> Optional[pd.DataFrame]:
        """Get all factory entries by name (may have multiple backplane variants)."""
        query = "SELECT * FROM factories WHERE factory_name = ? ORDER BY backplane"
        with get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[factory_name])
            return df if len(df) > 0 else None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_factory_ramp_date(factory_id: str) -> Optional[str]:
        """Get the first ramp date for a factory (first month with utilization > 0)."""
        query = """
            SELECT MIN(date) as ramp_date
            FROM utilization
            WHERE factory_id = ? AND utilization_pct > 0
        """
        with get_connection() as conn:
            cursor = conn.execute(query, [factory_id])
            row = cursor.fetchone()
            return row[0] if row and row[0] else None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_equipment_orders_for_factory(factory_id: str) -> pd.DataFrame:
        """Get equipment orders for a specific factory.

        Handles both old format (SDC_A3) and new format (SDC_A3_LTPO).
        """
        # Try exact match first, then try base factory_id (without backplane suffix)
        base_factory_id = '_'.join(factory_id.split('_')[:2]) if factory_id.count('_') >= 2 else factory_id

        query = """
            SELECT * FROM equipment_orders
            WHERE factory_id = ? OR factory_id = ?
            ORDER BY po_year DESC, po_quarter DESC
        """
        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=[factory_id, base_factory_id])

    @staticmethod
    @st.cache_data(ttl=300)
    def get_all_factory_ramp_dates() -> dict:
        """Get ramp dates for all factories."""
        query = """
            SELECT factory_id, MIN(date) as ramp_date
            FROM utilization
            WHERE utilization_pct > 0
            GROUP BY factory_id
        """
        with get_connection() as conn:
            cursor = conn.execute(query)
            return {row[0]: row[1] for row in cursor.fetchall()}

    @staticmethod
    @st.cache_data(ttl=300)
    def get_capacity_by_backplane(
        manufacturer: Optional[str] = None,
        factory_name: Optional[str] = None,
        date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get capacity breakdown by backplane technology.

        If factory_name provided, gets capacity for that factory and related lines.
        Otherwise gets total capacity by backplane for manufacturer or all.
        """
        # Use latest date with actual input data if not specified
        date_clause = "u.date = (SELECT MAX(date) FROM utilization WHERE is_projection = 0 AND actual_input_ksheets > 0)"
        if date:
            date_clause = "u.date = ?"

        query = f"""
            SELECT
                f.manufacturer,
                f.factory_name,
                f.backplane,
                f.technology,
                f.generation,
                u.capacity_ksheets,
                u.actual_input_ksheets,
                u.utilization_pct,
                u.date
            FROM factories f
            JOIN utilization u ON f.factory_id = u.factory_id
            WHERE {date_clause}
        """
        params = []
        if date:
            params.append(date)

        if manufacturer and manufacturer != "All":
            query += " AND f.manufacturer = ?"
            params.append(manufacturer)

        if factory_name:
            # Get the base factory name (e.g., "A3" from "A3" or "A4" from "A4 (L7-1)")
            base_name = factory_name.split('(')[0].strip().split('_')[0].strip()
            query += " AND (f.factory_name = ? OR f.factory_name LIKE ?)"
            params.append(factory_name)
            params.append(f"{base_name}%")

        query += " ORDER BY f.manufacturer, f.factory_name, f.backplane"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_total_capacity_by_backplane(date: Optional[str] = None) -> pd.DataFrame:
        """Get total industry capacity grouped by backplane technology."""
        date_clause = "u.date = (SELECT MAX(date) FROM utilization WHERE is_projection = 0 AND actual_input_ksheets > 0)"
        params = []
        if date:
            date_clause = "u.date = ?"
            params.append(date)

        query = f"""
            SELECT
                f.backplane,
                f.technology,
                SUM(u.capacity_ksheets) as total_capacity_k,
                SUM(u.actual_input_ksheets) as total_input_k,
                AVG(u.utilization_pct) as avg_utilization,
                COUNT(DISTINCT f.factory_id) as num_factories
            FROM factories f
            JOIN utilization u ON f.factory_id = u.factory_id
            WHERE {date_clause}
            AND f.backplane IS NOT NULL
            GROUP BY f.backplane, f.technology
            ORDER BY total_capacity_k DESC
        """

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    # Summary statistics
    @staticmethod
    @st.cache_data(ttl=300)
    def get_summary_stats() -> dict:
        """Get summary statistics for the dashboard."""
        with get_connection() as conn:
            stats = {}

            # Factory count
            cursor = conn.execute("SELECT COUNT(*) FROM factories")
            stats['total_factories'] = cursor.fetchone()[0]

            # Active factories
            cursor = conn.execute("SELECT COUNT(*) FROM factories WHERE status = 'operating'")
            stats['active_factories'] = cursor.fetchone()[0]

            # Total records
            cursor = conn.execute("SELECT COUNT(*) FROM utilization")
            stats['utilization_records'] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM equipment_orders")
            stats['equipment_orders'] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM shipments")
            stats['shipments'] = cursor.fetchone()[0]

            # Average utilization — use latest month that has real production
            # (future capacity-only rows have actual_input=0 and util=0)
            cursor = conn.execute("""
                SELECT AVG(u.utilization_pct)
                FROM utilization u
                WHERE u.actual_input_ksheets > 0
                  AND u.date = (
                      SELECT MAX(u2.date) FROM utilization u2
                      WHERE u2.actual_input_ksheets > 0
                  )
            """)
            result = cursor.fetchone()[0]
            stats['avg_utilization'] = round(float(result), 1) if result is not None else 0
            print(f"[dashboard] avg_utilization = {stats['avg_utilization']}%")

            # Unique manufacturers
            cursor = conn.execute("SELECT COUNT(DISTINCT manufacturer) FROM factories")
            stats['manufacturers'] = cursor.fetchone()[0]

            return stats

    @staticmethod
    @st.cache_data(ttl=300)
    def get_utilization_by_manufacturer(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get aggregated utilization by manufacturer over time."""
        query = """
            SELECT
                u.date,
                f.manufacturer,
                AVG(u.utilization_pct) as avg_utilization,
                SUM(u.capacity_ksheets) as total_capacity,
                SUM(u.actual_input_ksheets) as total_input
            FROM utilization u
            JOIN factories f ON u.factory_id = f.factory_id
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND u.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND u.date <= ?"
            params.append(end_date)

        query += " GROUP BY u.date, f.manufacturer ORDER BY u.date, f.manufacturer"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_equipment_spend_by_vendor(
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> pd.DataFrame:
        """Get equipment spending aggregated by vendor."""
        query = """
            SELECT
                vendor,
                SUM(amount_usd) as total_spend,
                SUM(units) as total_units,
                COUNT(*) as order_count
            FROM equipment_orders
            WHERE vendor IS NOT NULL AND po_year IS NOT NULL
        """
        params = []

        if start_year:
            query += " AND po_year >= ?"
            params.append(start_year)
        if end_year:
            query += " AND po_year <= ?"
            params.append(end_year)

        query += " GROUP BY vendor ORDER BY total_spend DESC"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_shipments_by_application(
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> pd.DataFrame:
        """Get shipments aggregated by application."""
        query = """
            SELECT
                date,
                application,
                SUM(units_k) as total_units_k,
                SUM(revenue_m) as total_revenue_m
            FROM shipments
            WHERE application IS NOT NULL
        """
        params = []

        if start_year:
            query += " AND CAST(SUBSTR(date, 1, 4) AS INTEGER) >= ?"
            params.append(start_year)
        if end_year:
            query += " AND CAST(SUBSTR(date, 1, 4) AS INTEGER) <= ?"
            params.append(end_year)

        query += " GROUP BY date, application ORDER BY date"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)


# =============================================================================
# Formatting Functions
# =============================================================================

def format_currency(value):
    """Format currency with $ and M/B suffix."""
    if pd.isna(value) or value == 0:
        return "$0"
    if value >= 1e9:
        return f"${value/1e9:.1f}B"
    elif value >= 1e6:
        return f"${value/1e6:.1f}M"
    elif value >= 1e3:
        return f"${value/1e3:.1f}K"
    else:
        return f"${value:.0f}"


def format_integer(value):
    """Format integer with commas."""
    if pd.isna(value):
        return "-"
    return f"{int(value):,}"


def format_units(value):
    """Format units (show - for null/zero)."""
    if pd.isna(value) or value == 0:
        return "-"
    return format_integer(value)


def format_percent(value):
    """Format as percentage."""
    if pd.isna(value):
        return "-"
    return f"{value:.1f}%"


# Process step mapping for OLED fab equipment
PROCESS_STEP_MAPPING = {
    # Step 1: Substrate/Glass
    'AKT': 1, 'Glass': 1, 'Cleaning': 1,
    'Glass Half Cut': 1, 'LLO': 1, 'Laser Cell Cutting': 1,
    'Laser Shape Cutting': 1, 'Scriber': 1, 'Wet Clean': 1,
    # Step 2: Backplane/TFT
    'CVD': 2, 'Sputtering': 2, 'PVD': 2, 'Etch': 2, 'Dry Etch': 2,
    'Exposure': 2, 'Developer': 2, 'Photolithography': 2, 'Implant': 2,
    'Coater': 2, 'Coater Developer': 2, 'Dry Strip': 2, 'ELA': 2,
    'Furnace Activation Annealing': 2, 'ITO Furnace': 2, 'Laser CVD Repair': 2,
    'Laser Drilling': 2, 'PI Coating': 2, 'PI Curing': 2,
    'PVD ITO IGZO': 2, 'PVD SD Gate LS': 2, 'Wet Etch': 2, 'Wet Strip': 2,
    # Step 3: Planarization
    'CMP': 3, 'Planarization': 3,
    # Step 4: OLED Deposition
    'Evaporation': 4, 'OLED': 4, 'RGB': 4, 'Organic': 4,
    'Evap RandD': 4, 'FMM VTE Source': 4, 'FMM VTE System': 4, 'IJP': 4,
    'Open Mask VTE': 4, 'Open Mask VTE Source': 4, 'Other IJP': 4,
    'Photo Patterned VTE': 4, 'Photo Patterned VTE Source': 4, 'Vacuum Alignment': 4,
    # Step 5: Encapsulation
    'Encapsulation': 5, 'Encap': 5, 'TFE': 5, 'Getter': 5,
    'ALD TFE': 5, 'Fill Dispense': 5, 'Glass Metal Encapsulation': 5,
    'Inorganic TFE': 5, 'Organic TFE': 5,
    # Step 6: Module Assembly
    'Module': 6, 'Bonding': 6, 'Touch': 6, 'Polarizer': 6,
    'COF COP COG Bonding': 6, 'Cell Module Repair': 6,
    'FOF FOG PCB Bonding': 6, 'Lamination Attach': 6,
    # Step 7: Test/Inspection
    'AOI': 7, 'Test': 7, 'Inspection': 7,
    'Array Test': 7, 'Auto Cell Aging Test': 7, 'Auto Final Test': 7,
    'Auto Module Test': 7, 'CD Overlay': 7, 'Film Thickness': 7,
    'Film Thickness Cluster': 7, 'Film Thickness Stand Alone': 7,
    'Multi Time Program': 7, 'OS Tester': 7, 'SEM': 7, 'SLA': 7,
    'Total Pitch': 7, 'Zap Repair': 7,
    # Step 8: Automation/Other
    'Automation': 8, 'Material Handling': 8, 'Others': 8,
    'Bubble PI Repair': 8
}

PROCESS_STEP_NAMES = {
    1: 'Substrate/Glass',
    2: 'Backplane/TFT',
    3: 'Planarization',
    4: 'OLED Deposition',
    5: 'Encapsulation',
    6: 'Module Assembly',
    7: 'Test/Inspection',
    8: 'Automation/Other'
}


def get_process_step(equipment_type):
    """Get process step number for equipment type."""
    if not equipment_type:
        return 8
    return PROCESS_STEP_MAPPING.get(equipment_type, 8)


def get_process_step_name(equipment_type):
    """Get process step name for equipment type."""
    step_num = get_process_step(equipment_type)
    return PROCESS_STEP_NAMES.get(step_num, 'Automation/Other')
