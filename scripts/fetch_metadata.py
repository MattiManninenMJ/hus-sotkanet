#!/usr/bin/env python3
"""
Fetch indicator metadata from Sotkanet API based on configured indicators.
Usage: python scripts/fetch_metadata.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE importing settings
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from api.sotkanet_api import SotkanetAPI, SotkanetAPIError
from utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('metadata_fetcher')


class MetadataFetcher:
    """Fetch and process indicator metadata using the API layer."""
    
    def __init__(self):
        """Initialize the metadata fetcher."""
        self.api = SotkanetAPI()
        self.indicator_ids = settings.INDICATOR_IDS
        
        logger.info(f"Environment: {settings.ENV}")
        logger.info(f"Loaded {len(self.indicator_ids)} indicator IDs from settings")
        logger.info(f"Indicators: {self.indicator_ids}")
    
    def fetch_all_metadata(self) -> Dict:
        """Fetch metadata for all configured indicators."""
        logger.info("="*60)
        logger.info("FETCHING METADATA")
        logger.info("="*60)
        
        metadata = self.api.get_all_metadata(self.indicator_ids)
        
        logger.info(f"Successfully fetched metadata for {len(metadata)} indicators")
        return metadata
    
    def save_metadata(self, metadata: Dict, output_path: Path = None):
        """Save fetched metadata to JSON file."""
        output_path = output_path or settings.METADATA_FILE
        
        # Add meta-information
        output = {
            'generated_at': datetime.now().isoformat(),
            'environment': settings.ENV,
            'source': 'Sotkanet REST API',
            'indicator_ids': self.indicator_ids,
            'indicator_count': len(metadata),
            'indicators': metadata
        }
        
        # Ensure output directory exists
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ Metadata saved to {output_path}")
        
        # Generate Python module for backwards compatibility
        self._generate_python_module(metadata)
        
        return output
    
    def _generate_python_module(self, metadata: Dict):
        """Generate Python module with indicator definitions."""
        # Use absolute path relative to project root
        project_root = Path(__file__).parent.parent
        output_path = project_root / "config" / "indicators.py"
        
        lines = [
            '"""',
            'Auto-generated indicator definitions from Sotkanet API.',
            f'Generated: {datetime.now().isoformat()}',
            f'Environment: {settings.ENV}',
            '"""',
            '',
            'INDICATORS = {'
        ]
        
        for ind_id, data in metadata.items():
            title = data.get('title', {})
            lines.append(f"    {ind_id}: {{")
            lines.append(f"        'id': {ind_id},")
            lines.append(f"        'name_fi': {repr(title.get('fi', ''))},")
            lines.append(f"        'name_sv': {repr(title.get('sv', ''))},")
            lines.append(f"        'name_en': {repr(title.get('en', ''))},")
            
            # Extract unit
            unit = self._extract_unit(data)
            lines.append(f"        'unit': {repr(unit)},")
            
            # Add other useful fields
            org = data.get('organization', {}).get('title', {}).get('fi', '')
            lines.append(f"        'organization': {repr(org)},")
            lines.append(f"        'decimals': {data.get('decimals', 1)},")
            lines.append(f"        'last_updated': {repr(data.get('data-updated', ''))}")
            lines.append("    },")
        
        lines.extend([
            "}",
            "",
            "# Helper functions",
            "def get_indicator_by_id(indicator_id):",
            '    """Get indicator metadata by ID."""',
            "    return INDICATORS.get(indicator_id, {})",
            "",
            "def get_all_ids():",
            '    """Get list of all indicator IDs."""',
            "    return list(INDICATORS.keys())"
        ])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"✓ Python module generated at {output_path}")
    
    def _extract_unit(self, data: Dict) -> str:
        """Try to extract unit from indicator data."""
        # Check if there's a unit field
        if 'unit' in data:
            unit = data['unit']
            if isinstance(unit, dict):
                return unit.get('fi', '')
            return str(unit)
        
        # Try to extract from title
        title = data.get('title', {}).get('fi', '')
        if '/ 100 000' in title:
            return '/ 100 000'
        elif '/ 1 000' in title:
            return '/ 1 000'
        elif '%' in title:
            return '%'
        
        return ''
    
    def print_summary(self, metadata: Dict):
        """Print summary of fetched indicators."""
        print("\n" + "="*60)
        print("METADATA SUMMARY")
        print("="*60)
        print(f"Environment: {settings.ENV}")
        print(f"Total indicators: {len(metadata)}")
        print("\nIndicators:")
        
        for ind_id, data in metadata.items():
            title = data.get('title', {})
            print(f"\n[{ind_id}]")
            print(f"  FI: {title.get('fi', 'N/A')[:60]}")
            print(f"  EN: {title.get('en', 'N/A')[:60]}")
            print(f"  Updated: {data.get('data-updated', 'N/A')}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fetch Sotkanet indicator metadata'
    )
    parser.add_argument(
        '--env',
        choices=['development', 'production', 'testing'],
        help='Override environment (default: from .env file or APP_ENV)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (default: from settings)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Also validate data availability for HUS region'
    )
    
    args = parser.parse_args()
    
    # Override environment if specified via command line
    if args.env:
        import os
        os.environ['APP_ENV'] = args.env
        # Reload settings to pick up new environment
        import importlib
        importlib.reload(settings)
        logger.info(f"Overriding environment to: {args.env}")
    
    # Log current configuration
    logger.info(f"Using environment: {settings.ENV}")
    logger.info(f"Expected indicators: {settings.INDICATOR_IDS}")
    
    # Fetch metadata
    fetcher = MetadataFetcher()
    metadata = fetcher.fetch_all_metadata()
    
    if metadata:
        # Save metadata
        output_data = fetcher.save_metadata(metadata, args.output)
        
        # Print summary
        fetcher.print_summary(metadata)
        
        # Optionally validate data availability
        if args.validate:
            print("\n" + "="*60)
            print("VALIDATING DATA AVAILABILITY")
            print("="*60)
            
            # Use the existing API instance from the fetcher
            validation_results = {}
            
            for ind_id in fetcher.indicator_ids:
                result = fetcher.api.validate_data_availability(ind_id)
                validation_results[ind_id] = result
                
                if result['has_data']:
                    completeness = result['completeness']
                    print(f"✓ [{ind_id}] {completeness:.0f}% complete")
                else:
                    print(f"✗ [{ind_id}] No data available")
            
            # Save validation results
            validation_output = {
                'validated_at': datetime.now().isoformat(),
                'environment': settings.ENV,
                'region_id': settings.HUS_REGION_ID,
                'years': settings.DEFAULT_YEARS,
                'results': validation_results
            }
            
            with open(settings.VALIDATION_RESULTS_FILE, 'w') as f:
                json.dump(validation_output, f, indent=2)
            
            print(f"\n✓ Validation results saved to {settings.VALIDATION_RESULTS_FILE}")
        
        print("\n✓ Complete!")
    else:
        logger.error("Failed to fetch metadata")
        sys.exit(1)


if __name__ == "__main__":
    main()