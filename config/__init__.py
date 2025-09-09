"""Configuration package for Sotkanet Health Dashboard."""

from pathlib import Path
import json

# Package directory
CONFIG_DIR = Path(__file__).parent

# Load settings
from .settings import (
    HUS_REGION_ID,
    DEFAULT_YEARS,
    DEFAULT_LANGUAGE,
    SOTKANET_BASE_URL,
    INDICATORS
)

# Try to load indicators if the file exists
try:
    from .indicators import INDICATORS as INDICATORS_METADATA, get_indicator_by_id, get_all_ids
except ImportError:
    INDICATORS_METADATA = {}
    def get_indicator_by_id(indicator_id):
        return {}
    def get_all_ids():
        return []

__all__ = [
    'HUS_REGION_ID',
    'DEFAULT_YEARS',
    'DEFAULT_LANGUAGE',
    'SOTKANET_BASE_URL',
    'INDICATORS',
    'INDICATORS_METADATA',
    'get_indicator_by_id',
    'get_all_ids',
    'CONFIG_DIR'
]