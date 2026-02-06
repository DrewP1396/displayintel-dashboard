"""
Apple-inspired styling for Display Intelligence Dashboard
"""


def get_css() -> str:
    """Return custom CSS for Apple-like design."""
    return """
    <style>
        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global styles */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        /* Main container */
        .main .block-container {
            padding: 2rem 3rem;
            max-width: 1400px;
        }

        /* Headers */
        h1, h2, h3 {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 600;
            color: #1D1D1F;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            margin-bottom: 0.5rem !important;
        }

        h2 {
            font-size: 1.75rem !important;
            margin-top: 2rem !important;
        }

        h3 {
            font-size: 1.25rem !important;
            color: #1D1D1F !important;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F5F7 100%);
            border: 1px solid #E5E5E7;
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            color: #86868B !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: #1D1D1F !important;
        }

        [data-testid="stMetricDelta"] {
            font-size: 0.875rem !important;
            font-weight: 500 !important;
        }

        /* Buttons */
        .stButton > button {
            background: #007AFF;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.625rem 1.25rem;
            font-weight: 500;
            font-size: 0.9375rem;
            transition: all 0.2s ease;
            font-family: 'Inter', sans-serif;
        }

        .stButton > button:hover {
            background: #0056CC;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,122,255,0.3);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Download buttons */
        .stDownloadButton > button {
            background: #F5F5F7;
            color: #1D1D1F;
            border: 1px solid #E5E5E7;
            border-radius: 12px;
            padding: 0.625rem 1.25rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .stDownloadButton > button:hover {
            background: #E5E5E7;
            border-color: #D1D1D6;
        }

        /* Selectbox and inputs */
        .stSelectbox > div > div {
            border-radius: 12px !important;
            border-color: #E5E5E7 !important;
            background: #FFFFFF;
        }

        .stSelectbox > div > div:focus-within {
            border-color: #007AFF !important;
            box-shadow: 0 0 0 3px rgba(0,122,255,0.15) !important;
        }

        .stTextInput > div > div > input {
            border-radius: 12px !important;
            border-color: #E5E5E7 !important;
            padding: 0.75rem 1rem;
        }

        .stTextInput > div > div > input:focus {
            border-color: #007AFF !important;
            box-shadow: 0 0 0 3px rgba(0,122,255,0.15) !important;
        }

        /* Date input */
        .stDateInput > div > div > input {
            border-radius: 12px !important;
            border-color: #E5E5E7 !important;
        }

        /* Multiselect */
        .stMultiSelect > div > div {
            border-radius: 12px !important;
            border-color: #E5E5E7 !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background: #F5F5F7;
            border-radius: 12px;
            padding: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            color: #86868B;
            background: transparent;
            border: none;
            transition: all 0.2s ease;
        }

        .stTabs [aria-selected="true"] {
            background: #FFFFFF !important;
            color: #1D1D1F !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #1D1D1F;
        }

        /* DataFrames */
        .stDataFrame {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid #E5E5E7;
        }

        [data-testid="stDataFrame"] > div {
            border-radius: 16px;
        }

        /* Center-align all table/dataframe cells and headers */
        [data-testid="stDataFrame"] td,
        [data-testid="stDataFrame"] th,
        [data-testid="stTable"] td,
        [data-testid="stTable"] th,
        .stDataFrame td,
        .stDataFrame th {
            text-align: center !important;
        }

        /* glide-data-grid header cells */
        [data-testid="stDataFrame"] [role="columnheader"],
        [data-testid="stDataFrame"] .gdg-header-cell {
            text-align: center !important;
            justify-content: center !important;
        }

        /* Better table header styling */
        [data-testid="stDataFrame"] th,
        [data-testid="stTable"] th {
            background: #F5F5F7 !important;
            font-weight: 600 !important;
            color: #1D1D1F !important;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background: #F5F5F7;
            border-radius: 12px;
            font-weight: 500;
            color: #1D1D1F;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #F5F5F7;
            border-right: 1px solid #E5E5E7;
        }

        /* Capitalize sidebar nav page labels (fixes lowercase "dashboard") */
        [data-testid="stSidebarNav"] a span {
            text-transform: capitalize;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
            font-size: 1.5rem !important;
            padding: 1rem 0;
        }

        /* Divider */
        hr {
            border: none;
            height: 1px;
            background: #E5E5E7;
            margin: 2rem 0;
        }

        /* Plotly charts container */
        .js-plotly-plot {
            border-radius: 16px;
            overflow: hidden;
        }

        /* Hide Plotly modebar (camera/screenshot icon) */
        .modebar {
            display: none !important;
        }

        /* Info/Warning/Error boxes */
        .stAlert {
            border-radius: 12px;
            border: none;
        }

        /* Success message */
        .stSuccess {
            background: #E8F5E9;
            color: #1B5E20;
        }

        /* Warning message */
        .stWarning {
            background: #FFF3E0;
            color: #E65100;
        }

        /* Error message */
        .stError {
            background: #FFEBEE;
            color: #C62828;
        }

        /* Info message */
        .stInfo {
            background: #E3F2FD;
            color: #1565C0;
        }

        /* Progress bar */
        .stProgress > div > div {
            background: #007AFF;
            border-radius: 8px;
        }

        /* Spinner */
        .stSpinner > div {
            border-color: #007AFF transparent transparent transparent;
        }

        /* Custom card class */
        .metric-card {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F5F7 100%);
            border: 1px solid #E5E5E7;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem;
            }

            h1 {
                font-size: 1.75rem !important;
            }

            [data-testid="stMetricValue"] {
                font-size: 1.5rem !important;
            }

            .stTabs [data-baseweb="tab"] {
                padding: 0.5rem 0.75rem;
                font-size: 0.875rem;
            }
        }

        /* Login page specific */
        .login-container {
            max-width: 400px;
            margin: 4rem auto;
            padding: 2rem;
            background: white;
            border-radius: 20px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        }

        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .login-logo {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
    </style>
    """


