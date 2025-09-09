#!/usr/bin/env python3
"""
Validate that indicators have data for HUS region and specified years.
Usage: python scripts/validate_data.py
"""

import json
import requests
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('data_validator')

class DataValidator:
    """Validate data availability for indicators."""
    
    BASE_URL = "https://sotkanet.fi/rest/1.1"
    HUS_REGION_ID = 629
    DEFAULT_YEARS = list(range(2018, 2024))
    
    def __init__(self, years: Optional[List[int]] = None):
        """Initialize validator."""
        self.years = years or self.DEFAULT_YEARS
        
    def check_indicator_data(self, indicator_id: int) -> Dict:
        """Check if indicator has data for HUS region in specified years."""
        
        # Build URL with repeated year parameters
        year_params = "&".join([f"years={year}" for year in self.years])
        url = f"{self.BASE_URL}/json?indicator={indicator_id}&{year_params}&genders=total&regions={self.HUS_REGION_ID}"
        
        logger.info(f"Checking data for indicator {indicator_id}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Filter for HUS region only (API might return other regions)
            hus_data = [item for item in data if item.get('region') == self.HUS_REGION_ID]
            
            # Extract available years
            available_years = sorted(set(item['year'] for item in hus_data if item.get('year')))
            missing_years = sorted(set(self.years) - set(available_years))
            
            # Get sample values
            sample_values = {}
            for item in hus_data[:3]:  # First 3 data points as sample
                year = item.get('year')
                if year:
                    sample_values[year] = {
                        'value': item.get('value'),
                        'absValue': item.get('absValue')
                    }
            
            result = {
                'indicator_id': indicator_id,
                'has_data': len(available_years) > 0,
                'requested_years': self.years,
                'available_years': available_years,
                'missing_years': missing_years,
                'data_points': len(hus_data),
                'completeness': len(available_years) / len(self.years) * 100 if self.years else 0,
                'sample_values': sample_values,
                'status': 'OK' if len(available_years) > 0 else 'NO_DATA'
            }
            
            # Log result
            if result['has_data']:
                logger.info(f"  ✓ Data available: {len(available_years)}/{len(self.years)} years ({result['completeness']:.1f}%)")
            else:
                logger.warning(f"  ✗ No data available for HUS region")
            
            if missing_years:
                logger.warning(f"  ⚠ Missing years: {missing_years}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  ✗ Error fetching data: {e}")
            return {
                'indicator_id': indicator_id,
                'has_data': False,
                'error': str(e),
                'status': 'ERROR'
            }
    
    def validate_multiple(self, indicator_ids: List[int]) -> Dict:
        """Validate multiple indicators."""
        results = {}
        
        for ind_id in indicator_ids:
            results[str(ind_id)] = self.check_indicator_data(ind_id)
        
        return results

def validate_indicators(indicator_ids: List[int], years: Optional[List[int]] = None) -> Dict:
    """
    Validate indicators data availability.
    
    Args:
        indicator_ids: List of indicator IDs to validate
        years: List of years to check (default: 2018-2023)
    
    Returns:
        Dictionary with validation results for each indicator
    """
    validator = DataValidator(years)
    return validator.validate_multiple(indicator_ids)

def load_metadata_and_validate():
    """Load indicators from metadata and validate them."""
    metadata_path = Path("config/indicators_metadata.json")
    
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        logger.info("Run scripts/fetch_metadata.py first")
        return None
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Extract indicator IDs
    indicator_ids = [int(ind_id) for ind_id in metadata['indicators'].keys()]
    
    logger.info(f"Validating {len(indicator_ids)} indicators for HUS region")
    logger.info(f"Years: {DataValidator.DEFAULT_YEARS}")
    logger.info("="*60)
    
    # Validate all indicators
    results = validate_indicators(indicator_ids)
    
    # Generate summary
    summary = {
        'total_indicators': len(results),
        'with_data': sum(1 for r in results.values() if r['has_data']),
        'without_data': sum(1 for r in results.values() if not r['has_data']),
        'complete_data': sum(1 for r in results.values() if r.get('completeness', 0) == 100),
        'partial_data': sum(1 for r in results.values() if 0 < r.get('completeness', 0) < 100),
        'validation_timestamp': datetime.now().isoformat(),
        'region_id': DataValidator.HUS_REGION_ID,
        'years_checked': DataValidator.DEFAULT_YEARS,
        'indicators': results
    }
    
    # Add indicator names to results
    for ind_id, result in results.items():
        if ind_id in metadata['indicators']:
            result['name'] = metadata['indicators'][ind_id].get('title', {}).get('fi', 'Unknown')
    
    return summary

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Sotkanet indicator data availability')
    parser.add_argument(
        '--ids',
        nargs='+',
        type=int,
        help='Specific indicator IDs to validate'
    )
    parser.add_argument(
        '--years',
        nargs='+',
        type=int,
        help='Years to check (default: 2018-2023)'
    )
    parser.add_argument(
        '--output',
        default='config/data_validation_results.json',
        help='Output file for validation results'
    )
    
    args = parser.parse_args()
    
    if args.ids:
        # Validate specific indicators
        logger.info(f"Validating indicators: {args.ids}")
        results = validate_indicators(args.ids, args.years)
        summary = {
            'validation_timestamp': datetime.now().isoformat(),
            'indicators_checked': args.ids,
            'results': results
        }
    else:
        # Validate all indicators from metadata
        summary = load_metadata_and_validate()
    
    if summary:
        # Save results
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        if 'total_indicators' in summary:
            print(f"Total indicators: {summary['total_indicators']}")
            print(f"With data: {summary['with_data']}")
            print(f"Without data: {summary['without_data']}")
            print(f"Complete data: {summary['complete_data']}")
            print(f"Partial data: {summary['partial_data']}")
        
        print(f"\n✓ Results saved to: {output_path}")
        
        # Print indicators with issues
        if 'indicators' in summary:
            issues = [
                (ind_id, result) 
                for ind_id, result in summary['indicators'].items() 
                if not result['has_data'] or result.get('completeness', 0) < 100
            ]
            
            if issues:
                print("\n" + "="*60)
                print("INDICATORS WITH ISSUES")
                print("="*60)
                for ind_id, result in issues:
                    name = result.get('name', 'Unknown')
                    print(f"\n[{ind_id}] {name[:50]}")
                    if not result['has_data']:
                        print("  ✗ No data available")
                    elif result.get('missing_years'):
                        print(f"  ⚠ Missing years: {result['missing_years']}")

if __name__ == "__main__":
    main()