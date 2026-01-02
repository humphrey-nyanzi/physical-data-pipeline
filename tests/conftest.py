"""
Pytest configuration and shared fixtures for Match-Analysis tests.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path


@pytest.fixture
def sample_raw_data():
    """Fixture: Sample raw data matching source format."""
    return pd.DataFrame(
        {
            "session_title": [
                "FWSL Match 1",
                "FWSL Match 1",
                "UPL Match 1",
                "UPL Match 1",
            ],
            "player_name": ["Player A", "Player B", "Player C", "Player D"],
            "position": ["GK", "DEF", "MID", "FWD"],
            "duration_minutes": [90.0, 45.0, 90.0, 90.0],
            "total_distance_km": [5.2, 8.1, 7.5, 6.8],
            "high_speed_distance_km": [0.5, 1.2, 1.8, 2.1],
            "sprint_distance_km": [0.1, 0.3, 0.6, 0.8],
            "total_accel_events": [12, 18, 25, 22],
            "total_decel_events": [10, 15, 20, 18],
            "avg_velocity_ms": [1.5, 2.1, 2.3, 2.0],
            "max_velocity_ms": [6.5, 7.2, 7.8, 7.5],
            "player_load": [45.2, 65.3, 72.1, 68.5],
        }
    )


@pytest.fixture
def sample_cleaned_data():
    """Fixture: Sample cleaned/processed data."""
    return pd.DataFrame(
        {
            "match_date": pd.to_datetime(
                ["2025-01-15", "2025-01-15", "2025-01-20", "2025-01-20"]
            ),
            "club": ["Amus College WFC", "Amus College WFC", "BUL FC", "BUL FC"],
            "league": ["FWSL", "FWSL", "UPL", "UPL"],
            "player_name": ["Player A", "Player B", "Player C", "Player D"],
            "position": ["Goalkeeper", "Defender", "Midfielder", "Forward"],
            "position_category": ["GK", "DEF", "MID", "FWD"],
            "minutes_played": [90.0, 45.0, 90.0, 90.0],
            "total_distance_km": [5.2, 8.1, 7.5, 6.8],
            "high_speed_distance_km": [0.5, 1.2, 1.8, 2.1],
            "sprint_distance_km": [0.1, 0.3, 0.6, 0.8],
            "total_accel_events": [12, 18, 25, 22],
            "total_decel_events": [10, 15, 20, 18],
            "avg_velocity_ms": [1.5, 2.1, 2.3, 2.0],
            "max_velocity_ms": [6.5, 7.2, 7.8, 7.5],
            "player_load": [45.2, 65.3, 72.1, 68.5],
            "per_minute_distance": [5.2 / 90, 8.1 / 45, 7.5 / 90, 6.8 / 90],
        }
    )


@pytest.fixture
def temp_data_dir(tmp_path):
    """Fixture: Temporary directory for test data files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    return data_dir


@pytest.fixture
def sample_csv_files(sample_raw_data, sample_cleaned_data, temp_data_dir):
    """Fixture: Create sample CSV files in temp directory."""
    raw_path = temp_data_dir / "raw" / "sample_raw.csv"
    processed_path = temp_data_dir / "processed" / "sample_cleaned.csv"

    sample_raw_data.to_csv(raw_path, index=False)
    sample_cleaned_data.to_csv(processed_path, index=False)

    return {"raw": raw_path, "processed": processed_path}
