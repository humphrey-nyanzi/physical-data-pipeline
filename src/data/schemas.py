"""
Data schemas and column definitions for Match-Analysis.

Defines expected columns, data types, validation rules, and transformations
for raw and processed datasets.
"""

from typing import List, Dict

# Raw data column definitions
RAW_DATA_COLUMNS = {
    "session_title": {"dtype": "str", "required": True},
    "player_name": {"dtype": "str", "required": True},
    "position": {"dtype": "str", "required": False},
    # Catapult raw exports commonly store duration in seconds under `duration`.
    # The cleaning pipeline normalizes this to minutes.
    "duration": {"dtype": "float", "required": False},
    "total_distance_km": {"dtype": "float", "required": False},
    "high_speed_distance_km": {"dtype": "float", "required": False},
    "sprint_distance_km": {"dtype": "float", "required": False},
    "total_accel_events": {"dtype": "int", "required": False},
    "total_decel_events": {"dtype": "int", "required": False},
    "avg_velocity_ms": {"dtype": "float", "required": False},
    "max_velocity_ms": {"dtype": "float", "required": False},
    "player_load": {"dtype": "float", "required": False},
}

# Processed data columns (after cleaning and transformation)
PROCESSED_DATA_COLUMNS = {
    "match_date": {"dtype": "datetime", "required": True},
    "club": {"dtype": "str", "required": True},
    "league": {"dtype": "str", "required": True},
    "player_name": {"dtype": "str", "required": True},
    "position": {"dtype": "str", "required": False},
    "position_category": {"dtype": "str", "required": False},
    "minutes_played": {"dtype": "float", "required": False},
    "total_distance_km": {"dtype": "float", "required": False},
    "high_speed_distance_km": {"dtype": "float", "required": False},
    "sprint_distance_km": {"dtype": "float", "required": False},
    "total_accel_events": {"dtype": "int", "required": False},
    "total_decel_events": {"dtype": "int", "required": False},
    "avg_velocity_ms": {"dtype": "float", "required": False},
    "max_velocity_ms": {"dtype": "float", "required": False},
    "player_load": {"dtype": "float", "required": False},
    "per_minute_distance": {"dtype": "float", "required": False},
}

# Column aliases and transformations
COLUMN_ALIASES = {
    "club_name": "club",
    "team": "club",
    "player_id": "player_name",
    "mins_played": "minutes_played",
    "mins": "minutes_played",
    "pos": "position",
}


def get_column_info(column_name: str, data_type: str = "processed") -> dict:
    """Get schema information for a column.

    Args:
        column_name (str): Column name
        data_type (str): 'raw' or 'processed'

    Returns:
        dict: Column info or empty dict if not found
    """
    schema = RAW_DATA_COLUMNS if data_type == "raw" else PROCESSED_DATA_COLUMNS
    return schema.get(column_name, {})


def get_required_columns(data_type: str = "processed") -> List[str]:
    """Get list of required columns.

    Args:
        data_type (str): 'raw' or 'processed'

    Returns:
        List[str]: List of required column names
    """
    schema = RAW_DATA_COLUMNS if data_type == "raw" else PROCESSED_DATA_COLUMNS
    return [col for col, info in schema.items() if info.get("required", False)]


def get_optional_columns(data_type: str = "processed") -> List[str]:
    """Get list of optional columns.

    Args:
        data_type (str): 'raw' or 'processed'

    Returns:
        List[str]: List of optional column names
    """
    schema = RAW_DATA_COLUMNS if data_type == "raw" else PROCESSED_DATA_COLUMNS
    return [col for col, info in schema.items() if not info.get("required", False)]
