"""
Parquet storage utilities for feature data
Handles reading and writing feature DataFrames to Parquet files
"""

import os
from pathlib import Path
from typing import Optional
import pandas as pd


def save_features_to_parquet(
    df: pd.DataFrame,
    feature_type: str,
    output_dir: str = "data/features"
) -> Path:
    """
    Save feature DataFrame to Parquet file
    
    Args:
        df: Feature DataFrame
        feature_type: Type of features (subscriptions, savings, credit, income, cash_flow)
        output_dir: Output directory path
        
    Returns:
        Path to saved Parquet file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save to Parquet
    file_path = output_path / f"{feature_type}.parquet"
    df.to_parquet(file_path, index=False, engine='pyarrow')
    
    return file_path


def load_features_from_parquet(
    feature_type: str,
    output_dir: str = "data/features"
) -> Optional[pd.DataFrame]:
    """
    Load feature DataFrame from Parquet file
    
    Args:
        feature_type: Type of features (subscriptions, savings, credit, income, cash_flow)
        output_dir: Output directory path
        
    Returns:
        Feature DataFrame or None if file doesn't exist
    """
    file_path = Path(output_dir) / f"{feature_type}.parquet"
    
    if not file_path.exists():
        return None
    
    return pd.read_parquet(file_path, engine='pyarrow')


def ensure_features_directory(output_dir: str = "data/features") -> Path:
    """
    Ensure features directory exists
    
    Args:
        output_dir: Output directory path
        
    Returns:
        Path object for directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

