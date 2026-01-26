"""
Export functionality for Display Intelligence Dashboard
"""

import io
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def export_to_csv(df: pd.DataFrame, filename: str = "export") -> bytes:
    """Export DataFrame to CSV bytes."""
    return df.to_csv(index=False).encode('utf-8')


def export_to_pdf(
    df: pd.DataFrame,
    title: str = "Display Intelligence Report",
    filename: str = "report"
) -> bytes:
    """Export DataFrame to PDF bytes."""
    buffer = io.BytesIO()

    # Create document with landscape orientation for wide tables
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.5*inch
    )

    elements = []
    styles = getSampleStyleSheet()

    # Custom title style (Apple-like)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1D1D1F'),
        fontName='Helvetica-Bold'
    )

    # Subtitle style
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#86868B')
    )

    # Add title
    elements.append(Paragraph(title, title_style))

    # Add generation timestamp
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    elements.append(Paragraph(f"Generated on {timestamp}", subtitle_style))

    # Prepare table data
    if len(df) > 0:
        # Limit columns for readability
        display_cols = df.columns[:10]  # Max 10 columns
        df_display = df[display_cols].head(100)  # Max 100 rows

        # Format column headers
        headers = [str(col).replace('_', ' ').title() for col in display_cols]

        # Format data
        data = [headers]
        for _, row in df_display.iterrows():
            row_data = []
            for val in row:
                if pd.isna(val):
                    row_data.append('')
                elif isinstance(val, float):
                    row_data.append(f'{val:,.2f}')
                else:
                    # Truncate long strings
                    str_val = str(val)
                    row_data.append(str_val[:30] + '...' if len(str_val) > 30 else str_val)
            data.append(row_data)

        # Calculate column widths
        available_width = landscape(letter)[0] - 1*inch
        col_width = available_width / len(display_cols)

        # Create table
        table = Table(data, colWidths=[col_width] * len(display_cols))

        # Apple-inspired table style
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1D1D1F')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),

            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1D1D1F')),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),

            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5E7')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#007AFF')),

            # Alignment
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)

        # Add record count note
        if len(df) > 100:
            note_style = ParagraphStyle(
                'Note',
                parent=styles['Normal'],
                fontSize=8,
                spaceBefore=15,
                alignment=TA_LEFT,
                textColor=colors.HexColor('#86868B')
            )
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f"Showing 100 of {len(df):,} records. Export to CSV for complete data.",
                note_style
            ))
    else:
        no_data_style = ParagraphStyle(
            'NoData',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#86868B')
        )
        elements.append(Spacer(1, 50))
        elements.append(Paragraph("No data available for the selected filters.", no_data_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def create_download_buttons(df: pd.DataFrame, key_prefix: str, title: str = "Data"):
    """Create download buttons for CSV and PDF exports."""
    import streamlit as st
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    col1, col2 = st.columns(2)

    with col1:
        csv_data = export_to_csv(df)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"{key_prefix}_{timestamp}.csv",
            mime="text/csv",
            key=f"{key_prefix}_csv",
            use_container_width=True
        )

    with col2:
        pdf_data = export_to_pdf(df, title=title)
        st.download_button(
            label="Download PDF",
            data=pdf_data,
            file_name=f"{key_prefix}_{timestamp}.pdf",
            mime="application/pdf",
            key=f"{key_prefix}_pdf",
            use_container_width=True
        )
