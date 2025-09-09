"""
Auto-generated indicator definitions from Sotkanet API.
Generated: 2025-09-09T10:10:05.541973
"""

INDICATORS = {
}

# Helper functions
def get_indicator_by_id(indicator_id):
    """Get indicator metadata by ID."""
    return INDICATORS.get(indicator_id, {})

def get_all_ids():
    """Get list of all indicator IDs."""
    return list(INDICATORS.keys())