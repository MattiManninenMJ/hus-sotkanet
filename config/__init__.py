"""Configuration module for the Sotkanet Health Dashboard."""

from .settings import (
    ENV,
    INDICATOR_IDS,
    HUS_REGION_ID,
    DEFAULT_YEARS,
    DEFAULT_LANGUAGE,
    SOTKANET_BASE_URL,
    API_TIMEOUT,
    API_RETRY_COUNT,
    API_RETRY_DELAY,
    CACHE_ENABLED,
    CACHE_TTL,
    CACHE_DIR,
    LOG_LEVEL,
    LOG_DIR,
)

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