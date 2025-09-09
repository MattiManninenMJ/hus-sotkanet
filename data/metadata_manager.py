"""Smart metadata management with auto-refresh capabilities."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.sotkanet_api import SotkanetAPI
from config import settings
from utils.logger import get_logger

logger = get_logger('metadata_manager')


class MetadataManager:
    """Manages indicator metadata with smart refresh logic."""
    
    def __init__(self, 
                 auto_refresh: bool = True,
                 max_age_days: int = 7,
                 fallback_to_cache: bool = True):
        """
        Initialize metadata manager.
        
        Args:
            auto_refresh: Whether to auto-refresh stale metadata
            max_age_days: Maximum age of metadata before refresh
            fallback_to_cache: Use cached metadata if API fails
        """
        self.auto_refresh = auto_refresh
        self.max_age = timedelta(days=max_age_days)
        self.fallback_to_cache = fallback_to_cache
        self.metadata_file = settings.METADATA_FILE
        self.api = None
        
    def ensure_metadata(self) -> Dict:
        """
        Ensure metadata exists and is reasonably fresh.
        
        Returns:
            Dictionary of metadata
        """
        metadata = self._load_cached_metadata()
        
        if metadata:
            # Check if metadata is for the current environment
            if not self._is_metadata_for_current_env(metadata):
                logger.warning(f"Metadata is for different environment or indicator set")
                logger.info(f"Current environment: {settings.ENV} with {len(settings.INDICATOR_IDS)} indicators")
                logger.info(f"Metadata environment: {metadata.get('environment')} with {metadata.get('indicator_count')} indicators")
                
                if self.auto_refresh:
                    logger.info("Auto-refreshing metadata due to environment change...")
                    try:
                        new_metadata = self._fetch_fresh_metadata()
                        if new_metadata:
                            self._save_metadata(new_metadata)
                            return new_metadata
                    except Exception as e:
                        logger.warning(f"Failed to refresh metadata: {e}")
                        if self.fallback_to_cache:
                            logger.info("Using cached metadata as fallback (may not match environment)")
                            return metadata
                        raise
                else:
                    logger.error(
                        f"Metadata doesn't match current environment. "
                        f"Run 'python scripts/fetch_metadata.py' to update."
                    )
                    # Return empty if not auto-refreshing and mismatch
                    return {}
            
            # Check if metadata is stale
            if self._is_metadata_stale(metadata):
                logger.info("Metadata is stale, considering refresh...")
                
                if self.auto_refresh:
                    try:
                        logger.info("Auto-refreshing metadata...")
                        new_metadata = self._fetch_fresh_metadata()
                        if new_metadata:
                            self._save_metadata(new_metadata)
                            return new_metadata
                    except Exception as e:
                        logger.warning(f"Failed to refresh metadata: {e}")
                        if self.fallback_to_cache:
                            logger.info("Using cached metadata as fallback")
                            return metadata
                        raise
                else:
                    logger.warning(
                        f"Metadata is {self._get_age_days(metadata)} days old. "
                        "Run 'python scripts/fetch_metadata.py' to update."
                    )
            else:
                logger.info(f"Using cached metadata (age: {self._get_age_days(metadata)} days)")
            
            return metadata
        else:
            # No metadata exists
            logger.warning("No metadata found")
            
            if self.auto_refresh:
                logger.info("Fetching initial metadata...")
                try:
                    metadata = self._fetch_fresh_metadata()
                    if metadata:
                        self._save_metadata(metadata)
                        return metadata
                except Exception as e:
                    logger.error(f"Failed to fetch initial metadata: {e}")
                    if not self.fallback_to_cache:
                        raise
            else:
                logger.error(
                    "No metadata available. Run 'python scripts/fetch_metadata.py' first."
                )
                
        return {}
    
    def _is_metadata_for_current_env(self, metadata: Dict) -> bool:
        """Check if metadata matches current environment and indicator set."""
        # Check environment
        if metadata.get('environment') != settings.ENV:
            return False
        
        # Check indicator IDs match
        metadata_ids = set(metadata.get('indicator_ids', []))
        current_ids = set(settings.INDICATOR_IDS)
        
        if metadata_ids != current_ids:
            logger.debug(f"Metadata IDs: {metadata_ids}")
            logger.debug(f"Current IDs: {current_ids}")
            return False
        
        # Check indicator count matches
        indicator_count = metadata.get('indicator_count', 0)
        if indicator_count != len(settings.INDICATOR_IDS):
            return False
        
        return True
    
    def _load_cached_metadata(self) -> Optional[Dict]:
        """Load metadata from cache file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded metadata from {self.metadata_file}")
                    return data
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        return None
    
    def _is_metadata_stale(self, metadata: Dict) -> bool:
        """Check if metadata is older than max_age."""
        generated_at = metadata.get('generated_at')
        if not generated_at:
            return True
            
        try:
            generated_date = datetime.fromisoformat(generated_at)
            age = datetime.now() - generated_date
            return age > self.max_age
        except:
            return True
    
    def _get_age_days(self, metadata: Dict) -> int:
        """Get age of metadata in days."""
        generated_at = metadata.get('generated_at')
        if not generated_at:
            return -1
            
        try:
            generated_date = datetime.fromisoformat(generated_at)
            age = datetime.now() - generated_date
            return age.days
        except:
            return -1
    
    def _fetch_fresh_metadata(self) -> Dict:
        """Fetch fresh metadata from API."""
        if not self.api:
            self.api = SotkanetAPI()
            
        indicator_ids = settings.INDICATOR_IDS
        logger.info(f"Fetching metadata for {len(indicator_ids)} indicators in {settings.ENV} environment")
        
        metadata = self.api.get_all_metadata(indicator_ids)
        
        return {
            'generated_at': datetime.now().isoformat(),
            'environment': settings.ENV,
            'source': 'Sotkanet REST API',
            'indicator_ids': indicator_ids,
            'indicator_count': len(metadata),
            'indicators': metadata
        }
    
    def _save_metadata(self, metadata: Dict):
        """Save metadata to file."""
        self.metadata_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved metadata to {self.metadata_file}")
        
        # Also update the settings to reload metadata
        import importlib
        importlib.reload(settings)
    
    def force_refresh(self) -> Dict:
        """Force refresh metadata regardless of age."""
        logger.info("Forcing metadata refresh...")
        metadata = self._fetch_fresh_metadata()
        self._save_metadata(metadata)
        return metadata
    
    def get_metadata_status(self) -> Dict:
        """Get status information about metadata."""
        metadata = self._load_cached_metadata()
        
        if not metadata:
            return {
                'exists': False,
                'age_days': None,
                'is_stale': True,
                'matches_environment': False,
                'indicator_count': 0,
                'environment': None
            }
        
        return {
            'exists': True,
            'age_days': self._get_age_days(metadata),
            'is_stale': self._is_metadata_stale(metadata),
            'matches_environment': self._is_metadata_for_current_env(metadata),
            'indicator_count': metadata.get('indicator_count', 0),
            'environment': metadata.get('environment'),
            'generated_at': metadata.get('generated_at')
        }


# Singleton instance
_manager_instance = None

def get_metadata_manager(auto_refresh: bool = False) -> MetadataManager:
    """
    Get singleton metadata manager.
    
    Args:
        auto_refresh: Whether to enable auto-refresh (default: False for production)
    """
    global _manager_instance
    if _manager_instance is None:
        # Use setting from environment if available
        auto_refresh = auto_refresh or settings.METADATA_AUTO_REFRESH
        _manager_instance = MetadataManager(
            auto_refresh=auto_refresh,
            max_age_days=settings.METADATA_MAX_AGE_DAYS
        )
    return _manager_instance


def ensure_metadata_exists() -> bool:
    """
    Quick check to ensure metadata exists.
    
    Returns:
        True if metadata is available
    """
    manager = get_metadata_manager()
    metadata = manager.ensure_metadata()
    return bool(metadata and metadata.get('indicators'))