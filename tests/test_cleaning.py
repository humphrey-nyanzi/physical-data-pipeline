import pandas as pd
import numpy as np
from src.data import cleaning
from src.config import league_definitions, constants


def test_normalize_clubs():
    df = pd.DataFrame(
        {
            "club_for": ["Kampala Queens", "Kcca Fc"],
            "club_against": ["She Maroons", "Vipers"],
        }
    )

    out = cleaning.normalize_clubs(df, "fwsl")
    assert "Kampala Queens FC" in out["club_for"].values


def test_compute_derived_metrics():
    df = pd.DataFrame(
        {
            "accelerations_zone_count:_1__2_mss": [1, 2],
            "accelerations_zone_count:_2__3_mss": [0, 1],
            "deceleration_zone_count:_1__2_mss": [0, 1],
            "duration": [45, 90],
        }
    )

    out = cleaning.compute_derived_metrics(df)
    assert "total_accelerations" in out.columns
    assert out.loc[0, "total_accelerations"] == 1
    assert np.isclose(out.loc[1, "acc_counts_per_min"], (2 + 1) / 90)


def test_drop_sparse_columns():
    df = pd.DataFrame({"a": [0, 0, 1], "b": [0, 0, 0], "c": [1, 2, 3]})

    out = cleaning.drop_sparse_columns(df, threshold=0.8)
    assert "b" not in out.columns
    assert "a" in out.columns


def test_normalize_duration_to_minutes_seconds_input():
    df = pd.DataFrame({"duration": [5400, 2700, 0, None]})
    out = cleaning.normalize_duration_to_minutes(df, raw_unit="seconds")

    assert "duration_seconds_raw" in out.columns
    assert np.isclose(out.loc[0, "duration"], 90.0)
    assert np.isclose(out.loc[1, "duration"], 45.0)


def test_normalize_duration_to_minutes_heuristic_auto():
    # Looks like seconds (very large for minutes)
    df = pd.DataFrame({"duration": [5400, 5600, 5300]})
    out = cleaning.normalize_duration_to_minutes(df, raw_unit="auto")
    assert out["duration"].median() < 200


# Note: Full pipeline test would require the large raw CSV; we avoid executing it in CI.
