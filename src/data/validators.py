"""
Data validation functions for Match-Analysis.

Provides functions to check data quality, detect outliers, and validate
against schema definitions.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
from . import schemas


def check_missing_data(df: pd.DataFrame, threshold: float = 0.5) -> Dict[str, float]:
    """Check for missing data in dataframe.

    Args:
        df (pd.DataFrame): Input dataframe
        threshold (float): Threshold for reporting (0-1)

    Returns:
        Dict[str, float]: Columns with missing % above threshold
    """
    missing_pct = (df.isnull().sum() / len(df) * 100).to_dict()
    return {col: pct for col, pct in missing_pct.items() if pct > threshold}


def detect_outliers(
    df: pd.DataFrame, columns: List[str], method: str = "iqr", multiplier: float = 1.5
) -> pd.DataFrame:
    """Detect outliers using IQR or z-score method.

    Args:
        df (pd.DataFrame): Input dataframe
        columns (List[str]): Columns to check
        method (str): 'iqr' or 'zscore'
        multiplier (float): IQR multiplier (default 1.5)

    Returns:
        pd.DataFrame: Boolean dataframe marking outliers
    """
    outliers = pd.DataFrame(False, index=df.index, columns=columns)

    for col in columns:
        if col not in df.columns:
            continue

        if method == "iqr":
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            outliers[col] = (df[col] < lower_bound) | (df[col] > upper_bound)

        elif method == "zscore":
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            outliers[col] = z_scores > 3

    return outliers


def validate_required_columns(
    df: pd.DataFrame, data_type: str = "processed"
) -> Tuple[bool, List[str]]:
    """Check if all required columns are present.

    Args:
        df (pd.DataFrame): Input dataframe
        data_type (str): 'raw' or 'processed'

    Returns:
        Tuple[bool, List[str]]: (is_valid, missing_columns)
    """
    required = schemas.get_required_columns(data_type)
    missing = [col for col in required if col not in df.columns]
    return len(missing) == 0, missing


def validate_data_types(
    df: pd.DataFrame, data_type: str = "processed"
) -> Dict[str, str]:
    """Check column data types match schema.

    Args:
        df (pd.DataFrame): Input dataframe
        data_type (str): 'raw' or 'processed'

    Returns:
        Dict[str, str]: Type mismatches (column: expected_type)
    """
    mismatches = {}
    schema = (
        schemas.RAW_DATA_COLUMNS
        if data_type == "raw"
        else schemas.PROCESSED_DATA_COLUMNS
    )

    for col, info in schema.items():
        if col not in df.columns:
            continue
        expected_type = info.get("dtype", "str")
        # Simplified type checking
        if expected_type == "int" and not pd.api.types.is_integer_dtype(df[col]):
            mismatches[col] = f"Expected int, got {df[col].dtype}"
        elif expected_type == "float" and not pd.api.types.is_numeric_dtype(df[col]):
            mismatches[col] = f"Expected float, got {df[col].dtype}"

    return mismatches


def check_sparsity(df: pd.DataFrame, threshold: float = 0.95) -> List[str]:
    """Check for sparse columns (mostly zeros or nulls).

    Args:
        df (pd.DataFrame): Input dataframe
        threshold (float): Sparsity threshold (0-1)

    Returns:
        List[str]: Column names above sparsity threshold
    """
    sparse_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        zero_pct = (df[col] == 0).sum() / len(df)
        null_pct = df[col].isnull().sum() / len(df)
        if zero_pct + null_pct > threshold:
            sparse_cols.append(col)
    return sparse_cols


def validate_duration(
    df: pd.DataFrame, col: str = "duration", min_duration: float = 60
) -> Tuple[int, pd.Series]:
    """Validate match/session duration.

    Args:
        df (pd.DataFrame): Input dataframe
        col (str): Duration column name
        min_duration (float): Minimum valid duration in minutes

    Returns:
        Tuple[int, pd.Series]: (count_invalid, invalid_rows)
    """
    if col not in df.columns:
        return 0, pd.Series(dtype=bool)

    invalid = df[col] < min_duration
    return invalid.sum(), df[invalid]
