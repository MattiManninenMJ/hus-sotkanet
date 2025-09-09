"""Application configuration."""

import json
from pathlib import Path

# Load indicators metadata
INDICATORS_METADATA_PATH = Path(__file__).parent / "indicators_metadata.json"

if INDICATORS_METADATA_PATH.exists():
    with open(INDICATORS_METADATA_PATH, 'r') as f:
        INDICATORS_DATA = json.load(f)
        INDICATORS = INDICATORS_DATA.get('indicators', {})
else:
    print("Warning: Indicators metadata not found. Run scripts/fetch_metadata.py first.")
    INDICATORS = {}

# Fixed configuration
HUS_REGION_ID = 629
DEFAULT_YEARS = list(range(2018, 2024))
DEFAULT_LANGUAGE = 'fi'

# API settings
SOTKANET_BASE_URL = "https://sotkanet.fi/rest/1.1"
