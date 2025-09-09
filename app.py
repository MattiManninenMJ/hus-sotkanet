#!/usr/bin/env python3
"""
HUS Sotkanet Health Dashboard - Main Application
Simplified version that fetches metadata on startup.
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
from api.sotkanet_api import SotkanetAPI
from config import settings
from utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('app')


class HUSDashboardApp:
    """Main dashboard application class."""
    
    def __init__(self):
        """Initialize the dashboard application."""
        logger.info("Initializing HUS Dashboard Application")
        logger.info(f"Environment: {settings.ENV}")
        logger.info(f"Configured indicators: {settings.INDICATOR_IDS}")
        
        # Fetch metadata for configured indicators on startup
        logger.info(f"Fetching metadata for {len(settings.INDICATOR_IDS)} indicators...")
        api = SotkanetAPI()
        metadata = {}
        
        for ind_id in settings.INDICATOR_IDS:
            try:
                logger.info(f"  Fetching metadata for indicator {ind_id}...")
                ind_metadata = api.get_indicator_metadata(ind_id)
                metadata[str(ind_id)] = ind_metadata
            except Exception as e:
                logger.error(f"  Failed to fetch metadata for {ind_id}: {e}")
        
        logger.info(f"✓ Fetched metadata for {len(metadata)} indicators")
        
        # Store metadata in memory
        self.indicators_metadata = metadata
        
        # Initialize data fetcher with our in-memory metadata
        self.data_fetcher = SotkanetDataFetcher()
        # Override the fetcher's metadata with our fresh data
        self.data_fetcher.metadata = self.indicators_metadata
        
        # Clear cache to ensure fresh data
        logger.info("Clearing cache to ensure fresh data")
        self.data_fetcher.clear_cache()
        
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
        
        # Setup layout with fresh metadata
        self._setup_layout()
        
        # Setup callbacks
        self._setup_callbacks()
        
        logger.info("Dashboard initialization complete")
    
    def _setup_layout(self):
        """Setup the dashboard layout."""
        logger.info("Setting up dashboard layout")
        
        # Use our in-memory metadata
        if not self.indicators_metadata:
            logger.warning("No indicators metadata available")
        
        # Create and set layout with metadata
        self.app.layout = DashboardLayout.create_layout(self.indicators_metadata)
    
    def _setup_callbacks(self):
        """Setup dashboard callbacks."""
        logger.info("Setting up dashboard callbacks")
        
        # Initialize callbacks handler with our fetcher that has fresh metadata
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