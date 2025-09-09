"""Sotkanet API module."""

from .sotkanet_api import (
    SotkanetAPI,
    fetch_indicator,
    fetch_latest,
    fetch_all_indicators
)

__all__ = [
    'SotkanetAPI',
    'fetch_indicator',
    'fetch_latest',
    'fetch_all_indicators'
]