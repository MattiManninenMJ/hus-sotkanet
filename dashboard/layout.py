"""Dashboard layout components."""

from dash import dcc, html
from typing import Dict, List, Optional, Any


class DashboardLayout:
    """Manages dashboard layout components."""
    
    @staticmethod
    def create_header() -> html.Div:
        """Create dashboard header."""
        return html.Div([
            html.H1("HUS Sotkanet Health Dashboard", id="dashboard-title"),
            html.P(
                "Healthcare and Social Indicators for Hospital District of Helsinki and Uusimaa",
                id="dashboard-subtitle"
            ),
            html.Hr()
        ], id="header")
    
    @staticmethod
    def create_indicator_selector(options: List[Dict[str, Any]]) -> html.Div:
        """
        Create indicator selection dropdown.
        
        Args:
            options: List of dropdown options
        """
        return html.Div([
            html.Label("Select Indicator:", className="control-label"),
            dcc.Dropdown(
                id='indicator-selector',
                options=options,  # type: ignore
                value=options[0]['value'] if options else None,
                clearable=False,
                searchable=True,
                placeholder="Select an indicator..."
            )
        ], className="control-group")
    
    @staticmethod
    def create_year_selector(min_year: int = 2015, 
                           max_year: int = 2024,
                           default_range: List[int] = [2018, 2023]) -> html.Div:
        """
        Create year range selector.
        
        Args:
            min_year: Minimum year
            max_year: Maximum year
            default_range: Default selected range [start, end]
        """
            
        return html.Div([
            html.Label("Select Years:", className="control-label"),
            dcc.RangeSlider(
                id='year-slider',
                min=min_year,
                max=max_year,
                step=1,
                marks={year: str(year) for year in range(min_year, max_year + 1, 2)},
                value=default_range,
                tooltip={"placement": "bottom", "always_visible": False}
            )
        ], className="control-group")
    
    @staticmethod
    def create_chart_type_selector() -> html.Div:
        """Create chart type selector."""
        return html.Div([
            html.Label("Chart Type:", className="control-label"),
            dcc.RadioItems(
                id='chart-type-selector',
                options=[
                    {'label': 'Line Chart', 'value': 'line'},
                    {'label': 'Bar Chart', 'value': 'bar'},
                    {'label': 'Area Chart', 'value': 'area'},
                    {'label': 'Scatter Plot', 'value': 'scatter'}
                ],
                value='line',
                inline=True,
                className="radio-items"
            )
        ], className="control-group")
    
    @staticmethod
    def create_controls_panel(indicator_options: List[Dict[str, Any]]) -> html.Div:
        """
        Create controls panel.
        
        Args:
            indicator_options: Options for indicator dropdown
        """
        return html.Div([
            html.H3("Controls", className="panel-title"),
            DashboardLayout.create_indicator_selector(indicator_options),
            DashboardLayout.create_year_selector(),
            DashboardLayout.create_chart_type_selector(),
            html.Div([
                html.Button(
                    "Refresh Data", 
                    id="refresh-button", 
                    className="btn btn-primary"
                ),
                html.Button(
                    "Download Data", 
                    id="download-button", 
                    className="btn btn-secondary"
                ),
            ], className="button-group"),
            html.Div([
                html.Label("Additional Options:", className="control-label"),
                dcc.Checklist(
                    id='options-checklist',
                    options=[
                        {'label': 'Show Moving Average', 'value': 'moving_avg'},
                        {'label': 'Show Trend Line', 'value': 'trend'},
                        {'label': 'Highlight Outliers', 'value': 'outliers'}
                    ],
                    value=[],
                    className="checklist"
                )
            ], className="control-group")
        ], id="controls-panel")
    
    @staticmethod
    def create_indicator_info_card() -> html.Div:
        """Create placeholder for indicator information card."""
        return html.Div(
            id='indicator-info-content',
            className="info-card"
        )
    
    @staticmethod
    def create_statistics_cards() -> html.Div:
        """Create placeholder for statistics cards."""
        return html.Div(
            id='statistics-content',
            className="statistics-row"
        )
    
    @staticmethod
    def create_main_chart() -> html.Div:
        """Create main chart container."""
        return html.Div([
            dcc.Graph(id='main-chart', className="chart"),
            dcc.Loading(
                id="loading-main-chart",
                type="default",
                children=html.Div(id="loading-output-main")
            )
        ], className="chart-container")
    
    @staticmethod
    def create_comparison_chart() -> html.Div:
        """Create comparison chart container."""
        return html.Div([
            html.H3("Comparison View", className="section-title"),
            html.Div([
                html.Label("Compare with:", className="control-label"),
                dcc.Dropdown(
                    id='comparison-selector',
                    options=[],
                    multi=True,
                    placeholder="Select indicators to compare...",
                    className="comparison-dropdown"
                )
            ]),
            dcc.Graph(id='comparison-chart', className="chart")
        ], className="chart-container")
    
    @staticmethod
    def create_data_table() -> html.Div:
        """Create data table container."""
        return html.Div([
            html.H3("Data Table", className="section-title"),
            html.Div(id='data-table-content')
        ], id="data-table-section")
    
    @staticmethod
    def create_layout(indicator_options: List[Dict[str, Any]]) -> html.Div:
        """
        Create complete dashboard layout.
        
        Args:
            indicator_options: Options for indicator dropdown
        """
        return html.Div([
            DashboardLayout.create_header(),
            
            html.Div([
                # Left sidebar
                html.Div([
                    DashboardLayout.create_controls_panel(indicator_options),
                    DashboardLayout.create_indicator_info_card()
                ], id="sidebar"),
                
                # Main content area
                html.Div([
                    DashboardLayout.create_statistics_cards(),
                    
                    html.Div([
                        DashboardLayout.create_main_chart(),
                        DashboardLayout.create_comparison_chart()
                    ], id="charts-row"),
                    
                    DashboardLayout.create_data_table()
                ], id="main-content")
            ], id="dashboard-container"),
            
            # Hidden stores for data
            dcc.Store(id='indicator-data-store'),
            dcc.Store(id='comparison-data-store'),
            
            # Download component
            dcc.Download(id="download-dataframe-csv")
            
        ], id="app-container")