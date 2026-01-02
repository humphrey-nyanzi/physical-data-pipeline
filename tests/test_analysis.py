"""Unit tests for analysis module."""

import pandas as pd
import numpy as np
from src.analysis import analysis


def test_normalize_match_day_format_fwsl():
    """Test match day format normalization for FWSL."""
    df = pd.DataFrame({"match_day": ["Wmd1", "Wmd2", "Wmd3"]})
    result = analysis.normalize_match_day_format(df, "fwsl")
    assert result["match_day"].tolist() == ["MD1", "MD2", "MD3"]


def test_normalize_match_day_format_upl():
    """Test match day format normalization for UPL."""
    df = pd.DataFrame({"match_day": ["Md1", "Md2", "Md3"]})
    result = analysis.normalize_match_day_format(df, "upl")
    assert result["match_day"].tolist() == ["MD1", "MD2", "MD3"]


def test_compute_metric_categories():
    """Test metric category identification."""
    df = pd.DataFrame(
        {
            "distance_km": [10.5, 11.2],
            "player_load": [350, 360],
            "p_name": ["John", "Jane"],
        }
    )
    cats = analysis.compute_metric_categories(df)
    assert "all_numeric" in cats
    assert "distance_km" in cats["all_numeric"]
    assert "player_load" in cats["all_numeric"]


def test_unique_players_per_club():
    """Test player count per club."""
    df = pd.DataFrame(
        {
            "club_for": ["Club A", "Club A", "Club B", "Club B", "Club B"],
            "p_name": ["P1", "P2", "P3", "P3", "P4"],
        }
    )
    result = analysis.unique_players_per_club(df)
    assert result[result["club_for"] == "Club A"]["unique_players"].values[0] == 2
    assert result[result["club_for"] == "Club B"]["unique_players"].values[0] == 2


def test_matchdays_per_club():
    """Test matchday count per club."""
    df = pd.DataFrame(
        {
            "club_for": ["Club A", "Club A", "Club A", "Club B", "Club B"],
            "match_day": ["MD1", "MD2", "MD1", "MD1", "MD2"],
            "p_name": ["P1", "P2", "P3", "P4", "P5"],
        }
    )
    result = analysis.matchdays_per_club(df)
    assert result[result["club_for"] == "Club A"]["unique_matchdays"].values[0] == 2
    assert result[result["club_for"] == "Club B"]["unique_matchdays"].values[0] == 2


def test_top_players_by_matchdays():
    """Test identification of top players."""
    df = pd.DataFrame(
        {
            "p_name": ["P1", "P1", "P1", "P2", "P2", "P3"],
            "player_club_": ["A", "A", "A", "B", "B", "C"],
            "match_day": ["MD1", "MD2", "MD3", "MD1", "MD2", "MD1"],
        }
    )
    result = analysis.top_players_by_matchdays(df, top_n=3)
    assert result.iloc[0]["p_name"] == "P1"  # P1 played 3 matchdays
    assert result.iloc[0]["unique_match_days"] == 3


def test_positional_stats():
    """Test positional analysis."""
    df = pd.DataFrame(
        {
            "general_position": ["defender", "defender", "forward", "forward"],
            "distance_km": [10.0, 11.0, 12.0, 13.0],
        }
    )
    result = analysis.compute_positional_stats(df, "distance_km")
    assert "defender" in result.index
    assert "forward" in result.index
    # Defender mean = 10.5, Forward mean = 12.5
    assert np.isclose(result.loc["defender", "mean"], 10.5)
    assert np.isclose(result.loc["forward", "mean"], 12.5)


def test_total_players_per_matchday():
    """Test player count aggregation by matchday."""
    df = pd.DataFrame(
        {
            "match_day": ["MD1", "MD1", "MD1", "MD2", "MD2"],
            "p_name": ["P1", "P2", "P3", "P4", "P5"],
        }
    )
    result = analysis.total_players_per_matchday(df)
    assert result[result["match_day"] == "MD1"]["total_player_entries"].values[0] == 3
    assert result[result["match_day"] == "MD2"]["total_player_entries"].values[0] == 2


def test_clubs_per_matchday():
    """Test club count aggregation by matchday."""
    df = pd.DataFrame(
        {
            "match_day": ["MD1", "MD1", "MD1", "MD2", "MD2"],
            "club_for": ["A", "A", "B", "A", "B"],
            "p_name": ["P1", "P2", "P3", "P4", "P5"],
        }
    )
    result = analysis.clubs_per_matchday(df)
    assert result[result["match_day"] == "MD1"]["num_clubs"].values[0] == 2
    assert result[result["match_day"] == "MD2"]["num_clubs"].values[0] == 2


def test_matchday_club_coverage_grid():
    """Test coverage grid generation."""
    df = pd.DataFrame(
        {
            "match_day": ["MD1", "MD1", "MD2"],
            "club_for": ["A", "B", "A"],
            "p_name": ["P1", "P2", "P3"],
        }
    )
    grid = analysis.matchday_club_coverage_grid(df)
    assert grid.loc["MD1", "A"] == 1  # A played MD1
    assert grid.loc["MD1", "B"] == 1  # B played MD1
    assert grid.loc["MD2", "A"] == 1  # A played MD2
    assert grid.loc["MD2", "B"] == 0  # B did not play MD2


def test_coverage_summary():
    """Test coverage statistics computation."""
    df = pd.DataFrame(
        {
            "match_day": ["MD1", "MD1", "MD2", "MD2"],
            "club_for": ["A", "B", "A", "B"],
            "p_name": ["P1", "P2", "P3", "P4"],
        }
    )
    summary = analysis.coverage_summary(df)
    assert "coverage_pct" in summary
    assert summary["unique_clubs"] == 2
    assert summary["unique_players"] == 4
    assert summary["total_matchdays"] == 2


def test_club_vs_league_comparison():
    """Test club vs league comparison."""
    df = pd.DataFrame(
        {
            "club_for": ["A", "A", "B", "B"],
            "distance_km": [10.0, 11.0, 12.0, 13.0],
        }
    )
    result = analysis.club_vs_league_comparison(df, "distance_km")
    league_mean = (10 + 11 + 12 + 13) / 4  # 11.5
    assert "club_mean" in result.columns
    assert "league_mean" in result.columns
    assert "diff_from_avg" in result.columns
