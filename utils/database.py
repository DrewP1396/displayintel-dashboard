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
        manufacturer: Optional[str] = None
    ) -> pd.DataFrame:
        """Get utilization data with optional filters."""
        query = """
            SELECT u.*, f.manufacturer, f.factory_name, f.technology, f.region
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
        if manufacturer and manufacturer != "All":
            query += " AND f.manufacturer = ?"
            params.append(manufacturer)

        query += " ORDER BY u.date, f.manufacturer"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_equipment_orders(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        manufacturer: Optional[str] = None,
        vendor: Optional[str] = None,
        equipment_type: Optional[str] = None
    ) -> pd.DataFrame:
        """Get equipment orders with optional filters."""
        query = "SELECT * FROM equipment_orders WHERE 1=1"
        params = []

        if start_date:
            query += " AND po_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND po_date <= ?"
            params.append(end_date)
        if manufacturer and manufacturer != "All":
            query += " AND manufacturer = ?"
            params.append(manufacturer)
        if vendor and vendor != "All":
            query += " AND vendor = ?"
            params.append(vendor)
        if equipment_type and equipment_type != "All":
            query += " AND equipment_type = ?"
            params.append(equipment_type)

        query += " ORDER BY po_date DESC"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_shipments(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        panel_maker: Optional[str] = None,
        technology: Optional[str] = None,
        application: Optional[str] = None
    ) -> pd.DataFrame:
        """Get shipment data with optional filters."""
        query = "SELECT * FROM shipments WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
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
            return pd.read_sql_query(query, conn, params=params)

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

            # Average utilization (latest quarter)
            cursor = conn.execute("""
                SELECT AVG(utilization_pct)
                FROM utilization
                WHERE date = (SELECT MAX(date) FROM utilization WHERE is_projection = 0)
            """)
            result = cursor.fetchone()[0]
            stats['avg_utilization'] = round(result, 1) if result else 0

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
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get equipment spending aggregated by vendor."""
        query = """
            SELECT
                vendor,
                SUM(amount_usd) as total_spend,
                SUM(units) as total_units,
                COUNT(*) as order_count
            FROM equipment_orders
            WHERE vendor IS NOT NULL
        """
        params = []

        if start_date:
            query += " AND po_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND po_date <= ?"
            params.append(end_date)

        query += " GROUP BY vendor ORDER BY total_spend DESC"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    @staticmethod
    @st.cache_data(ttl=300)
    def get_shipments_by_application(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
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

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " GROUP BY date, application ORDER BY date"

        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
