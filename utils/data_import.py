"""
Data import utilities for Display Intelligence Dashboard.
Imports utilization data from DSCC Excel reports.
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "displayintel.db"
SOURCE_DATA_PATH = Path(__file__).parent.parent / "source_data"


def import_utilization_data(
    file_path: Optional[str] = None,
    clear_existing: bool = False
):
    """
    Import utilization data from DSCC Excel file.

    The StaticDB sheet contains detailed data with:
    - Factory, Phase, Backplane, Frontplane info
    - Monthly capacity and actual input
    - Each row is a factory-phase-month combination

    We aggregate by Factory + Backplane to get total capacity per backplane technology.
    """
    if file_path is None:
        file_path = SOURCE_DATA_PATH / "2025Q4_Quarterly_All_Display_Fab_Utilization Report_RevA copy.xlsm"

    print(f"Reading from: {file_path}")

    # Read StaticDB sheet
    df = pd.read_excel(file_path, sheet_name='StaticDB', header=3)

    print(f"Total rows in source: {len(df)}")

    # Clean column names
    df.columns = [c.strip().replace('\n', ' ') for c in df.columns]

    # Rename columns for clarity
    column_map = {
        'Factory1': 'factory_name',
        'Factory2 (Location)': 'location',
        'Manufacturer': 'manufacturer',
        'Region': 'region',
        'Backplane': 'backplane',
        'Frontplane': 'technology',
        'TFT Gen1': 'generation',
        'Substrate': 'substrate',
        'Application Category': 'application_category',
        'Month': 'date',
        'Year': 'year',
        'Q': 'quarter',
        'Phase': 'phase',
        'Eqpt PO': 'eqpt_po_year',
        'Install': 'install_date',
        'MP Ramp': 'mp_ramp_date',
        'Probability': 'probability',
        'Capacity (k Sheet/Month)': 'capacity_ksheets',
        'Actual Input (k Sheet/Month)': 'actual_input_ksheets',
        'Areal Input Capacity (1,000 m2/Month)': 'capacity_sqm_k',
        'Areal Actual Input (1,000 m2/Month)': 'actual_input_sqm_k',
        'Utilization )%': 'utilization_pct'
    }

    df = df.rename(columns=column_map)

    # Filter out rows without required data
    df = df[df['manufacturer'].notna() & df['factory_name'].notna()]

    # Convert date to string format
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    # Extract month number
    df['month'] = pd.to_datetime(df['date']).dt.month

    # Create factory_id: manufacturer_factory_backplane
    df['factory_id'] = df.apply(
        lambda r: f"{r['manufacturer']}_{r['factory_name']}_{r['backplane']}"
        if pd.notna(r['backplane']) else f"{r['manufacturer']}_{r['factory_name']}",
        axis=1
    )

    # Aggregate by factory_id + date (sum across phases)
    agg_df = df.groupby(['factory_id', 'date', 'year', 'quarter', 'month']).agg({
        'manufacturer': 'first',
        'factory_name': 'first',
        'location': 'first',
        'region': 'first',
        'backplane': 'first',
        'technology': 'first',
        'generation': 'first',
        'substrate': 'first',
        'application_category': 'first',
        'eqpt_po_year': 'first',
        'install_date': 'first',
        'mp_ramp_date': 'first',
        'probability': 'first',
        'capacity_ksheets': 'sum',
        'actual_input_ksheets': 'sum',
        'capacity_sqm_k': 'sum',
        'actual_input_sqm_k': 'sum',
        'phase': 'count'  # Count of phases
    }).reset_index()

    agg_df = agg_df.rename(columns={'phase': 'phase_count'})

    # Calculate utilization percentage
    agg_df['utilization_pct'] = (agg_df['actual_input_ksheets'] / agg_df['capacity_ksheets'] * 100).fillna(0)

    print(f"Aggregated to {len(agg_df)} factory-backplane-date combinations")

    # Get unique factories for the factories table
    factories_df = agg_df.groupby('factory_id').agg({
        'manufacturer': 'first',
        'factory_name': 'first',
        'location': 'first',
        'region': 'first',
        'backplane': 'first',
        'technology': 'first',
        'generation': 'first',
        'substrate': 'first',
        'application_category': 'first',
        'eqpt_po_year': 'first',
        'install_date': 'first',
        'mp_ramp_date': 'first',
        'probability': 'first'
    }).reset_index()

    # Add status based on capacity
    latest_date = agg_df['date'].max()
    latest_capacity = agg_df[agg_df['date'] == latest_date].set_index('factory_id')['capacity_ksheets']
    factories_df['status'] = factories_df['factory_id'].apply(
        lambda x: 'operating' if x in latest_capacity.index and latest_capacity[x] > 0 else 'planned'
    )

    factories_df['created_at'] = datetime.now().isoformat()

    # Convert date columns to strings
    for col in ['install_date', 'mp_ramp_date', 'eqpt_po_year']:
        if col in factories_df.columns:
            factories_df[col] = factories_df[col].apply(
                lambda x: str(x) if pd.notna(x) else None
            )

    print(f"Unique factories: {len(factories_df)}")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    if clear_existing:
        print("Clearing existing data...")
        conn.execute("DELETE FROM utilization")
        conn.execute("DELETE FROM factories")
        conn.commit()

    # Prepare utilization data
    util_cols = [
        'factory_id', 'date', 'year', 'quarter', 'month',
        'utilization_pct', 'capacity_ksheets', 'actual_input_ksheets',
        'capacity_sqm_k', 'actual_input_sqm_k'
    ]

    util_df = agg_df[util_cols].copy()
    util_df['data_source'] = str(file_path.name) if hasattr(file_path, 'name') else str(file_path).split('/')[-1]
    util_df['created_at'] = datetime.now().isoformat()
    util_df['is_projection'] = 0

    # Insert/update factories
    print("Updating factories table...")
    for _, row in factories_df.iterrows():
        conn.execute("""
            INSERT OR REPLACE INTO factories
            (factory_id, manufacturer, factory_name, location, region, technology,
             backplane, generation, substrate, application_category,
             eqpt_po_year, install_date, mp_ramp_date, probability, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['factory_id'], row['manufacturer'], row['factory_name'],
            row['location'], row['region'], row['technology'],
            row['backplane'], row['generation'], row['substrate'],
            row['application_category'], row['eqpt_po_year'],
            row['install_date'], row['mp_ramp_date'], row['probability'],
            row['status'], row['created_at']
        ))

    # Insert utilization data
    print("Updating utilization table...")
    for _, row in util_df.iterrows():
        conn.execute("""
            INSERT OR REPLACE INTO utilization
            (factory_id, date, year, quarter, month, utilization_pct,
             capacity_ksheets, actual_input_ksheets, capacity_sqm_k,
             actual_input_sqm_k, data_source, created_at, is_projection)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['factory_id'], row['date'], row['year'], row['quarter'],
            row['month'], row['utilization_pct'], row['capacity_ksheets'],
            row['actual_input_ksheets'], row['capacity_sqm_k'],
            row['actual_input_sqm_k'], row['data_source'],
            row['created_at'], row['is_projection']
        ))

    conn.commit()
    conn.close()

    print("Import complete!")

    # Print summary
    print("\n=== Import Summary ===")
    print(f"Factories imported: {len(factories_df)}")
    print(f"Utilization records: {len(util_df)}")

    # Show sample of A3 data
    a3_data = agg_df[(agg_df['factory_name'] == 'A3') & (agg_df['date'] == latest_date)]
    if len(a3_data) > 0:
        print("\n=== A3 Capacity (latest month) ===")
        for _, row in a3_data.iterrows():
            print(f"  {row['backplane']}: {row['capacity_ksheets']:.1f}K/mo ({row['phase_count']} phases)")
        print(f"  Total: {a3_data['capacity_ksheets'].sum():.1f}K/mo")


if __name__ == "__main__":
    import_utilization_data(clear_existing=True)
