"""Application configuration with environment-based settings."""

import os
import json
from pathlib import Path

# Environment configuration
ENV = os.getenv('APP_ENV', 'development')

# Indicator sets for different environments
INDICATOR_SETS = {
    'development': [
        186,   # Syntyneiden ennenaikaisuus, %
        322,   # Dementoivien muistisairauksien esiintyvyys
        5527,  # Diabetes lääkeostot
    ],
    'production': [
        186,   # Syntyneiden ennenaikaisuus, %
        322,   # Dementoivien muistisairauksien esiintyvyys
        5527,  # Diabetes lääkeostot
        5529,  # Verenpainetauti lääkeostot
        4559,  # Sepelvaltimotauti lääkeostot
        4461,  # Psykoosi lääkeostot
    ],
    'testing': [
        186,   # Single indicator for unit tests
    ],
}

# Select indicator IDs based on environment
INDICATOR_IDS = INDICATOR_SETS.get(ENV, INDICATOR_SETS['development'])

# Regional and time configuration
HUS_REGION_ID = 629
DEFAULT_YEARS = list(range(2018, 2024))
DEFAULT_LANGUAGE = 'fi'

# API settings
SOTKANET_BASE_URL = "https://sotkanet.fi/rest/1.1"
API_TIMEOUT = 30  # seconds
API_RETRY_COUNT = 3
API_RETRY_DELAY = 1  # seconds

# Cache settings
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour default
CACHE_DIR = Path(__file__).parent.parent / 'data' / 'cache'

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = Path(__file__).parent.parent / 'logs'

# Paths
METADATA_FILE = Path(__file__).parent / 'indicators_metadata.json'
VALIDATION_RESULTS_FILE = Path(__file__).parent / 'data_validation_results.json'

def load_metadata():
    """Load generated metadata if it exists."""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('indicators', {})
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load metadata: {e}")
            return {}
    return {}

# Load metadata on import
INDICATORS_METADATA = load_metadata()

def get_indicator_metadata(indicator_id):
    """Get metadata for a specific indicator."""
    return INDICATORS_METADATA.get(str(indicator_id), {})

def get_all_indicator_ids():
    """Get all configured indicator IDs for current environment."""
    return INDICATOR_IDS

def get_environment():
    """Get current environment name."""
    return ENV

def require_metadata():
    """Check if metadata has been generated."""
    if not INDICATORS_METADATA:
        raise RuntimeError(
            f"Metadata not found. Run 'python scripts/fetch_metadata.py' first.\n"
            f"Environment: {ENV}\n"
            f"Expected file: {METADATA_FILE}"
        )
    return True

# Export commonly used settings
__all__ = [
    'ENV',
    'INDICATOR_IDS',
    'HUS_REGION_ID',
    'DEFAULT_YEARS',
    'DEFAULT_LANGUAGE',
    'SOTKANET_BASE_URL',
    'API_TIMEOUT',
    'API_RETRY_COUNT',
    'API_RETRY_DELAY',
    'CACHE_ENABLED',
    'CACHE_TTL',
    'CACHE_DIR',
    'LOG_LEVEL',
    'LOG_DIR',
    'METADATA_FILE',
    'VALIDATION_RESULTS_FILE',
    'INDICATORS_METADATA',
    'get_indicator_metadata',
    'get_all_indicator_ids',
    'get_environment',
    'require_metadata',
]