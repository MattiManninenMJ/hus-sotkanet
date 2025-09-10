"""Data fetching module using the consolidated API layer."""

import pandas as pd
from typing import List, Dict, Optional, Any, Union
from pathlib import Path
import json
import hashlib
import pickle
from datetime import datetime, timedelta
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.sotkanet_api import SotkanetAPI, SotkanetAPIError, filter_data_by_gender
from config import settings
from utils.logger import get_logger

logger = get_logger('data.fetcher')


class DataCache:
    """Simple cache implementation for API data."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory for cache files
            ttl_seconds: Time to live for cache entries in seconds
        """
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.ttl = timedelta(seconds=ttl_seconds)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_key(self, **kwargs) -> str:
        """Generate cache key from parameters."""
        key_str = json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, **kwargs) -> Optional[Any]:
        """Get data from cache if valid."""
        if not settings.CACHE_ENABLED:
            return None
            
        cache_key = self._get_cache_key(**kwargs)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # Check if cache is still valid
                if datetime.now() - cached_data['timestamp'] < self.ttl:
                    logger.debug(f"Cache hit for key {cache_key}")
                    return cached_data['data']
                else:
                    logger.debug(f"Cache expired for key {cache_key}")
                    cache_file.unlink()  # Remove expired cache
            except Exception as e:
                logger.warning(f"Error reading cache: {e}")
        
        return None
    
    def set(self, data: Any, **kwargs) -> None:
        """Store data in cache."""
        if not settings.CACHE_ENABLED:
            return
            
        cache_key = self._get_cache_key(**kwargs)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            cached_data = {
                'timestamp': datetime.now(),
                'data': data,
                'params': kwargs
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
            logger.debug(f"Cached data with key {cache_key}")
        except Exception as e:
            logger.warning(f"Error writing cache: {e}")
    
    def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Error deleting cache file {cache_file}: {e}")
        logger.info("Cache cleared")


class SotkanetDataFetcher:
    """Handles data fetching using the consolidated API layer."""
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize the data fetcher.
        
        Args:
            use_cache: Whether to use caching
        """
        self.api = SotkanetAPI()
        self.region_id = settings.HUS_REGION_ID
        self.metadata = {}  # Will be set by the app after fetching
        self.cache = DataCache(ttl_seconds=settings.CACHE_TTL) if use_cache else None
    
    def fetch_indicator_data(self, 
                           indicator_id: int, 
                           years: Optional[List[int]] = None,
                           genders: Optional[List[str]] = None,
                           return_dataframe: bool = True) -> Union[pd.DataFrame, List[Dict]]:
        """
        Fetch indicator data using the API layer.
        
        Args:
            indicator_id: Indicator ID
            years: List of years to fetch (defaults to settings)
            genders: List of genders to fetch (defaults to all)
            return_dataframe: If True, return DataFrame; otherwise return list of dicts
            
        Returns:
            DataFrame or list of dicts with indicator data
        """
        years = years or settings.DEFAULT_YEARS
        genders = genders or ['male', 'female', 'total']
        
        logger.info(f"Fetching data for indicator  {indicator_id}, years: {years}, genders: {genders} in fetcher.py")
        
        # Check metadata for data availability
        metadata = self.get_indicator_metadata(indicator_id)
        if metadata:
            data_range = metadata.get('range', {})
            start_year = data_range.get('start')
            end_year = data_range.get('end')
            
            if start_year and end_year:
                # Filter years to only those available
                available_years = [y for y in years if start_year <= y <= end_year]
                
                if not available_years:
                    logger.warning(f"Indicator {indicator_id} has no data for requested years {min(years)}-{max(years)}")
                    logger.info(f"Available range for indicator {indicator_id}: {start_year}-{end_year}")
                    if return_dataframe:
                        return pd.DataFrame()
                    return []
                
                if len(available_years) < len(years):
                    logger.info(f"Indicator {indicator_id}: Adjusting years from {min(years)}-{max(years)} to available {min(available_years)}-{max(available_years)}")
                    years = available_years

        # Check cache first
        if self.cache:
            cache_params = {
                'indicator_id': indicator_id,
                'region_id': self.region_id,
                'years': years,
                'genders': genders
            }
            cached_data = self.cache.get(**cache_params)
            if cached_data is not None:
                logger.info(f"Using cached data for indicator {indicator_id}")
                if return_dataframe:
                    return pd.DataFrame(cached_data)
                return cached_data
        
        # Fetch from API
        logger.info(f"Fetching data for indicator {indicator_id}, years: {min(years)}-{max(years)}, genders: {genders}")
        
        try:
            data = self.api.get_indicator_data(
                indicator_id, 
                self.region_id, 
                years, 
                genders
            )
            
            # Debug logging for empty responses
            if not data:
                logger.warning(f"API returned empty data for indicator {indicator_id}")
                logger.debug(f"  Request params: region={self.region_id}, years={years}, genders={genders}")
                # Check if it's a data availability issue
                metadata = self.get_indicator_metadata(indicator_id)
                if metadata:
                    logger.info(f"  Indicator {indicator_id} metadata says: range {metadata.get('range', {})}")
                    # Check if this indicator has gender-specific data
                    classifications = metadata.get('classifications', {})
                    if 'sex' in classifications:
                        available_genders = classifications['sex'].get('values', [])
                        logger.info(f"  Available genders in metadata: {available_genders}")
            
            # Cache the data (even if empty, to avoid repeated API calls)
            if self.cache:
                self.cache.set(
                    data,
                    indicator_id=indicator_id,
                    region_id=self.region_id,
                    years=years,
                    genders=genders
                )
                if data:
                    logger.info(f"✓ CACHED: Stored {len(data)} data points for indicator {indicator_id}")
                else:
                    logger.info(f"✓ CACHED: Stored empty result for indicator {indicator_id} (to avoid repeated API calls)")
            
            if return_dataframe:
                if data:
                    df = pd.DataFrame(data)
                    # Clean and prepare data
                    if not df.empty:
                        # Ensure we have the needed columns
                        df = self._prepare_dataframe(df)
                        logger.info(f"Retrieved {len(df)} data points for indicator {indicator_id}")
                        return df
                
                logger.warning(f"No data found for indicator {indicator_id}")
                return pd.DataFrame()
            else:
                return data
                
        except SotkanetAPIError as e:
            logger.error(f"API error fetching data for indicator {indicator_id}: {e}")
            if return_dataframe:
                return pd.DataFrame()
            return []
    
    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare and clean DataFrame.
        
        Args:
            df: Raw DataFrame from API
            
        Returns:
            Cleaned DataFrame
        """
        # Ensure we have the needed columns
        required_cols = ['year', 'value', 'gender']
        optional_cols = ['absValue', 'region', 'indicator']
        
        # Select available columns
        available_cols = [col for col in required_cols + optional_cols if col in df.columns]
        df = df[available_cols]
        
        # Drop rows with missing critical values
        df = df.dropna(subset=['year', 'value'])
        
        # Ensure correct data types
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        if 'absValue' in df.columns:
            df['absValue'] = pd.to_numeric(df['absValue'], errors='coerce')
        
        # Sort by year and gender
        sort_cols = ['year']
        if 'gender' in df.columns:
            sort_cols.append('gender')
        df = df.sort_values(sort_cols)
        
        return df
    
    def fetch_multiple_indicators(self, 
                                indicator_ids: List[int],
                                years: Optional[List[int]] = None,
                                genders: Optional[List[str]] = None,
                                return_dataframe: bool = True) -> Dict[int, Union[pd.DataFrame, List[Dict]]]:
        """
        Fetch data for multiple indicators.
        
        Args:
            indicator_ids: List of indicator IDs
            years: List of years to fetch
            genders: List of genders to fetch
            return_dataframe: If True, return DataFrames; otherwise return lists of dicts
            
        Returns:
            Dictionary mapping indicator ID to DataFrame or list of dicts
        """
        years = years or settings.DEFAULT_YEARS
        genders = genders or ['male', 'female', 'total']
        
        results = {}
        
        for ind_id in indicator_ids:
            data = self.fetch_indicator_data(ind_id, years, genders, return_dataframe)
            
            if return_dataframe:
                # Type checker knows data is DataFrame when return_dataframe=True
                if isinstance(data, pd.DataFrame) and not data.empty:
                    results[ind_id] = data
            else:
                # Type checker knows data is List when return_dataframe=False
                if isinstance(data, list) and data:
                    results[ind_id] = data
                
        logger.info(f"Fetched data for {len(results)}/{len(indicator_ids)} indicators")
        return results
    
    def fetch_indicator_by_gender(self,
                                 indicator_id: int,
                                 gender: str,
                                 years: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Fetch data for a specific gender.
        
        Args:
            indicator_id: Indicator ID
            gender: Gender to fetch ('male', 'female', or 'total')
            years: List of years
            
        Returns:
            DataFrame with data for specified gender
        """
        # Fetch all genders as list of dicts (might be cached)
        all_data = self.fetch_indicator_data(
            indicator_id, 
            years, 
            ['male', 'female', 'total'],
            return_dataframe=False  # Always get list of dicts
        )
        
        # Now all_data is guaranteed to be List[Dict]
        if isinstance(all_data, list):
            # Filter for specific gender
            gender_data = filter_data_by_gender(all_data, gender)
            
            if gender_data:
                df = pd.DataFrame(gender_data)
                return self._prepare_dataframe(df)
        
        return pd.DataFrame()
    
    def get_indicator_metadata(self, indicator_id: Union[str, int]) -> Dict:
        """
        Get metadata for an indicator.
        
        Args:
            indicator_id: Indicator ID (as string or int)
            
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
            List of dicts with 'label' and 'value' keys for UI dropdowns
        """
        options: List[Dict[str, Any]] = []
        
        for ind_id, metadata in self.metadata.items():
            title = metadata.get('title', {})
            label = title.get('fi', f"Indicator {ind_id}")
            
            # Truncate long labels
            if len(label) > 80:
                label = label[:77] + "..."
            
            options.append({
                'label': f"[{ind_id}] {label}", 
                'value': int(ind_id)  # Ensure value is int
            })
        
        # Sort by indicator ID
        options.sort(key=lambda x: x['value'])
        
        return options
    
    def get_indicator_name(self, indicator_id: Union[str, int], language: str = 'fi') -> str:
        """
        Get the name of an indicator in specified language.
        
        Args:
            indicator_id: Indicator ID
            language: Language code ('fi', 'sv', 'en')
            
        Returns:
            Indicator name or fallback
        """
        metadata = self.get_indicator_metadata(indicator_id)
        if metadata:
            title = metadata.get('title', {})
            return title.get(language, title.get('fi', f"Indicator {indicator_id}"))
        return f"Indicator {indicator_id}"
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        if self.cache:
            self.cache.clear()
            logger.info("Data cache cleared")
    
    def close(self):
        """Close API connection."""
        self.api.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for quick data fetching
def fetch_indicator_data(indicator_id: int, 
                        years: Optional[List[int]] = None,
                        genders: Optional[List[str]] = None) -> pd.DataFrame:
    fetcher = SotkanetDataFetcher()
    # Explicitly request DataFrame format
    result = fetcher.fetch_indicator_data(indicator_id, years, genders, return_dataframe=True)
    # Type assertion - we know it's a DataFrame when return_dataframe=True
    assert isinstance(result, pd.DataFrame)
    return result