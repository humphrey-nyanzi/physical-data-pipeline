"""
Unified analysis module for Match-Analysis.

Provides core analytical functions for both FWSL and UPL leagues, encapsulating
logic from `analysis_FWSL_2025.ipynb` and `analysis_UPL_2025.ipynb`.

The module separates data loading, metric computation, aggregation, and
visualization into reusable functions that can be called independently or
as part of an analysis pipeline.
"""

from typing import List, Optional, Tuple, Dict
import pandas as pd
import numpy as np

from ..config import constants, league_definitions


# ============================================================================
# Data Loading & Preparation
# ============================================================================


def load_processed_data(league: str, data_dir: str = "./") -> pd.DataFrame:
    """Load cleaned processed data from CSV.

    Args:
        league (str): League identifier ('fwsl' or 'upl')
        data_dir (str): Directory containing processed CSVs

    Returns:
        pd.DataFrame: Loaded data
    """
    filename = (
        constants.FWSL_PROCESSED_OUTPUT
        if league.lower() == "fwsl"
        else constants.UPL_PROCESSED_OUTPUT
    )
    path = f"{data_dir}/{filename}"
    return pd.read_csv(path)


def normalize_match_day_format(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """Standardize match_day column to 'MDx' format.

    Args:
        df (pd.DataFrame): DataFrame with match_day column
        league (str): League identifier ('fwsl' or 'upl')

    Returns:
        pd.DataFrame: DataFrame with normalized match_day column
    """
    df = df.copy()
    if "match_day" in df.columns:
        if league.lower() == "fwsl":
            # Replace 'Wmd' prefix with 'MD'
            df["match_day"] = df["match_day"].str.replace("Wmd", "MD")
        elif league.lower() == "upl":
            # Keep 'Md' but standardize to 'MD'
            df["match_day"] = df["match_day"].str.replace("Md", "MD")
    return df


def compute_metric_categories(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Identify numeric columns and categorize by type.

    Returns:
        dict: {
            'all_numeric': [...],
            'core': [...],
            'volume': [...],
            'intensity': [...]
        }
    """
    all_numeric = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
    core = constants.CORE_METRICS
    volume = constants.VOLUME_METRICS
    intensity = constants.INTENSITY_METRICS

    return {
        "all_numeric": all_numeric,
        "core": [c for c in core if c in df.columns],
        "volume": [c for c in volume if c in df.columns],
        "intensity": [c for c in intensity if c in df.columns],
    }


# ============================================================================
# Summary Statistics
# ============================================================================


def compute_summary_stats(df: pd.DataFrame, metric_type: str = "all") -> pd.DataFrame:
    """Compute summary statistics for metrics.

    Args:
        df (pd.DataFrame): Data
        metric_type (str): 'volume', 'intensity', or 'all'

    Returns:
        pd.DataFrame: Summary stats (rows=metrics, columns=stats)
    """
    metrics_dict = compute_metric_categories(df)

    if metric_type == "volume":
        metrics = metrics_dict["volume"]
        agg_funcs = constants.SUMMARY_STATISTICS_VOLUME
    elif metric_type == "intensity":
        metrics = metrics_dict["intensity"]
        agg_funcs = constants.SUMMARY_STATISTICS_INTENSITY
    else:
        metrics = metrics_dict["core"]
        agg_funcs = constants.SUMMARY_STATISTICS

    if not metrics:
        return pd.DataFrame()

    return df[metrics].agg(agg_funcs).T.round(2)


# ============================================================================
# Club-Level Analysis
# ============================================================================


def unique_players_per_club(df: pd.DataFrame) -> pd.DataFrame:
    """Count unique players per club.

    Returns:
        pd.DataFrame: Columns [club_for, unique_players]
    """
    return (
        df.groupby("club_for")["p_name"]
        .nunique()
        .reset_index()
        .rename(columns={"p_name": "unique_players"})
        .sort_values("unique_players", ascending=False)
    )


def players_per_club_per_matchday(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate average unique players per matchday for each club.

    Returns:
        pd.DataFrame: Columns [club_for, avg_players_per_matchday]
    """
    players_per_day = (
        df.groupby(["club_for", "match_day"])["p_name"]
        .nunique()
        .reset_index()
        .rename(columns={"p_name": "unique_players"})
    )
    avg = (
        players_per_day.groupby("club_for")["unique_players"]
        .mean()
        .reset_index()
        .rename(columns={"unique_players": "avg_players_per_matchday"})
    )
    return avg.sort_values("avg_players_per_matchday", ascending=False)


def matchdays_per_club(df: pd.DataFrame) -> pd.DataFrame:
    """Count unique matchdays analysed per club.

    Returns:
        pd.DataFrame: Columns [club_for, unique_matchdays]
    """
    return (
        df.groupby("club_for")["match_day"]
        .nunique()
        .reset_index()
        .rename(columns={"match_day": "unique_matchdays"})
        .sort_values("unique_matchdays", ascending=False)
    )


def club_coverage_analysis(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """Full club coverage analysis: uploaded vs analysed matchdays.

    Args:
        df (pd.DataFrame): Processed data
        league (str): League identifier ('fwsl' or 'upl')

    Returns:
        pd.DataFrame: Columns [club_for, Uploaded, Analysed, Pending, Not Uploaded]
    """
    config = league_definitions.get_league_config(league)
    uploaded_dict = config.get("uploaded_matches", {})

    analysed = (
        df.groupby("club_for")["match_day"]
        .nunique()
        .reset_index()
        .rename(columns={"match_day": "Analysed Matchdays"})
    )

    if not uploaded_dict:
        # If no uploaded data, just return analysed
        return analysed

    uploaded_df = pd.DataFrame(
        uploaded_dict.items(), columns=["club_for", "Uploaded Matchdays"]
    )

    # Merge and compute pending/not uploaded
    result = analysed.merge(uploaded_df, on="club_for", how="left")
    result["Uploaded Matchdays"] = result["Uploaded Matchdays"].fillna(0).astype(int)

    result["Pending"] = (
        result["Uploaded Matchdays"] - result["Analysed Matchdays"]
    ).clip(lower=0)

    max_days = 22  # Standard FWSL matchdays
    result["Not Uploaded"] = (max_days - result["Uploaded Matchdays"]).clip(lower=0)

    return result.sort_values("Analysed Matchdays", ascending=False)


# ============================================================================
# Player-Level Analysis
# ============================================================================


def top_players_by_matchdays(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Identify top players by number of matchdays played.

    Args:
        df (pd.DataFrame): Data
        top_n (int): Number of players to return

    Returns:
        pd.DataFrame: Columns [p_name, player_club_, unique_match_days]
    """
    return (
        df.groupby(["p_name", "player_club_"])["match_day"]
        .nunique()
        .reset_index()
        .rename(columns={"match_day": "unique_match_days"})
        .sort_values("unique_match_days", ascending=False)
        .head(top_n)
    )


# ============================================================================
# Positional Analysis
# ============================================================================


def compute_positional_stats(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Compute average metric by player position.

    Args:
        df (pd.DataFrame): Data
        metric (str): Column name (e.g., 'distance_km', 'player_load')

    Returns:
        pd.DataFrame: Positional averages
    """
    if metric not in df.columns or "general_position" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("general_position")[metric]
        .agg(["mean", "std", "count"])
        .round(2)
        .sort_values("mean", ascending=False)
    )


def positional_comparison_all_metrics(
    df: pd.DataFrame, metrics: Optional[List[str]] = None
) -> pd.DataFrame:
    """Compute mean of each metric by position.

    Args:
        df (pd.DataFrame): Data
        metrics (Optional[List[str]]): Specific metrics to analyze.
                                      If None, uses all numeric.

    Returns:
        pd.DataFrame: Positions x Metrics mean values
    """
    if metrics is None:
        metrics = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

    available = [m for m in metrics if m in df.columns]

    if "general_position" not in df.columns or not available:
        return pd.DataFrame()

    return df.groupby("general_position")[available].mean().round(2)


# ============================================================================
# Match Day Trends
# ============================================================================


def total_players_per_matchday(df: pd.DataFrame) -> pd.DataFrame:
    """Count total player entries per matchday across all clubs.

    Returns:
        pd.DataFrame: Columns [match_day, total_player_entries]
    """
    return (
        df.groupby("match_day")["p_name"]
        .count()
        .reset_index()
        .rename(columns={"p_name": "total_player_entries"})
    )


def clubs_per_matchday(df: pd.DataFrame) -> pd.DataFrame:
    """Count unique clubs that submitted data per matchday.

    Returns:
        pd.DataFrame: Columns [match_day, num_clubs]
    """
    return (
        df.groupby("match_day")["club_for"]
        .nunique()
        .reset_index()
        .rename(columns={"club_for": "num_clubs"})
    )


def matchday_trend_metrics(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Compute mean of a metric per matchday (trend analysis).

    Args:
        df (pd.DataFrame): Data
        metric (str): Column name

    Returns:
        pd.DataFrame: Columns [match_day, metric (mean)]
    """
    if metric not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("match_day")[metric]
        .agg(["mean", "std", "count"])
        .round(2)
        .reset_index()
        .rename(columns={"mean": f"{metric}_mean", "std": f"{metric}_std"})
    )


# ============================================================================
# Completeness & Coverage
# ============================================================================


def matchday_club_coverage_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Build binary coverage grid: rows=matchdays, cols=clubs.

    Returns:
        pd.DataFrame: Binary (1=analysed, 0=missing)
    """
    clubs = sorted(df["club_for"].unique())
    # Use actual matchdays from data instead of hardcoded format
    matchdays = sorted(df["match_day"].unique())

    if not matchdays:
        # Return empty grid if no matchdays
        return pd.DataFrame()

    grid_data = []
    for md in matchdays:
        row = []
        for club in clubs:
            mask = (df["match_day"] == md) & (df["club_for"] == club)
            is_present = 1 if df.loc[mask, "p_name"].nunique() > 0 else 0
            row.append(is_present)
        grid_data.append(row)

    return pd.DataFrame(grid_data, index=matchdays, columns=clubs)


def coverage_summary(df: pd.DataFrame) -> Dict[str, float]:
    """Compute overall coverage statistics.

    Returns:
        dict: {
            'total_matches': int,
            'coverage_pct': float,
            'avg_players_per_match': float,
            'unique_clubs': int
        }
    """
    grid = matchday_club_coverage_grid(df)

    total_cells = grid.shape[0] * grid.shape[1]
    covered_cells = (grid == 1).sum().sum()
    coverage_pct = (covered_cells / total_cells * 100) if total_cells > 0 else 0

    return {
        "total_matchdays": grid.shape[0],
        "total_clubs": grid.shape[1],
        "total_cells": total_cells,
        "covered_cells": int(covered_cells),
        "coverage_pct": round(coverage_pct, 1),
        "avg_players_per_match": round(
            df.groupby(["match_day", "club_for"]).size().mean(), 1
        ),
        "unique_clubs": df["club_for"].nunique(),
        "unique_players": df["p_name"].nunique(),
    }


# ============================================================================
# Comparison & Relative Metrics
# ============================================================================


def club_vs_league_comparison(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Compare each club's average metric to league average.

    Args:
        df (pd.DataFrame): Data
        metric (str): Column name

    Returns:
        pd.DataFrame: Columns [club_for, club_mean, league_mean, diff_from_avg]
    """
    if metric not in df.columns:
        return pd.DataFrame()

    league_mean = df[metric].mean()

    club_means = (
        df.groupby("club_for")[metric]
        .mean()
        .reset_index()
        .rename(columns={metric: "club_mean"})
    )

    club_means["league_mean"] = league_mean
    club_means["diff_from_avg"] = (club_means["club_mean"] - league_mean).round(2)

    return club_means.sort_values("club_mean", ascending=False).round(2)


# ============================================================================
# Analysis Pipeline
# ============================================================================


def full_analysis_summary(league: str, data_dir: str = "./") -> Dict:
    """Run complete analysis and return all summaries.

    Args:
        league (str): League identifier ('fwsl' or 'upl')
        data_dir (str): Directory with processed data

    Returns:
        dict: {
            'data': DataFrame,
            'summary_stats_volume': DataFrame,
            'summary_stats_intensity': DataFrame,
            'club_coverage': DataFrame,
            'top_players': DataFrame,
            'coverage_summary': dict,
            'position_comparison': DataFrame
        }
    """
    # Load and prepare
    df = load_processed_data(league, data_dir)
    df = normalize_match_day_format(df, league)

    # Compute all analyses
    result = {
        "data": df,
        "summary_stats_volume": compute_summary_stats(df, "volume"),
        "summary_stats_intensity": compute_summary_stats(df, "intensity"),
        "unique_players_per_club": unique_players_per_club(df),
        "club_coverage": club_coverage_analysis(df, league),
        "top_players": top_players_by_matchdays(df, top_n=15),
        "coverage_summary": coverage_summary(df),
        "position_comparison": positional_comparison_all_metrics(df),
        "clubs_per_matchday": clubs_per_matchday(df),
        "players_per_matchday": total_players_per_matchday(df),
    }

    return result
