"""
Consolidated Sotkanet API client.
All API calls to Sotkanet should go through this module.
"""

import requests
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from utils.logger import get_logger, log_api_call

logger = get_logger('sotkanet_api')


class SotkanetAPIError(Exception):
    """
    Base exception for Sotkanet API errors.
    Raised for any error encountered during API requests or processing.
    """
    pass


class SotkanetAPI:
    """
    Unified client for Sotkanet REST API.
    All API interactions should go through this class.
    Handles metadata and data fetching, retry logic, and session management.
    """
    
    def __init__(self, 
                 base_url: Optional[str] = None,
                 timeout: Optional[int] = None,
                 retry_count: Optional[int] = None,
                 retry_delay: Optional[int] = None):
        """
        Initialize Sotkanet API client.
        Sets up session, headers, and retry logic for robust API communication.
        Args:
            base_url: API base URL (defaults to settings)
            timeout: Request timeout in seconds
            retry_count: Number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url or settings.SOTKANET_BASE_URL
        self.timeout = timeout or settings.API_TIMEOUT
        self.retry_count = retry_count or settings.API_RETRY_COUNT
        self.retry_delay = retry_delay or settings.API_RETRY_DELAY
        
        # Create session for connection pooling
        self.session = requests.Session()
        
        # Add browser-like headers to avoid 403 errors
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://sotkanet.fi/',
            'Origin': 'https://sotkanet.fi'
        })
        
        logger.info(f"Initialized SotkanetAPI client for {self.base_url}")
    
    def _make_request(self, 
                      endpoint: str, 
                      params: Optional[Dict[str, Any]] = None,
                      method: str = 'GET') -> Any:
        """
        Make HTTP request to the Sotkanet API with retry logic.
        Handles timeouts, HTTP errors, and JSON decoding errors.
        Args:
            endpoint: API endpoint (can include query string)
            params: Query parameters (optional, since we often build the query string manually)
            method: HTTP method
        Returns:
            Response data (JSON)
        Raises:
            SotkanetAPIError: On API errors
        """
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.retry_count):
            try:
                logger.debug(f"Request {method} {url} (attempt {attempt + 1}/{self.retry_count})")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=self.timeout
                )
                
                log_api_call(url, method, response.status_code)
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Return JSON data
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.retry_count}")
                if attempt == self.retry_count - 1:
                    raise SotkanetAPIError(f"Request timed out after {self.retry_count} attempts")
                time.sleep(self.retry_delay)
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                if e.response.status_code == 404:
                    raise SotkanetAPIError(f"Resource not found: {url}")
                elif e.response.status_code >= 500:
                    # Retry on server errors
                    if attempt < self.retry_count - 1:
                        logger.warning(f"Server error, retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                        continue
                raise SotkanetAPIError(f"HTTP {e.response.status_code}: {e}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt == self.retry_count - 1:
                    raise SotkanetAPIError(f"Request failed: {e}")
                time.sleep(self.retry_delay)
                
            except ValueError as e:
                # JSON decode error
                logger.error(f"Invalid JSON response: {e}")
                raise SotkanetAPIError(f"Invalid JSON response from API")
    
    def get_indicator_metadata(self, indicator_id: int) -> Dict:
        """
        Fetch metadata for a single indicator from the API.
        Args:
            indicator_id: Indicator ID
        Returns:
            Indicator metadata dictionary
        """
        logger.info(f"Fetching metadata for indicator {indicator_id}")
        
        endpoint = f"indicators/{indicator_id}"
        data = self._make_request(endpoint)
        
        # Add indicator_id to response for convenience
        data['indicator_id'] = indicator_id
        
        return data
    
    def get_indicator_data(self,
                          indicator_id: int,
                          region_id: Optional[int] = None,
                          years: Optional[List[int]] = None,
                          genders: Optional[List[str]] = None) -> List[Dict]:
        """
        Fetch data for a single indicator for a region, years, and genders.
        Args:
            indicator_id: Indicator ID (required)
            region_id: Region ID (defaults to HUS)
            years: List of years (defaults to settings)
            genders: List of genders (defaults to all: ['male', 'female', 'total'])
        Returns:
            List of data points with all requested genders
        """
        # Set defaults for optional parameters
        region_id = region_id or settings.HUS_REGION_ID
        years = years or settings.DEFAULT_YEARS
        genders = genders or ['male', 'female', 'total']
        
        logger.info(f"Fetching data for indicator {indicator_id}, region {region_id}, years {years}, genders {genders}")
        
        # Build query parameters as a list of tuples
        # This allows repeated parameters for lists
        params: List[tuple[str, Union[int, str]]] = [
            ('indicator', indicator_id),
            ('regions', region_id),
        ]
        
        # Add each year as a separate parameter
        for year in years:
            params.append(('years', year))
        
        # Add each gender as a separate parameter
        for gender in genders:
            params.append(('genders', gender))
        
        # Convert to query string
        query_string = urlencode(params)
        
        # Use json endpoint with query string already built
        endpoint = f"json?{query_string}"
        
        # Make request (params already in URL, so we don't pass params)
        data = self._make_request(endpoint)
        
        # Filter for the requested region (API might return others)
        filtered_data = [
            item for item in data 
            if item.get('region') == region_id
        ]
        
        return filtered_data
    
    def get_multiple_indicators_data(self,
                                    indicator_ids: List[int],
                                    region_id: Optional[int] = None,
                                    years: Optional[List[int]] = None,
                                    genders: Optional[List[str]] = None) -> Dict[int, List[Dict]]:
        """
        Fetch data for multiple indicators for a region, years, and genders.
        Args:
            indicator_ids: List of indicator IDs
            region_id: Region ID
            years: List of years
            genders: List of genders (defaults to all)
        Returns:
            Dictionary mapping indicator_id to data points
        """
        # Resolve defaults here to avoid passing None
        region_id = region_id or settings.HUS_REGION_ID
        years = years or settings.DEFAULT_YEARS
        genders = genders or ['male', 'female', 'total']
        
        logger.info(f"Fetching data for {len(indicator_ids)} indicators with all genders")
        
        results = {}
        
        for indicator_id in indicator_ids:
            try:
                # Now region_id, years, and genders are guaranteed to be non-None
                data = self.get_indicator_data(indicator_id, region_id, years, genders)
                results[indicator_id] = data
            except SotkanetAPIError as e:
                logger.warning(f"Failed to fetch indicator {indicator_id}: {e}")
                results[indicator_id] = []
        
        return results
    
    def get_all_metadata(self, indicator_ids: Optional[List[int]] = None) -> Dict[str, Dict]:
        """
        Fetch metadata for all configured indicators.
        Args:
            indicator_ids: List of IDs (defaults to settings.INDICATOR_IDS)
        Returns:
            Dictionary mapping indicator_id (as string) to metadata
        """
        indicator_ids = indicator_ids or settings.INDICATOR_IDS
        
        logger.info(f"Fetching metadata for {len(indicator_ids)} indicators")
        
        metadata = {}
        
        for indicator_id in indicator_ids:
            try:
                data = self.get_indicator_metadata(indicator_id)
                metadata[str(indicator_id)] = data
                
                # Log progress
                title = data.get('title', {}).get('fi', 'Unknown')
                logger.info(f"  ✓ {indicator_id}: {title[:50]}...")
                
            except SotkanetAPIError as e:
                logger.error(f"  ✗ Failed to fetch metadata for {indicator_id}: {e}")
        
        return metadata
    
    def validate_data_availability(self,
                                   indicator_id: int,
                                   region_id: Optional[int] = None,
                                   years: Optional[List[int]] = None,
                                   genders: Optional[List[str]] = None) -> Dict:
        """
        Check data availability for an indicator for a region, years, and genders.
        Args:
            indicator_id: Indicator ID
            region_id: Region ID
            years: Years to check
            genders: Genders to check (defaults to ['total'])
        Returns:
            Validation results dictionary
        """
        # Resolve defaults here
        region_id = region_id or settings.HUS_REGION_ID
        years = years or settings.DEFAULT_YEARS
        genders = genders or ['total']  # For validation, usually we just check 'total'
        
        try:
            # Now all parameters are guaranteed to be non-None
            data = self.get_indicator_data(indicator_id, region_id, years, genders)
            
            # Extract available years (from 'total' gender for consistency)
            total_data = [item for item in data if item.get('gender') == 'total']
            
            available_years = sorted(set(
                item['year'] for item in total_data 
                if item.get('year')
            ))
            
            missing_years = sorted(set(years) - set(available_years))
            
            # Check gender availability
            available_genders = list()

            for item in data:
                g = item.get('gender')
                if g is not None:
                    available_genders.append(g)

            available_genders = sorted(set(available_genders))            
            return {
                'indicator_id': indicator_id,
                'has_data': len(available_years) > 0,
                'requested_years': years,
                'available_years': available_years,
                'missing_years': missing_years,
                'available_genders': available_genders,
                'data_points': len(data),
                'completeness': len(available_years) / len(years) * 100 if years else 0,
                'status': 'OK' if available_years else 'NO_DATA'
            }
            
        except SotkanetAPIError as e:
            return {
                'indicator_id': indicator_id,
                'has_data': False,
                'error': str(e),
                'status': 'ERROR'
            }
    
    def get_regions(self) -> List[Dict]:
        """
        Fetch all available regions from the API.
        Returns:
            List of region dictionaries
        """
        logger.info("Fetching regions list")
        
        endpoint = "regions"
        return self._make_request(endpoint)
    
    def close(self):
        """
        Close the requests session.
        Should be called when done with the API client.
        """
        self.session.close()
    
    def __enter__(self):
        """
        Context manager entry. Returns self for use in 'with' statements.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit. Closes the session.
        """
        self.close()


# Singleton instance for convenience
_api_instance = None

def get_api() -> SotkanetAPI:
    """
    Get singleton API instance for convenience functions.
    Returns:
        SotkanetAPI instance
    """
    global _api_instance
    if _api_instance is None:
        _api_instance = SotkanetAPI()
    return _api_instance


# Convenience functions that use the singleton
def fetch_indicator_metadata(indicator_id: int) -> Dict:
    """
    Convenience function to fetch metadata for a single indicator.
    Args:
        indicator_id: Indicator ID
    Returns:
        Indicator metadata dictionary
    """
    return get_api().get_indicator_metadata(indicator_id)


def fetch_indicator_data(indicator_id: int, 
                         region_id: Optional[int] = None,
                         years: Optional[List[int]] = None,
                         genders: Optional[List[str]] = None) -> List[Dict]:
    """
    Convenience function to fetch data for a single indicator with all genders.
    Args:
        indicator_id: Indicator ID
        region_id: Region ID
        years: List of years
        genders: List of genders
    Returns:
        List of data points
    """
    return get_api().get_indicator_data(indicator_id, region_id, years, genders)


def fetch_all_metadata(indicator_ids: Optional[List[int]] = None) -> Dict[str, Dict]:
    """
    Convenience function to fetch metadata for all configured indicators.
    Args:
        indicator_ids: List of indicator IDs
    Returns:
        Dictionary mapping indicator_id to metadata
    """
    return get_api().get_all_metadata(indicator_ids)


def validate_data_availability(indicator_id: int,
                               region_id: Optional[int] = None,
                               years: Optional[List[int]] = None,
                               genders: Optional[List[str]] = None) -> Dict:
    """
    Convenience function to check data availability for an indicator.
    Args:
        indicator_id: Indicator ID
        region_id: Region ID
        years: List of years
        genders: List of genders
    Returns:
        Validation results dictionary
    """
    return get_api().validate_data_availability(indicator_id, region_id, years, genders)


def filter_data_by_gender(data: List[Dict], gender: str) -> List[Dict]:
    """
    Filter data points by specific gender.
    Args:
        data: List of data points from API
        gender: Gender to filter for ('male', 'female', or 'total')
    Returns:
        Filtered list of data points
    """
    return [item for item in data if item.get('gender') == gender]


def filter_data_by_year(data: List[Dict], year: int) -> List[Dict]:
    """
    Filter data points by specific year.
    Args:
        data: List of data points from API
        year: Year to filter for
    Returns:
        Filtered list of data points
    """
    return [item for item in data if item.get('year') == year]


def filter_data_by_years(data: List[Dict], years: List[int]) -> List[Dict]:
    """
    Filter data points by multiple years.
    Args:
        data: List of data points from API
        years: Years to filter for
    Returns:
        Filtered list of data points
    """
    year_set = set(years)
    return [item for item in data if item.get('year') in year_set]