"""Dashboard layout components."""

from dash import dcc, html
from typing import Dict, List, Optional, Any


class DashboardLayout:
    """Manages dashboard layout components."""
    
    # UI translations
    TRANSLATIONS = {
        'fi': {
            'title': 'HUS Sotkanet Terveysmittaristo',
            'subtitle': 'Terveydenhuollon ja sosiaalialan indikaattorit Helsingin ja Uudenmaan sairaanhoitopiirille',
            'controls': 'Hallinta',
            'select_years': 'Valitse vuodet:',
            'chart_type': 'Kaaviotyyppi:',
            'line_chart': 'Viivakaavio',
            'bar_chart': 'Pylväskaavio',
            'gender': 'Sukupuoli:',
            'total': 'Yhteensä',
            'male': 'Miehet',
            'female': 'Naiset',
            'language': 'Kieli:',
            'refresh': 'Päivitä kaikki tiedot',
            'refresh_tooltip': 'Lataa uusimmat tiedot kaikille indikaattoreille Sotkanet-palvelusta',
            'download': 'Lataa kaikki tiedot',
            'download_tooltip': 'Lataa kaikki näytetyt tiedot CSV-tiedostona',
            'source': 'Lähde:',
            'last_updated': 'Päivitetty:',
            'no_metadata': 'Ei metatietoja saatavilla',
            'loading': 'Ladataan...',
            'no_data': 'Ei tietoja saatavilla',
            'footer_attribution': 'Tietolähde: Sotkanet / THL (Creative Commons Attribution 4.0, '
        },
        'sv': {
            'title': 'HUS Sotkanet Hälsopanel',
            'subtitle': 'Hälso- och socialvårdsindikatorer för Helsingfors och Nylands sjukvårdsdistrikt',
            'controls': 'Kontroller',
            'select_years': 'Välj år:',
            'chart_type': 'Diagramtyp:',
            'line_chart': 'Linjediagram',
            'bar_chart': 'Stapeldiagram',
            'gender': 'Kön:',
            'total': 'Totalt',
            'male': 'Män',
            'female': 'Kvinnor',
            'language': 'Språk:',
            'refresh': 'Uppdatera alla data',
            'refresh_tooltip': 'Ladda de senaste uppgifterna för alla indikatorer från Sotkanet-tjänsten',
            'download': 'Ladda ner alla data',
            'download_tooltip': 'Ladda ner alla visade data som CSV-fil',
            'source': 'Källa:',
            'last_updated': 'Uppdaterad:',
            'no_metadata': 'Ingen metadata tillgänglig',
            'loading': 'Laddar...',
            'no_data': 'Ingen data tillgänglig',
            'footer_attribution': 'Datakälla: Sotkanet / THL (Creative Commons Attribution 4.0, '
        },
        'en': {
            'title': 'HUS Sotkanet Health Dashboard',
            'subtitle': 'Healthcare and Social Indicators for Hospital District of Helsinki and Uusimaa',
            'controls': 'Controls',
            'select_years': 'Select Years:',
            'chart_type': 'Chart Type:',
            'line_chart': 'Line Chart',
            'bar_chart': 'Bar Chart',
            'gender': 'Gender:',
            'total': 'Total',
            'male': 'Male',
            'female': 'Female',
            'language': 'Language:',
            'refresh': 'Refresh All Data',
            'refresh_tooltip': 'Load the latest data for all indicators from Sotkanet service',
            'download': 'Download All Data',
            'download_tooltip': 'Download all displayed data as a CSV file',
            'source': 'Source:',
            'last_updated': 'Last Updated:',
            'no_metadata': 'No metadata available',
            'loading': 'Loading...',
            'no_data': 'No data available',
            'footer_attribution': 'Data source: Sotkanet / THL (Creative Commons Attribution 4.0, '
        }
    }
    
    @staticmethod
    def get_text(key: str, lang: str = 'fi') -> str:
        """Get translated text for a key."""
        return DashboardLayout.TRANSLATIONS.get(lang, DashboardLayout.TRANSLATIONS['fi']).get(key, key)
    
    @staticmethod
    def create_header(lang: str = 'fi') -> html.Div:
        """Create dashboard header with language support."""
        return html.Div([
            html.H1(
                id="dashboard-title",
                children=DashboardLayout.get_text('title', lang)
            ),
            html.P(
                id="dashboard-subtitle",
                children=DashboardLayout.get_text('subtitle', lang)
            ),
            html.Hr()
        ], id="header")
    
    @staticmethod
    def create_controls_panel(lang: str = 'fi') -> html.Div:
        """Create global controls panel with language support."""
        t = lambda key: DashboardLayout.get_text(key, lang)
        
        return html.Div([
            html.H3(t('controls'), className="panel-title", id="controls-title"),
            
            # Year selector - full width
            html.Div([
                html.Label(t('select_years'), className="control-label", id="year-label"),
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
            
            # All controls in one row
            html.Div([
                # Chart type selector
                html.Div([
                    html.Label(t('chart_type'), className="control-label", id="chart-type-label"),
                    dcc.RadioItems(
                        id='chart-type-selector',
                        options=[
                            {'label': t('line_chart'), 'value': 'line'},
                            {'label': t('bar_chart'), 'value': 'bar'}
                        ],
                        value='line',
                        inline=True,
                        className="radio-items"
                    )
                ], className="control-group"),
                
                # Gender selector
                html.Div([
                    html.Label(t('gender'), className="control-label", id="gender-label"),
                    dcc.RadioItems(
                        id='gender-selector',
                        options=[
                            {'label': t('total'), 'value': 'total'},
                            {'label': t('male'), 'value': 'male'},
                            {'label': t('female'), 'value': 'female'}
                        ],
                        value='total',
                        inline=True,
                        className="radio-items"
                    )
                ], className="control-group"),
                
                # Language selector
                html.Div([
                    html.Label(t('language'), className="control-label", id="language-label"),
                    dcc.RadioItems(
                        id='language-selector',
                        options=[
                            {'label': 'Suomi', 'value': 'fi'},
                            {'label': 'Svenska', 'value': 'sv'},
                            {'label': 'English', 'value': 'en'}
                        ],
                        value='fi',
                        inline=True,
                        className="radio-items"
                    )
                ], className="control-group"),
                
                # Buttons
                html.Div([
                    html.Button(
                        t('refresh'), 
                        id="refresh-button", 
                        className="btn btn-primary",
                        title=t('refresh_tooltip')
                    ),
                    html.Button(
                        t('download'), 
                        id="download-all-button", 
                        className="btn btn-secondary",
                        title=t('download_tooltip')
                    ),
                ], className="control-group button-group")
            ], className="controls-row")
        ], id="controls-panel")
    
    @staticmethod
    def create_indicator_card(indicator_id: int, metadata: Dict, lang: str = 'fi') -> html.Div:
        """
        Create a card for a single indicator with its chart and info.
        
        Args:
            indicator_id: The indicator ID
            metadata: Indicator metadata dictionary
            lang: Language code
        """
        # Get title in selected language, fallback to Finnish
        title = metadata.get('title', {}).get(lang, 
                metadata.get('title', {}).get('fi', f'Indicator {indicator_id}'))
        
        # Truncate long titles
        if len(title) > 100:
            title = title[:97] + "..."
        
        return html.Div([
            # Indicator header with title
            html.Div([
                html.H4(f"[{indicator_id}] {title}", 
                       className="indicator-title",
                       id={'type': 'indicator-title', 'index': indicator_id}),
                
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
                    className="indicator-chart",
                    config={
                        'displayModeBar': False,  # Hide the toolbar completely
                        'displaylogo': False,      # Hide plotly logo
                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d', 'zoom2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
                        'staticPlot': False  # Keep interactivity (hover) but hide tools
                    }
                ),
                type="default"
            )
        ], className="indicator-card", id=f"indicator-card-{indicator_id}")
    
    @staticmethod
    def create_indicators_grid(indicators_metadata: Dict, lang: str = 'fi') -> html.Div:
        """
        Create a grid of all indicator cards.
        
        Args:
            indicators_metadata: Dictionary of all indicators metadata
            lang: Language code
        """
        # Sort indicators by ID for consistent ordering
        sorted_indicators = sorted(indicators_metadata.items(), key=lambda x: int(x[0]))
        
        indicator_cards = []
        for ind_id_str, metadata in sorted_indicators:
            ind_id = int(ind_id_str)
            card = DashboardLayout.create_indicator_card(ind_id, metadata, lang)
            indicator_cards.append(card)
        
        return html.Div(
            indicator_cards,
            id="indicators-grid",
            className="indicators-grid"
        )
    
    @staticmethod
    def create_footer(lang: str = 'fi') -> html.Div:
        """Create dashboard footer with attribution."""
        attribution_text = DashboardLayout.get_text('footer_attribution', lang)
        
        return html.Div([
            html.Hr(),
            html.P([
                attribution_text,
                html.A('http://www.sotkanet.fi/', 
                      href='http://www.sotkanet.fi/',
                      target='_blank',
                      style={'color': '#0066CC'}),
                ')'
            ], style={
                'text-align': 'center',
                'color': '#666',
                'font-size': '0.9rem',
                'margin-top': '20px',
                'margin-bottom': '20px'
            })
        ], id="footer")
    
    @staticmethod
    def create_layout(indicators_metadata: Dict) -> html.Div:
        """
        Create complete dashboard layout.
        
        Args:
            indicators_metadata: Dictionary of all indicators metadata
        """
        # Start with Finnish as default
        return html.Div([
            # Header
            DashboardLayout.create_header('fi'),
            
            # Global controls
            DashboardLayout.create_controls_panel('fi'),
            
            # Main content - grid of all indicators
            html.Div([
                DashboardLayout.create_indicators_grid(indicators_metadata, 'fi')
            ], id="main-content"),
            
            # Footer with attribution
            DashboardLayout.create_footer('fi'),
            
            # Hidden stores for data
            dcc.Store(id='all-indicators-data-store'),
            dcc.Store(id='ui-settings-store'),
            dcc.Store(id='current-language-store', data='fi'),
            
            # Download component
            dcc.Download(id="download-all-data-csv")
            
        ], id="app-container")