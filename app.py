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