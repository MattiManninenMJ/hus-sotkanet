"""Data fetching module for Sotkanet API."""

import requests
import pandas as pd
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import HUS_REGION_ID, DEFAULT_YEARS, SOTKANET_BASE_URL
from utils.logger import get_logger, log_api_call

logger = get_logger('data.fetcher')


class SotkanetDataFetcher:
    """Handles all data fetching from Sotkanet API."""
    
    def __init__(self):
        """Initialize the data fetcher."""
        self.base_url = SOTKANET_BASE_URL
        self.region_id = HUS_REGION_ID
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict:
        """Load indicators metadata from JSON file."""
        metadata_path = Path("config/indicators_metadata.json")
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded metadata for {len(data.get('indicators', {}))} indicators")
                return data.get('indicators', {})
        logger.warning("No metadata file found")
        return {}
    
    def fetch_indicator_data(self, 
                           indicator_id: int, 
                           years: Optional[List[int]] = None,
                           gender: str = 'total') -> pd.DataFrame:
        """
        Fetch indicator data from Sotkanet API.
        
        Args:
            indicator_id: Indicator ID
            years: List of years to fetch
            gender: Gender filter (total, male, female)
            
        Returns:
            DataFrame with indicator data
        """
        if years is None:
            years = DEFAULT_YEARS
            
        # Build URL with year parameters
        year_params = "&".join([f"years={year}" for year in years])
        url = f"{self.base_url}/json?indicator={indicator_id}&{year_params}&genders={gender}&regions={self.region_id}"
        
        logger.info(f"Fetching data for indicator {indicator_id}, years: {min(years)}-{max(years)}")
        
        try:
            response = requests.get(url, timeout=10)
            log_api_call(url, "GET", response.status_code)
            response.raise_for_status()
            
            data = response.json()
            
            # Filter for HUS region
            hus_data = [item for item in data if item.get('region') == self.region_id]
            
            if hus_data:
                df = pd.DataFrame(hus_data)
                # Clean and prepare data
                df = df[['year', 'value', 'absValue']].dropna(subset=['year', 'value'])
                df = df.sort_values('year')
                
                logger.info(f"Retrieved {len(df)} data points for indicator {indicator_id}")
                return df
            else:
                logger.warning(f"No data found for indicator {indicator_id} in HUS region")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data for indicator {indicator_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing data for indicator {indicator_id}: {e}")
        
        return pd.DataFrame()
    
    def fetch_multiple_indicators(self, 
                                indicator_ids: List[int],
                                years: Optional[List[int]] = None) -> Dict[int, pd.DataFrame]:
        """
        Fetch data for multiple indicators.
        
        Args:
            indicator_ids: List of indicator IDs
            years: List of years to fetch
            
        Returns:
            Dictionary mapping indicator ID to DataFrame
        """
        results = {}
        
        for ind_id in indicator_ids:
            df = self.fetch_indicator_data(ind_id, years)
            if not df.empty:
                results[ind_id] = df
                
        logger.info(f"Fetched data for {len(results)}/{len(indicator_ids)} indicators")
        return results
    
    def get_indicator_metadata(self, indicator_id: str) -> Dict:
        """
        Get metadata for an indicator.
        
        Args:
            indicator_id: Indicator ID (as string)
            
        Returns:
            Dictionary with indicator metadata
        """
        return self.metadata.get(str(indicator_id), {})
    
    def get_all_indicators(self) -> Dict:
        """Get all available indicators metadata."""
        return self.metadata
    
    def get_indicator_options(self) -> List[Dict[str, Any]]:
        """
        Get formatted options for dropdown selector.
        
        Returns:
            List of dicts with 'label' and 'value' keys
        """
        options: List[Dict[str, Any]] = []
        for ind_id, metadata in self.metadata.items():
            title = metadata.get('title', {})
            label = title.get('fi', f"Indicator {ind_id}")
            if len(label) > 80:
                label = label[:77] + "..."
            options.append({
                'label': f"[{ind_id}] {label}", 
                'value': ind_id
            })
        return options