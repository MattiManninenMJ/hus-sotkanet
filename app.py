#!/usr/bin/env python3
"""
HUS Sotkanet Health Dashboard - Main Application
Modular Dash application for visualizing health indicators.
"""

import dash
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import modules
from data.fetcher import SotkanetDataFetcher
from data.processor import DataProcessor
from dashboard.layout import DashboardLayout
from dashboard.callbacks import DashboardCallbacks
from utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('app')


class HUSDashboardApp:
    """Main dashboard application class."""
    
    def __init__(self):
        """Initialize the dashboard application."""
        logger.info("Initializing HUS Dashboard Application")
        
        # Initialize data handlers
        self.data_fetcher = SotkanetDataFetcher()
        self.data_processor = DataProcessor()
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            suppress_callback_exceptions=True,
            meta_tags=[
                {"name": "viewport", "content": "width=device-width, initial-scale=1"}
            ]
        )
        
        self.app.title = "HUS Sotkanet Health Dashboard"
        
        # Setup layout
        self._setup_layout()
        
        # Setup callbacks
        self._setup_callbacks()
        
        # Add custom CSS
        self._setup_styles()
        
        logger.info("Dashboard initialization complete")
    
    def _setup_layout(self):
        """Setup the dashboard layout."""
        logger.info("Setting up dashboard layout")
        
        # Get indicator options
        indicator_options = self.data_fetcher.get_indicator_options()
        
        if not indicator_options:
            logger.warning("No indicators available - check metadata")
        
        # Create and set layout
        self.app.layout = DashboardLayout.create_layout(indicator_options)
    
    def _setup_callbacks(self):
        """Setup dashboard callbacks."""
        logger.info("Setting up dashboard callbacks")
        
        # Initialize callbacks handler
        callbacks_handler = DashboardCallbacks(
            self.data_fetcher,
            self.data_processor
        )
        
        # Register callbacks
        callbacks_handler.register_callbacks(self.app)
    
    def _setup_styles(self):
        """Setup custom CSS styles."""
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    /* Base styles */
                    * {
                        box-sizing: border-box;
                        margin: 0;
                        padding: 0;
                    }
                    
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
                                     Roboto, Oxygen, Ubuntu, sans-serif;
                        background-color: #f5f7fa;
                        color: #333;
                    }
                    
                    /* Layout containers */
                    #app-container {
                        max-width: 1600px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    
                    #header {
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }
                    
                    #dashboard-title {
                        color: #0066CC;
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                    }
                    
                    #dashboard-subtitle {
                        color: #666;
                        font-size: 1.1rem;
                    }
                    
                    #dashboard-container {
                        display: grid;
                        grid-template-columns: 350px 1fr;
                        gap: 20px;
                    }
                    
                    #sidebar {
                        display: flex;
                        flex-direction: column;
                        gap: 20px;
                    }
                    
                    #controls-panel, .info-card {
                        background: white;
                        padding: 25px;
                        border-radius: 10px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }
                    
                    #main-content {
                        display: flex;
                        flex-direction: column;
                        gap: 20px;
                    }
                    
                    /* Controls */
                    .control-group {
                        margin-bottom: 20px;
                    }
                    
                    .control-label {
                        display: block;
                        margin-bottom: 8px;
                        font-weight: 600;
                        color: #444;
                        font-size: 0.95rem;
                    }
                    
                    .panel-title {
                        color: #0066CC;
                        margin-bottom: 20px;
                        font-size: 1.3rem;
                    }
                    
                    /* Buttons */
                    .button-group {
                        display: flex;
                        gap: 10px;
                        margin-top: 20px;
                    }
                    
                    .btn {
                        padding: 10px 20px;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 500;
                        transition: all 0.3s ease;
                    }
                    
                    .btn-primary {
                        background: #0066CC;
                        color: white;
                    }
                    
                    .btn-primary:hover {
                        background: #0052A3;
                        transform: translateY(-1px);
                        box-shadow: 0 4px 8px rgba(0,102,204,0.3);
                    }
                    
                    .btn-secondary {
                        background: #6c757d;
                        color: white;
                    }
                    
                    .btn-secondary:hover {
                        background: #5a6268;
                        transform: translateY(-1px);
                    }
                    
                    /* Statistics cards */
                    .statistics-row {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                    }
                    
                    .stat-card {
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        text-align: center;
                        transition: transform 0.3s ease;
                    }
                    
                    .stat-card:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    }
                    
                    .stat-card h4 {
                        color: #666;
                        font-size: 0.9rem;
                        font-weight: 500;
                        margin-bottom: 10px;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }
                    
                    .stat-value {
                        font-size: 2rem;
                        font-weight: bold;
                        margin: 10px 0;
                    }
                    
                    .stat-label {
                        color: #999;
                        font-size: 0.85rem;
                    }
                    
                    .trend-up { color: #00AA88; }
                    .trend-down { color: #FF4444; }
                    .trend-neutral { color: #666; }
                    
                    /* Charts */
                    #charts-row {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 20px;
                    }
                    
                    .chart-container {
                        background: white;
                        padding: 25px;
                        border-radius: 10px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }
                    
                    /* Data table */
                    #data-table-section {
                        background: white;
                        padding: 25px;
                        border-radius: 10px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }
                    
                    .section-title {
                        color: #0066CC;
                        margin-bottom: 20px;
                        font-size: 1.2rem;
                    }
                    
                    .data-table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    
                    .data-table th,
                    .data-table td {
                        padding: 12px;
                        text-align: left;
                        border-bottom: 1px solid #e0e0e0;
                    }
                    
                    .data-table th {
                        background-color: #f8f9fa;
                        font-weight: 600;
                        color: #444;
                    }
                    
                    .data-table tr:hover {
                        background-color: #f8f9fa;
                    }
                    
                    /* Info card */
                    .info-card h4 {
                        color: #0066CC;
                        margin-bottom: 15px;
                    }
                    
                    .info-card p {
                        margin-bottom: 10px;
                        line-height: 1.6;
                    }
                    
                    .info-card strong {
                        color: #444;
                    }
                    
                    .info-card hr {
                        margin: 15px 0;
                        border: none;
                        border-top: 1px solid #e0e0e0;
                    }
                    
                    /* Dropdowns and inputs */
                    .Select-control {
                        border-radius: 6px !important;
                        border-color: #ddd !important;
                    }
                    
                    .Select-control:hover {
                        border-color: #0066CC !important;
                    }
                    
                    /* Radio items */
                    .radio-items {
                        display: flex;
                        gap: 15px;
                        flex-wrap: wrap;
                    }
                    
                    .radio-items label {
                        display: flex;
                        align-items: center;
                        gap: 5px;
                        cursor: pointer;
                    }
                    
                    /* Checklist */
                    .checklist {
                        display: flex;
                        flex-direction: column;
                        gap: 10px;
                    }
                    
                    .checklist label {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        cursor: pointer;
                    }
                    
                    /* Loading indicator */
                    ._dash-loading {
                        margin: auto;
                        color: #0066CC;
                    }
                    
                    /* Responsive design */
                    @media (max-width: 1200px) {
                        #dashboard-container {
                            grid-template-columns: 1fr;
                        }
                        
                        #sidebar {
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 20px;
                        }
                        
                        #charts-row {
                            grid-template-columns: 1fr;
                        }
                    }
                    
                    @media (max-width: 768px) {
                        #sidebar {
                            grid-template-columns: 1fr;
                        }
                        
                        .statistics-row {
                            grid-template-columns: 1fr 1fr;
                        }
                        
                        #dashboard-title {
                            font-size: 1.8rem;
                        }
                    }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''
    
    def run(self, debug: bool = True, port: int = 8050, host: str = '127.0.0.1'):
        """
        Run the dashboard server.
        
        Args:
            debug: Enable debug mode
            port: Port number
            host: Host address
        """
        logger.info(f"Starting dashboard server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        self.app.run(
            debug=debug,
            port=port,
            host=host
        )


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='HUS Sotkanet Health Dashboard')
    parser.add_argument('--port', type=int, default=8050, help='Port number')
    parser.add_argument('--host', default='127.0.0.1', help='Host address')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run app
    app = HUSDashboardApp()
    app.run(debug=args.debug, port=args.port, host=args.host)


if __name__ == '__main__':
    main()