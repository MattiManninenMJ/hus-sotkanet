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
    def create_controls_panel() -> html.Div:
        """Create global controls panel."""
        return html.Div([
            html.H3("Controls", className="panel-title"),
            
            # Year selector - full width
            html.Div([
                html.Label("Select Years:", className="control-label"),
                dcc.RangeSlider(
                    id='year-slider',
                    min=2015,
                    max=2024,
                    step=1,
                    marks={year: str(year) for year in range(2015, 2025, 2)},
                    value=[2018, 2023],
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ], className="control-group year-selector"),
            
            # Options row
            html.Div([
                # Chart type selector
                html.Div([
                    html.Label("Chart Type:", className="control-label"),
                    dcc.RadioItems(
                        id='chart-type-selector',
                        options=[
                            {'label': 'Line Chart', 'value': 'line'},
                            {'label': 'Bar Chart', 'value': 'bar'}
                        ],
                        value='line',
                        inline=True,
                        className="radio-items"
                    )
                ], className="control-group"),
                
                # Gender selector
                html.Div([
                    html.Label("Gender:", className="control-label"),
                    dcc.RadioItems(
                        id='gender-selector',
                        options=[
                            {'label': 'Total', 'value': 'total'},
                            {'label': 'Male', 'value': 'male'},
                            {'label': 'Female', 'value': 'female'}
                        ],
                        value='total',
                        inline=True,
                        className="radio-items"
                    )
                ], className="control-group"),
                
                # Language selector
                html.Div([
                    html.Label("Language:", className="control-label"),
                    dcc.RadioItems(
                        id='language-selector',
                        options=[
                            {'label': 'Suomi', 'value': 'fi'},
                            {'label': 'English', 'value': 'en'},
                            {'label': 'Svenska', 'value': 'sv'}
                        ],
                        value='fi',
                        inline=True,
                        className="radio-items"
                    )
                ], className="control-group"),
            ], className="options-row"),
            
            # Buttons
            html.Div([
                html.Button(
                    "Refresh All Data", 
                    id="refresh-button", 
                    className="btn btn-primary"
                ),
                html.Button(
                    "Download All Data", 
                    id="download-all-button", 
                    className="btn btn-secondary"
                ),
            ], className="button-group")
        ], id="controls-panel")
    
    @staticmethod
    def create_indicator_card(indicator_id: int, metadata: Dict) -> html.Div:
        """
        Create a card for a single indicator with its chart and info.
        
        Args:
            indicator_id: The indicator ID
            metadata: Indicator metadata dictionary
        """
        # Default to Finnish title if metadata is available
        title = metadata.get('title', {}).get('fi', f'Indicator {indicator_id}')
        
        # Truncate long titles
        if len(title) > 100:
            title = title[:97] + "..."
        
        return html.Div([
            # Indicator header with title
            html.Div([
                html.H4(f"[{indicator_id}] {title}", className="indicator-title"),
                
                # Info button that shows/hides metadata
                html.Button(
                    "ℹ", 
                    id={'type': 'info-button', 'index': indicator_id},
                    className="info-button",
                    title="Show/hide information"
                )
            ], className="indicator-header"),
            
            # Collapsible info section
            html.Div(
                id={'type': 'info-content', 'index': indicator_id},
                className="indicator-info-content",
                style={'display': 'none'}
            ),
            
            # Chart container
            dcc.Loading(
                dcc.Graph(
                    id={'type': 'indicator-chart', 'index': indicator_id},
                    className="indicator-chart"
                ),
                type="default"
            )
        ], className="indicator-card", id=f"indicator-card-{indicator_id}")
    
    @staticmethod
    def create_indicators_grid(indicators_metadata: Dict) -> html.Div:
        """
        Create a grid of all indicator cards.
        
        Args:
            indicators_metadata: Dictionary of all indicators metadata
        """
        # Sort indicators by ID for consistent ordering
        sorted_indicators = sorted(indicators_metadata.items(), key=lambda x: int(x[0]))
        
        indicator_cards = []
        for ind_id_str, metadata in sorted_indicators:
            ind_id = int(ind_id_str)
            card = DashboardLayout.create_indicator_card(ind_id, metadata)
            indicator_cards.append(card)
        
        return html.Div(
            indicator_cards,
            id="indicators-grid",
            className="indicators-grid"
        )
    
    @staticmethod
    def create_layout(indicators_metadata: Dict) -> html.Div:
        """
        Create complete dashboard layout.
        
        Args:
            indicators_metadata: Dictionary of all indicators metadata
        """
        return html.Div([
            # Header
            DashboardLayout.create_header(),
            
            # Global controls
            DashboardLayout.create_controls_panel(),
            
            # Main content - grid of all indicators
            html.Div([
                DashboardLayout.create_indicators_grid(indicators_metadata)
            ], id="main-content"),
            
            # Hidden stores for data
            dcc.Store(id='all-indicators-data-store'),
            dcc.Store(id='ui-settings-store'),
            
            # Download component
            dcc.Download(id="download-all-data-csv")
            
        ], id="app-container")