"""API module for Sotkanet data access."""

from .sotkanet_api import (
    SotkanetAPI,
    SotkanetAPIError,
    get_api,
    fetch_indicator_metadata,
    fetch_indicator_data,
    fetch_all_metadata,
    validate_data_availability,
    filter_data_by_gender,
    filter_data_by_year,
    filter_data_by_years,
)

__all__ = [
    'SotkanetAPI',
    'SotkanetAPIError',
    'get_api',
    'fetch_indicator_metadata',
    'fetch_indicator_data',
    'fetch_all_metadata',
    'validate_data_availability',
    'filter_data_by_gender',
    'filter_data_by_year',
    'filter_data_by_years',
]