def get_plotly_theme() -> dict:
    """Return Plotly theme configuration for Apple-like charts."""
    return {
        'template': 'plotly_white',
        'color_discrete_sequence': [
            '#007AFF',  # Blue
            '#34C759',  # Green
            '#FF9500',  # Orange
            '#FF3B30',  # Red
            '#5856D6',  # Purple
            '#AF52DE',  # Violet
            '#00C7BE',  # Teal
            '#FF2D55',  # Pink
            '#5AC8FA',  # Light Blue
            '#FFCC00',  # Yellow
        ],
        # Simplified layout - apply these directly, don't use with **spread
        'font_family': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        'font_color': '#1D1D1F',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'margin': {'t': 60, 'b': 40, 'l': 60, 'r': 40},
        'gridcolor': '#E5E5E7',
        'tickfont_color': '#86868B',
        'hoverlabel': {
            'bgcolor': '#1D1D1F',
            'font': {'color': 'white', 'size': 12},
            'bordercolor': '#1D1D1F'
        }
    }


def apply_chart_theme(fig, theme=None):
    """Apply Apple-like theme to a Plotly figure safely."""
    if theme is None:
        theme = get_plotly_theme()

    fig.update_layout(
        font=dict(
            family=theme['font_family'],
            color=theme['font_color'],
            size=12
        ),
        paper_bgcolor=theme['paper_bgcolor'],
        plot_bgcolor=theme['plot_bgcolor'],
        margin=theme['margin'],
        hoverlabel=theme['hoverlabel']
    )

    # Update axes styling
    fig.update_xaxes(
        gridcolor=theme['gridcolor'],
        linecolor=theme['gridcolor'],
        tickfont=dict(size=11, color=theme['tickfont_color'])
    )
    fig.update_yaxes(
        gridcolor=theme['gridcolor'],
        linecolor=theme['gridcolor'],
        tickfont=dict(size=11, color=theme['tickfont_color'])
    )

    return fig


def apply_plotly_theme(fig):
    """Apply Apple-like theme to a Plotly figure (legacy wrapper)."""
    return apply_chart_theme(fig)


def format_number(value, decimals: int = 1, prefix: str = '', suffix: str = '') -> str:
    """Format a number with proper thousand separators and abbreviations."""
    if value is None:
        return 'N/A'
    try:
        value = float(value)
    except (ValueError, TypeError):
        return 'N/A'

    if abs(value) >= 1_000_000_000:
        return f"{prefix}{value/1_000_000_000:,.{decimals}f}B{suffix}"
    elif abs(value) >= 1_000_000:
        return f"{prefix}{value/1_000_000:,.{decimals}f}M{suffix}"
    elif abs(value) >= 1_000:
        return f"{prefix}{value/1_000:,.{decimals}f}K{suffix}"
    else:
        return f"{prefix}{value:,.{decimals}f}{suffix}"


def format_currency(value, decimals: int = 1) -> str:
    """Format a number as currency with $ prefix."""
    return format_number(value, decimals=decimals, prefix='$')


def format_percent(value, decimals: int = 1) -> str:
    """Format a number as percentage."""
    if value is None:
        return 'N/A'
    try:
        return f"{float(value):,.{decimals}f}%"
    except (ValueError, TypeError):
        return 'N/A'


def format_with_commas(value, decimals: int = 0) -> str:
    """Format a number with commas for thousands."""
    if value is None:
        return 'N/A'
    try:
        if decimals == 0:
            return f"{int(value):,}"
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return 'N/A'
