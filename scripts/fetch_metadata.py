#!/usr/bin/env python3
"""
Fetch indicator metadata from Sotkanet API based on ID list.
Usage: python scripts/fetch_metadata.py
"""

import json
import requests
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('metadata_fetcher')

class MetadataFetcher:
    """Fetch and process indicator metadata from Sotkanet API."""
    
    BASE_URL = "https://sotkanet.fi/rest/1.1"
    
    def __init__(self, ids_file: str = ""):
        """Initialize the metadata fetcher."""
        if ids_file == "":
            # Look for the file relative to project root
            project_root = Path(__file__).parent.parent
            
            # Try different possible locations
            possible_files = [
                project_root / "config" / "indicator_ids.txt",
                project_root / "config" / "indicator_ids.json",
                Path("config/indicator_ids.txt"),
                Path("config/indicator_ids.json"),
            ]
            
            for possible_file in possible_files:
                if possible_file.exists():
                    self.ids_file = possible_file
                    logger.info(f"Found IDs file: {self.ids_file}")
                    break
            else:
                raise FileNotFoundError(
                    f"No indicator IDs file found. Tried:\n" + 
                    "\n".join(f"  - {f}" for f in possible_files) +
                    f"\n\nCurrent directory: {Path.cwd()}" +
                    f"\nProject root: {project_root}"
                )
        else:
            self.ids_file = Path(ids_file)
            
            if not self.ids_file.is_absolute() and not self.ids_file.exists():
                project_root = Path(__file__).parent.parent
                self.ids_file = project_root / self.ids_file
        
        if not self.ids_file.exists():
            raise FileNotFoundError(
                f"IDs file not found: {self.ids_file}\n"
                f"Current directory: {Path.cwd()}"
            )
        
        self.indicator_ids = self._load_ids()
        logger.info(f"Loaded {len(self.indicator_ids)} indicator IDs")
        
        # Setup session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'fi-FI,fi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://sotkanet.fi/',
            'Origin': 'https://sotkanet.fi'
        })
    
    def _load_ids(self) -> List[int]:
        """Load indicator IDs from file."""
        logger.info(f"Loading IDs from: {self.ids_file}")
        
        if self.ids_file.suffix == '.json':
            with open(self.ids_file, 'r') as f:
                return json.load(f)
        else:  # Assume text file with one ID per line
            with open(self.ids_file, 'r') as f:
                ids = []
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            ids.append(int(line))
                        except ValueError:
                            logger.warning(f"Skipping invalid ID on line {line_num}: {line}")
                return ids

    def fetch_indicator_metadata(self, indicator_id: int) -> Dict:
        """Fetch metadata for a single indicator from API."""
        url = f"{self.BASE_URL}/indicators/{indicator_id}"
        
        logger.info(f"Fetching metadata for indicator {indicator_id}")
        
        try:
            # Try the direct metadata endpoint first
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 403:
                # If forbidden, try alternative approach using data endpoint
                logger.warning(f"Metadata endpoint forbidden for {indicator_id}, trying data endpoint")
                return self.fetch_metadata_from_data_endpoint(indicator_id)
            
            response.raise_for_status()
            data = response.json()
            
            # Add our ID
            data['indicator_id'] = indicator_id
            
            logger.info(f"✓ Fetched: {data.get('title', {}).get('fi', 'Unknown')[:50]}...")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Failed to fetch indicator {indicator_id}: {e}")
            # Try alternative method
            return self.fetch_metadata_from_data_endpoint(indicator_id)
    
    def fetch_metadata_from_data_endpoint(self, indicator_id: int) -> Dict:
        """Fetch metadata using the data endpoint as fallback."""
        try:
            # First, get basic info from a data query
            url = f"{self.BASE_URL}/json"
            params = {
                'indicator': indicator_id,
                'years': 2023,
                'genders': 'total'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                # Extract metadata from the first result
                first_result = data[0]
                
                # Try to get indicator title from another endpoint
                title_info = self._fetch_indicator_title(indicator_id)
                
                metadata = {
                    'indicator_id': indicator_id,
                    'id': indicator_id,
                    'title': title_info.get('title', {
                        'fi': first_result.get('indicator', {}).get('title', f'Indicator {indicator_id}'),
                        'sv': '',
                        'en': ''
                    }),
                    'organization': title_info.get('organization', {
                        'title': {'fi': 'Unknown', 'sv': '', 'en': ''}
                    }),
                    'decimals': 1,
                    'data-updated': datetime.now().strftime('%Y-%m-%d'),
                    'unit': self._extract_unit_from_title(
                        title_info.get('title', {}).get('fi', '')
                    )
                }
                
                logger.info(f"✓ Fetched via data endpoint: {metadata['title']['fi'][:50]}...")
                return metadata
            else:
                logger.warning(f"No data available for indicator {indicator_id}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to fetch via data endpoint for {indicator_id}: {e}")
            return {}
    
    def _fetch_indicator_title(self, indicator_id: int) -> Dict:
        """Try to fetch indicator title from various sources."""
        # Known indicator titles (fallback data)
        known_indicators = {
            186: {'title': {'fi': 'Yleinen kuolleisuus', 'sv': 'Allmän dödlighet', 'en': 'General mortality'}},
            322: {'title': {'fi': 'Liikunnan harrastaminen vapaa-ajalla', 'sv': 'Motion på fritiden', 'en': 'Physical activity in leisure time'}},
            5527: {'title': {'fi': 'Kaatumisiin ja putoamisiin liittyvät hoitojaksot 65 vuotta täyttäneillä', 'sv': 'Vårdperioder relaterade till fall', 'en': 'Fall-related hospital periods'}},
            5529: {'title': {'fi': 'Päivittäin tupakoivat', 'sv': 'Dagliga rökare', 'en': 'Daily smokers'}},
            4559: {'title': {'fi': 'Alkoholijuomien myynti asukasta kohti 100 %:n alkoholina', 'sv': 'Försäljning av alkoholdrycker', 'en': 'Alcohol sales per capita'}},
            4461: {'title': {'fi': 'Mielenterveyden ja käyttäytymisen häiriöiden vuoksi työkyvyttömyyseläkettä saavat', 'sv': 'Sjukpension för psykiska störningar', 'en': 'Disability pension for mental disorders'}}
        }
        
        if indicator_id in known_indicators:
            return known_indicators[indicator_id]
        
        # Try to fetch from regions endpoint which sometimes has titles
        try:
            url = f"{self.BASE_URL}/regions"
            response = self.session.get(url, timeout=5)
            # This is just a placeholder - adapt based on actual API
            return {'title': {'fi': f'Indicator {indicator_id}', 'sv': '', 'en': ''}}
        except:
            return {'title': {'fi': f'Indicator {indicator_id}', 'sv': '', 'en': ''}}
    
    def _extract_unit_from_title(self, title: str) -> str:
        """Extract unit from indicator title."""
        if '/ 100 000' in title:
            return '/ 100 000'
        elif '/ 10 000' in title:
            return '/ 10 000'
        elif '/ 1 000' in title or '/ 1000' in title:
            return '/ 1 000'
        elif '%' in title:
            return '%'
        elif '100 %:n alkoholina' in title:
            return 'litraa / asukas'
        return ''
    
    def fetch_all_metadata(self) -> Dict:
        """Fetch metadata for all indicator IDs."""
        metadata = {}
        
        for indicator_id in self.indicator_ids:
            data = self.fetch_indicator_metadata(indicator_id)
            if data:
                metadata[str(indicator_id)] = data
            else:
                logger.warning(f"Skipping indicator {indicator_id} due to fetch error")
        
        return metadata
    
    def save_metadata(self, output_path: str = "{project_root}/config/indicators_metadata.json"):
        """Save fetched metadata to JSON file."""
        metadata = self.fetch_all_metadata()
        
        # Add meta-information
        output = {
            'generated_at': datetime.now().isoformat(),
            'source': 'Sotkanet REST API',
            'ids_file': str(self.ids_file),
            'indicator_count': len(metadata),
            'indicators': metadata
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ Metadata saved to {output_file}")
        
        # Generate Python module for easy import
        self._generate_python_module(metadata)
        
        # Print summary
        self._print_summary(metadata)
        
        return metadata
    
    def _generate_python_module(self, metadata: Dict):
        """Generate Python module with indicator definitions."""
        # Ensure path is relative to project root, not script location
        project_root = Path(__file__).parent.parent
        output_path = project_root / "config" / "indicators.py"
        
        lines = [
            '"""',
            'Auto-generated indicator definitions from Sotkanet API.',
            f'Generated: {datetime.now().isoformat()}',
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
            
            unit = data.get('unit', self._extract_unit_from_title(title.get('fi', '')))
            lines.append(f"        'unit': {repr(unit)},")
            
            lines.append(f"        'organization': {repr(data.get('organization', {}).get('title', {}).get('fi', ''))},")
            lines.append(f"        'decimals': {data.get('decimals', 1)},")
            lines.append(f"        'last_updated': {repr(data.get('data-updated', ''))}")
            lines.append("    },")
        
        lines.append("}")
        lines.append("")
        lines.append("# Helper functions")
        lines.append("def get_indicator_by_id(indicator_id):")
        lines.append('    """Get indicator metadata by ID."""')
        lines.append("    return INDICATORS.get(indicator_id, {})")
        lines.append("")
        lines.append("def get_all_ids():")
        lines.append('    """Get list of all indicator IDs."""')
        lines.append("    return list(INDICATORS.keys())")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"✓ Python module generated at {output_path}")
    
    def _print_summary(self, metadata: Dict):
        """Print summary of fetched indicators."""
        print("\n" + "="*60)
        print("INDICATOR SUMMARY")
        print("="*60)
        
        for ind_id, data in metadata.items():
            title = data.get('title', {})
            print(f"\n[{ind_id}]")
            print(f"  FI: {title.get('fi', 'N/A')[:60]}")
            print(f"  EN: {title.get('en', 'N/A')[:60]}")
            print(f"  Updated: {data.get('data-updated', 'N/A')}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch Sotkanet indicator metadata')
    parser.add_argument(
        '--ids', 
        default='../config/indicator_ids.txt',
        help='Path to file containing indicator IDs'
    )
    parser.add_argument(
        '--output',
        default='../config/indicators_metadata.json',
        help='Path to output JSON file'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Also validate data availability for HUS region'
    )
    
    args = parser.parse_args()
    
    # Fetch metadata
    fetcher = MetadataFetcher(args.ids)
    metadata = fetcher.save_metadata(args.output)
    
    # Optionally validate data availability
    if args.validate:
        print("\n" + "="*60)
        print("VALIDATING DATA AVAILABILITY FOR HUS REGION")
        print("="*60)
        from validate_data import validate_indicators
        validate_indicators(list(metadata.keys()))
    
    print("\n✓ Complete!")

if __name__ == "__main__":
    main()