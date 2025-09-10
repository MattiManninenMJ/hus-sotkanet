"""Application configuration with environment-based settings."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Environment configuration
ENV = os.getenv('APP_ENV', 'development')


# Indicator sets for different environments
INDICATOR_SETS = {
    'development': [
        186,   # Mortality per 100 000
        322,   # Mortality 65+
        5527,  # Physical activity
    ],
    'production': [
        186,   # Mortality per 100 000
        322,   # Mortality 65+
        5527,  # Physical activity
        5529,  # Additional indicator
        4559,  # Additional indicator
        4461,  # Additional indicator
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
SOTKANET_BASE_URL = os.getenv('SOTKANET_BASE_URL', 'https://sotkanet.fi/rest/1.1')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
API_RETRY_COUNT = int(os.getenv('API_RETRY_COUNT', '3'))
API_RETRY_DELAY = int(os.getenv('API_RETRY_DELAY', '1'))

# Cache settings
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))
CACHE_DIR = Path(__file__).parent.parent / 'data' / 'cache'

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = Path(__file__).parent.parent / 'logs'

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
]