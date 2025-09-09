"""Data processing and statistics module."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger('data.processor')


class DataProcessor:
    """Handles data processing and statistical calculations."""
    
    @staticmethod
    def calculate_statistics(df: pd.DataFrame) -> Dict:
        """
        Calculate statistics for indicator data.
        
        Args:
            df: DataFrame with 'year' and 'value' columns
            
        Returns:
            Dictionary with calculated statistics
        """
        if df.empty:
            return {
                'latest_value': None,
                'latest_year': None,
                'min_value': None,
                'max_value': None,
                'mean_value': None,
                'median_value': None,
                'std_value': None,
                'trend': None,
                'trend_pct': None,
                'data_points': 0
            }
        
        stats = {
            'latest_value': df.iloc[-1]['value'],
            'latest_year': int(df.iloc[-1]['year']),
            'min_value': df['value'].min(),
            'max_value': df['value'].max(),
            'mean_value': df['value'].mean(),
            'median_value': df['value'].median(),
            'std_value': df['value'].std(),
            'data_points': len(df)
        }
        
        # Calculate trend
        if len(df) > 1:
            change = df.iloc[-1]['value'] - df.iloc[-2]['value']
            change_pct = (change / df.iloc[-2]['value'] * 100) if df.iloc[-2]['value'] != 0 else 0
            stats['trend'] = change
            stats['trend_pct'] = change_pct
        else:
            stats['trend'] = None
            stats['trend_pct'] = None
            
        logger.debug(f"Calculated statistics for {len(df)} data points")
        return stats
    
    @staticmethod
    def calculate_growth_rate(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate year-over-year growth rate.
        
        Args:
            df: DataFrame with 'year' and 'value' columns
            
        Returns:
            DataFrame with added 'growth_rate' column
        """
        if df.empty or len(df) < 2:
            return df
            
        df = df.copy()
        df['growth_rate'] = df['value'].pct_change() * 100
        
        logger.debug(f"Calculated growth rates for {len(df)} data points")
        return df
    
    @staticmethod
    def calculate_moving_average(df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
        """
        Calculate moving average.
        
        Args:
            df: DataFrame with 'year' and 'value' columns
            window: Window size for moving average
            
        Returns:
            DataFrame with added 'moving_avg' column
        """
        if df.empty:
            return df
            
        df = df.copy()
        df['moving_avg'] = df['value'].rolling(window=window, center=True).mean()
        
        logger.debug(f"Calculated {window}-year moving average for {len(df)} data points")
        return df
    
    @staticmethod
    def normalize_data(df: pd.DataFrame, method: str = 'minmax') -> pd.DataFrame:
        """
        Normalize data values.
        
        Args:
            df: DataFrame with 'value' column
            method: Normalization method ('minmax' or 'zscore')
            
        Returns:
            DataFrame with added 'normalized_value' column
        """
        if df.empty:
            return df
            
        df = df.copy()
        
        if method == 'minmax':
            min_val = df['value'].min()
            max_val = df['value'].max()
            if max_val != min_val:
                df['normalized_value'] = (df['value'] - min_val) / (max_val - min_val)
            else:
                df['normalized_value'] = 0.5
        elif method == 'zscore':
            mean_val = df['value'].mean()
            std_val = df['value'].std()
            if std_val != 0:
                df['normalized_value'] = (df['value'] - mean_val) / std_val
            else:
                df['normalized_value'] = 0
                
        logger.debug(f"Normalized {len(df)} data points using {method} method")
        return df
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, method: str = 'iqr') -> pd.DataFrame:
        """
        Detect outliers in the data.
        
        Args:
            df: DataFrame with 'value' column
            method: Detection method ('iqr' or 'zscore')
            
        Returns:
            DataFrame with added 'is_outlier' column
        """
        if df.empty:
            return df
            
        df = df.copy()
        
        if method == 'iqr':
            Q1 = df['value'].quantile(0.25)
            Q3 = df['value'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df['is_outlier'] = (df['value'] < lower_bound) | (df['value'] > upper_bound)
        elif method == 'zscore':
            z_scores = np.abs((df['value'] - df['value'].mean()) / df['value'].std())
            df['is_outlier'] = z_scores > 3
            
        outlier_count = df['is_outlier'].sum()
        if outlier_count > 0:
            logger.info(f"Detected {outlier_count} outliers using {method} method")
            
        return df
    
    @staticmethod
    def compare_indicators(dfs: Dict[int, pd.DataFrame], 
                         normalize: bool = True) -> pd.DataFrame:
        """
        Compare multiple indicators.
        
        Args:
            dfs: Dictionary mapping indicator ID to DataFrame
            normalize: Whether to normalize values for comparison
            
        Returns:
            Combined DataFrame for comparison
        """
        if not dfs:
            return pd.DataFrame()
            
        combined_dfs = []
        
        for ind_id, df in dfs.items():
            df = df.copy()
            
            if normalize:
                df = DataProcessor.normalize_data(df)
                df['indicator_id'] = ind_id
                df = df[['year', 'normalized_value', 'indicator_id']]
                df.rename(columns={'normalized_value': 'value'}, inplace=True)
            else:
                df['indicator_id'] = ind_id
                df = df[['year', 'value', 'indicator_id']]
                
            combined_dfs.append(df)
            
        result = pd.concat(combined_dfs, ignore_index=True)
        
        logger.info(f"Combined {len(dfs)} indicators for comparison")
        return result
    
    @staticmethod
    def aggregate_by_period(df: pd.DataFrame, 
                          period: str = 'yearly') -> pd.DataFrame:
        """
        Aggregate data by time period.
        
        Args:
            df: DataFrame with 'year' and 'value' columns
            period: Aggregation period ('yearly', '3year', '5year')
            
        Returns:
            Aggregated DataFrame
        """
        if df.empty:
            return df
            
        df = df.copy()
        
        if period == 'yearly':
            return df
        elif period == '3year':
            window = 3
        elif period == '5year':
            window = 5
        else:
            logger.warning(f"Unknown period: {period}, using yearly")
            return df
            
        # Create period groups
        df['period'] = (df['year'] // window) * window
        
        # Aggregate by period
        result = df.groupby('period').agg({
            'value': 'mean',
            'absValue': 'sum'
        }).reset_index()
        
        result.rename(columns={'period': 'year'}, inplace=True)
        
        logger.debug(f"Aggregated data into {len(result)} {period} periods")
        return result