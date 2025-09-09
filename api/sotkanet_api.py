"""Sotkanet API client for fetching health indicator data."""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger, log_api_call
from config.settings import SOTKANET_BASE_URL, HUS_REGION_ID, DEFAULT_YEARS

logger = get_logger('api.sotkanet')


class SotkanetAPI:
    """Client for interacting with Sotkanet REST API."""
    
    def __init__(self, 
                 base_url: str = SOTKANET_BASE_URL,
                 region_id: int = HUS_REGION_ID,
                 timeout: int = 30):
        """
        Initialize Sotkanet API client.
        
        Args:
            base_url: Base URL for Sotkanet API
            region_id: Default region ID (HUS = 629)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.region_id = region_id
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set headers to mimic browser requests and avoid 403 errors
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,fi;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://sotkanet.fi/sotkanet/fi/index',
        })
        
        logger.info(f"Initialized Sotkanet API client for region {region_id}")
    
    def get_indicator_data(self,
                          indicator_id: int,
                          region_id: int = 629,
                          years: List[int] = [2024],
                          genders: List[str] = ['totals']) -> List[Dict]:
        """
        Fetch data for a single indicator.
        
        Args:
            indicator_id: Indicator ID
            years: List of years to fetch (default: 2018-2023)
            region_id: Region ID to filter results (default: HUS)
            genders: List of genders to fetch ['male', 'female', 'total'] (default: ['total'])
            
        Returns:
            List of data points (empty list on error)
        """
        # Validate inputs
        if not isinstance(indicator_id, int) or indicator_id <= 0:
            logger.error(f"Invalid indicator_id: {indicator_id}")
            return []
        
        years = years or DEFAULT_YEARS
        region_id = region_id if region_id is not None else self.region_id
        genders = genders or ['total']
        
        # Map gender names to API codes
        gender_map = {
            'male': 'male',
            'female': 'female', 
            'total': 'total',
            'm': 'male',
            'f': 'female',
            't': 'total'
        }
        
        # Build URL with multiple years and genders as repeated parameters
        params = [f"indicator={indicator_id}"]
        
        # Add years as repeated parameters
        for year in years:
            params.append(f"years={year}")
        
        # Add genders as repeated parameters
        for gender in genders:
            gender_code = gender_map.get(gender.lower(), gender)
            params.append(f"genders={gender_code}")
        
        # Join all parameters
        url = f"{self.base_url}/json?{'&'.join(params)}"
        
        logger.debug(f"Fetching indicator {indicator_id} for years {years}, genders {genders}")
        logger.debug(f"URL: {url}")
        
        retries = 0
        max_retries = 3
        
        while retries < max_retries:
            try:
                response = self.session.get(url, timeout=self.timeout)
                log_api_call(url, "GET", response.status_code)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Log total data received
                    logger.debug(f"API returned {len(data)} total data points")
                    
                    # Filter for specified region if provided
                    if region_id is not None:
                        filtered_data = [
                            item for item in data 
                            if item.get('region') == region_id
                        ]
                        
                        if len(data) > 0 and len(filtered_data) == 0:
                            logger.debug(f"No data for region {region_id} (API returned data for other regions)")
                        
                        logger.info(f"Retrieved {len(filtered_data)} data points for indicator {indicator_id} in region {region_id}")
                        return filtered_data
                    else:
                        logger.info(f"Retrieved {len(data)} total data points for indicator {indicator_id}")
                        return data
                        
                elif response.status_code == 404:
                    logger.debug(f"No data for indicator {indicator_id} (404)")
                    return []
                    
                elif response.status_code == 403:
                    # If we get 403, fall back to individual year fetches
                    logger.warning(f"Got 403 error, falling back to individual year fetches")
                    return self._fetch_years_individually(indicator_id, years, region_id, genders)
                    
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    wait_time = (retries + 1) * 2
                    logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                    
                else:
                    logger.warning(f"Failed to fetch data: status {response.status_code}")
                    return []
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching data, attempt {retries + 1}/{max_retries}")
                retries += 1
                if retries < max_retries:
                    time.sleep(1)
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error: {e}")
                retries += 1
                if retries < max_retries:
                    time.sleep(2)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching data: {e}")
                return []
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {e}")
                return []
        
        logger.warning(f"Max retries exceeded for indicator {indicator_id}")
        return []
    
    def _fetch_years_individually(self, indicator_id: int, years: List[int], region_id: List[int], genders: List[str]) -> List[Dict]:
        """
        Fallback method to fetch years individually if batch fetch fails.
        
        Args:
            indicator_id: Indicator ID
            years: List of years
            region_id: Region ID to filter
            genders: List of genders
            
        Returns:
            List of data points
        """
        logger.info(f"Falling back to individual year fetches for indicator {indicator_id}")
        all_data = []
        
        gender_map = {
            'male': 'male',
            'female': 'female', 
            'total': 'total',
            'm': 'male',
            'f': 'female',
            't': 'total'
        }
        
        for year in years:
            for gender in genders:
                gender_code = gender_map.get(gender.lower(), gender)
                url = f"{self.base_url}/json?indicator={indicator_id}&years={year}&genders={gender_code}"
                
                try:
                    response = self.session.get(url, timeout=self.timeout)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Filter for region if specified
                        if region_id is not None:
                            filtered = [
                                item for item in data 
                                if item.get('region') == region_id
                            ]
                            all_data.extend(filtered)
                        else:
                            all_data.extend(data)
                            
                except Exception as e:
                    logger.warning(f"Failed to fetch year {year}, gender {gender_code}: {e}")
                    continue
                
                # Small delay between requests
                time.sleep(0.1)
        
        return all_data
    
    def get_multiple_indicators(self,
                               indicator_ids: List[int],
                               years: List[int] = [2024],
                               region_id: int = 629,
                               genders: List[str] = ['total']) -> Dict[int, List[Dict]]:
        """
        Fetch data for multiple indicators.
        
        Args:
            indicator_ids: List of indicator IDs
            years: List of years to fetch
            region_id: Region ID
            genders: List of genders to fetch
            
        Returns:
            Dictionary mapping indicator ID to data points
        """
        results = {}
        errors = []
        
        for ind_id in indicator_ids:
            try:
                data = self.get_indicator_data(ind_id, region_id, years, genders)
                results[ind_id] = data
            except Exception as e:
                logger.error(f"Failed to fetch indicator {ind_id}: {e}")
                errors.append({'indicator_id': ind_id, 'error': str(e)})
        
        if errors:
            logger.warning(f"Failed to fetch {len(errors)} indicators")
        
        return results
    
    def get_latest_value(self,
                        indicator_id: int,
                        region_id: Optional[int] = None,
                        genders: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Get the most recent data point for an indicator.
        
        Args:
            indicator_id: Indicator ID
            region_id: Region ID to filter results
            genders: List of genders to fetch
            
        Returns:
            Latest data point or None (or dict of genders if multiple)
        """
        # Fetch last 5 years of data
        current_year = datetime.now().year
        years = list(range(current_year - 5, current_year + 1))
        genders = genders or ['total']
        
        data = self.get_indicator_data(indicator_id, years, region_id, genders)
        
        if not data:
            return None
        
        # Sort by year and return latest
        sorted_data = sorted(data, key=lambda x: x.get('year', 0))
        
        if len(genders) == 1:
            return sorted_data[-1] if sorted_data else None
        else:
            # Return dict with latest for each gender
            latest = {}
            for gender in genders:
                gender_data = [d for d in sorted_data if d.get('gender') == gender]
                if gender_data:
                    latest[gender] = gender_data[-1]
            return latest if latest else None
    
    def get_time_series(self,
                       indicator_id: int,
                       start_year: int,
                       end_year: int,
                       region_id: int = 629,
                       genders: List[str] = ['total']) -> Dict[int, float]:
        """
        Get time series data for an indicator.
        
        Args:
            indicator_id: Indicator ID
            start_year: Start year
            end_year: End year (inclusive)
            region_id: Region ID to filter results
            genders: List of genders to fetch
            
        Returns:
            Dictionary mapping year to value (or nested dict if multiple genders)
        """
        years = list(range(start_year, end_year + 1))
        genders = genders or ['total']
        data = self.get_indicator_data(indicator_id, region_id, years, genders)
        
        # Create time series dictionary
        if len(genders) == 1:
            # Simple year -> value mapping for single gender
            time_series = {}
            for item in data:
                year = item.get('year')
                value = item.get('value')
                if year and value is not None:
                    time_series[year] = value
        else:
            # Nested year -> gender -> value mapping
            time_series = {}
            for item in data:
                year = item.get('year')
                gender = item.get('gender')
                value = item.get('value')
                if year and gender and value is not None:
                    if year not in time_series:
                        time_series[year] = {}
                    time_series[year][gender] = value
        
        return time_series
    
    def get_indicator_metadata(self, indicator_id: int) -> Optional[Dict]:
        """
        Fetch metadata for an indicator.
        
        Args:
            indicator_id: Indicator ID
            
        Returns:
            Indicator metadata or None
        """
        url = f"{self.base_url}/indicators/{indicator_id}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            log_api_call(url, "GET", response.status_code)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch metadata for indicator {indicator_id}: {e}")
            return None
    
    def get_regions(self) -> List[Dict]:
        """
        Fetch all available regions.
        
        Returns:
            List of regions
        """
        url = f"{self.base_url}/regions"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            log_api_call(url, "GET", response.status_code)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch regions: {e}")
            raise
    
    def search_indicators(self, search_term: str, language: str = 'fi') -> List[Dict]:
        """
        Search for indicators by keyword.
        
        Args:
            search_term: Search term
            language: Language code (fi, sv, en)
            
        Returns:
            List of matching indicators
        """
        url = f"{self.base_url}/indicators"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            log_api_call(url, "GET", response.status_code)
            response.raise_for_status()
            
            indicators = response.json()
            
            # Filter by search term in title
            matches = []
            for ind in indicators:
                title = ind.get('title', {}).get(language, '')
                if search_term.lower() in title.lower():
                    matches.append(ind)
            
            logger.info(f"Found {len(matches)} indicators matching '{search_term}'")
            return matches
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search indicators: {e}")
            raise
    
    def batch_fetch(self,
                   indicator_ids: List[int],
                   years: Optional[List[int]] = None,
                   genders: Optional[List[str]] = None,
                   save_to: Optional[str] = None) -> Dict:
        """
        Batch fetch data for multiple indicators.
        
        Args:
            indicator_ids: List of indicator IDs
            years: Years to fetch
            genders: List of genders to fetch ['male', 'female', 'total']
            save_to: Optional path to save results
            
        Returns:
            Dictionary with all fetched data
        """
        years = years or DEFAULT_YEARS
        genders = genders or ['total']
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'region_id': self.region_id,
            'years': years,
            'genders': genders,
            'indicators': {}
        }
        
        total = len(indicator_ids)
        
        for i, ind_id in enumerate(indicator_ids, 1):
            logger.info(f"Fetching indicator {ind_id} ({i}/{total})")
            
            try:
                data = self.get_indicator_data(ind_id, years, genders=genders)
                
                # Organize by year and gender
                by_year_gender = {}
                for item in data:
                    year = item.get('year')
                    gender = item.get('gender')
                    if year and gender:
                        if year not in by_year_gender:
                            by_year_gender[year] = {}
                        by_year_gender[year][gender] = {
                            'value': item.get('value'),
                            'absValue': item.get('absValue')
                        }
                
                results['indicators'][ind_id] = {
                    'data': by_year_gender,
                    'status': 'success',
                    'data_points': len(data)
                }
                
            except Exception as e:
                results['indicators'][ind_id] = {
                    'data': {},
                    'status': 'error',
                    'error': str(e)
                }
        
        # Save if requested
        if save_to:
            save_path = Path(save_to)
            save_path.parent.mkdir(exist_ok=True, parents=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Results saved to {save_path}")
        
        # Summary
        success_count = sum(
            1 for ind in results['indicators'].values() 
            if ind['status'] == 'success'
        )
        logger.info(f"Batch fetch complete: {success_count}/{total} indicators successful")
        
        return results
    
    def close(self):
        """Close the session."""
        self.session.close()
        logger.debug("API session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions
def fetch_indicator(indicator_id: int, years: Optional[List[int]] = None, genders: Optional[List[str]] = None) -> List[Dict]:
    """
    Quick fetch for a single indicator.
    
    Args:
        indicator_id: Indicator ID
        years: Years to fetch
        genders: Genders to fetch
        
    Returns:
        List of data points
    """
    with SotkanetAPI() as api:
        return api.get_indicator_data(indicator_id, years, genders=genders)


def fetch_latest(indicator_id: int, genders: Optional[List[str]] = None) -> Optional[Dict]:
    """
    Get latest value for an indicator.
    
    Args:
        indicator_id: Indicator ID
        genders: Genders to fetch
        
    Returns:
        Latest data point or None
    """
    with SotkanetAPI() as api:
        return api.get_latest_value(indicator_id, genders=genders)


def fetch_all_indicators(indicator_ids: List[int], 
                        years: Optional[List[int]] = None,
                        genders: Optional[List[str]] = None) -> Dict:
    """
    Fetch data for all indicators.
    
    Args:
        indicator_ids: List of indicator IDs
        years: Years to fetch
        genders: Genders to fetch
        
    Returns:
        Dictionary with all data
    """
    with SotkanetAPI() as api:
        return api.batch_fetch(indicator_ids, years, genders)


if __name__ == "__main__":
    # Test the API
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    
    from utils.logger import setup_logging
    setup_logging()
    
    # Test with a single indicator
    test_id = 186
    
    print(f"\nTesting Sotkanet REST API")
    print("="*60)
    
    with SotkanetAPI() as api:
        # Test basic data fetch with genders
        print("\n1. Testing data fetch for years 2020-2022...")
        data = api.get_indicator_data(test_id, years=[2020, 2021, 2022], region_id=api.region_id, genders=['total'])
        if data:
            print(f"   ✓ Retrieved {len(data)} data points")
            for item in data[:3]:  # Show first 3
                print(f"   Year {item.get('year')}: {item.get('value')}")
        else:
            print("   ✗ No data retrieved")
        
        # Get latest value
        print("\n2. Testing latest value...")
        latest = api.get_latest_value(test_id)
        if latest:
            print(f"   ✓ Latest value: {latest.get('value')} (year {latest.get('year')})")
        else:
            print("   ✗ No latest value found")
        
        # Get time series
        print("\n3. Testing time series 2018-2023...")
        time_series = api.get_time_series(test_id, 2018, 2023)
        if time_series:
            print(f"   ✓ Time series: {time_series}")
        else:
            print("   ✗ No time series data")
        
        # Get metadata
        print("\n4. Testing metadata fetch...")
        metadata = api.get_indicator_metadata(test_id)
        if metadata:
            title = metadata.get('title', {}).get('fi', 'Unknown')
            print(f"   ✓ Indicator: {title[:60]}")
        else:
            print("   ✗ No metadata retrieved")
        
        # Test batch fetch with known indicators
        print("\n5. Testing batch fetch with multiple indicators...")
        indicators_file = Path(__file__).parent.parent / "config" / "indicator_ids.txt"
        if indicators_file.exists():
            with open(indicators_file, 'r') as f:
                batch_ids = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            batch_ids.append(int(line))
                        except ValueError:
                            continue
                batch_ids = batch_ids[:3]  # Test with first 3
            
            if batch_ids:
                batch_data = api.batch_fetch(
                    batch_ids,
                    years=[2020, 2021, 2022]
                )
                success = sum(1 for ind in batch_data['indicators'].values() if ind['status'] == 'success')
                print(f"   ✓ Batch fetch: {success}/{len(batch_ids)} indicators successful")
                
                # Show sample data
                for ind_id, ind_data in batch_data['indicators'].items():
                    if ind_data['status'] == 'success':
                        print(f"   Indicator {ind_id}: {ind_data['data_points']} data points")
        else:
            print(f"   ⚠ No indicator file found at: {indicators_file}")
        
        # Test fetching all genders
        print("\n6. Testing fetch with all genders (male, female, total)...")
        gender_data = api.get_indicator_data(
            test_id, 
            years=[2021, 2022], 
            region_id=api.region_id, 
            genders=['male', 'female', 'total']
        )
        
        if gender_data:
            # Organize by year and gender for display
            by_year_gender = {}
            for item in gender_data:
                year = item.get('year')
                gender = item.get('gender')
                value = item.get('value')
                if year and gender:
                    if year not in by_year_gender:
                        by_year_gender[year] = {}
                    by_year_gender[year][gender] = value
            
            print(f"   ✓ Retrieved {len(gender_data)} data points")
            for year, genders in sorted(by_year_gender.items()):
                print(f"   Year {year}:")
                for gender, value in sorted(genders.items()):
                    print(f"     - {gender}: {value}")
        else:
            print("   ✗ No gender-specific data retrieved")
    
    print("\n✓ API test complete")