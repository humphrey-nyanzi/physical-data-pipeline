"""
Report Builder Module for Club-Level Performance Reports

Consolidates data aggregation and metric computation logic for generating
comprehensive club-level Catapult performance reports. Abstracts away from
document generation to enable reusable data preparation for multiple output formats.

Functions are league-agnostic and parameterized by league identifier.
All constants and configuration sourced from src/config modules.

Author: FUFA Research, Science & Technology Unit
Version: 1.0
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from src.config.speed_zones import get_speed_zones


def get_matchday_stats(
    club_df: pd.DataFrame, matchday_order: List[str]
) -> pd.DataFrame:
    """
    Aggregate per-matchday statistics for a club.

    Computes: opponent, players monitored, average duration, match result, location.
    Ensures all matchdays are present (fills missing with NaN/0).

    Args:
        club_df: Filtered club data
        matchday_order: Ordered list of matchday identifiers (e.g., ['Md1', 'Md2', ...])

    Returns:
        DataFrame with columns: Match Day, Opponent Club, Number of Players Monitored,
                                Average Session Duration (min), Match Result, Match Location
    """
    match_stats = (
        club_df.groupby("match_day", as_index=False)
        .agg(
            {
                "club_against": "first",
                "p_name": "nunique",
                "duration": "mean",
                "result": "first",
                "location": "first",
            }
        )
        .rename(
            columns={
                "club_against": "Opponent Club",
                "match_day": "Match Day",
                "p_name": "Number of Players Monitored",
                "duration": "Average Session Duration (min)",
                "result": "Match Result",
                "location": "Match Location",
            }
        )
    )

    # Ensure all matchdays are present
    full_md_df = pd.DataFrame({"Match Day": matchday_order})
    match_stats = full_md_df.merge(match_stats, on="Match Day", how="left")

    # Fill text columns with NaN, numeric columns with 0
    text_cols = ["Opponent Club", "Match Result", "Match Location"]
    num_cols = ["Number of Players Monitored", "Average Session Duration (min)"]

    for col in text_cols:
        match_stats[col] = match_stats[col].where(match_stats[col].notna(), np.nan)
    for col in num_cols:
        match_stats[col] = match_stats[col].fillna(0)

    # Round duration
    match_stats["Average Session Duration (min)"] = match_stats[
        "Average Session Duration (min)"
    ].round(1)

    return match_stats


def get_players_monitored_stats(club_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate per-player statistics for a club.

    Computes: player position (first occurrence) and count of unique matchdays played.

    Args:
        club_df: Filtered club data

    Returns:
        DataFrame with columns: Player Name, Position, Match Days Analysed
    """
    player_stats = (
        club_df.groupby("p_name", as_index=False)
        .agg({"general_position": "first", "match_day": pd.Series.nunique})
        .rename(columns={"match_day": "Match Days Analysed"})
    )

    # Title-case player names and sort
    player_stats["p_name"] = player_stats["p_name"].str.title()
    player_stats = player_stats.sort_values("p_name")

    # Rename columns for display
    player_stats = player_stats.rename(
        columns={"p_name": "Player Name", "general_position": "Position"}
    )

    return player_stats


def get_metric_summary(
    club_df: pd.DataFrame,
    volume_metrics: List[str],
    intensity_metrics: List[str],
    metric_display_names: Dict[str, str],
) -> pd.DataFrame:
    """
    Aggregate overall metrics (Total, Max, Min, Mean, Std Dev, Range).

    Computes summary statistics across all sessions for volume and intensity metrics.

    Args:
        club_df: Filtered club data
        volume_metrics: List of volume metric column names
        intensity_metrics: List of intensity metric column names
        metric_display_names: Dictionary mapping column names to display names

    Returns:
        DataFrame with columns: Metric, Total, Max, Min, Mean, Std Dev, Range
    """
    # Filter for valid metrics present in dataframe
    valid_vol = [m for m in volume_metrics if m in club_df.columns]
    valid_int = [m for m in intensity_metrics if m in club_df.columns]
    all_metrics = valid_vol + valid_int

    if not all_metrics:
        return pd.DataFrame()

    # Compute stats
    summary = club_df[all_metrics].agg(["sum", "max", "min", "mean", "std"])
    summary = summary.T
    
    # Null out 'sum' for intensity metrics
    summary.loc[valid_int, "sum"] = np.nan
    
    summary = summary.reset_index().rename(columns={"index": "Metric"})
    summary["Metric"] = summary["Metric"].map(metric_display_names).fillna(summary["Metric"])
    
    summary = summary.rename(
        columns={
            "sum": "Total",
            "max": "Max",
            "min": "Min",
            "mean": "Mean",
            "std": "Std Dev",
        }
    )

    summary = summary[["Metric", "Total", "Max", "Min", "Mean", "Std Dev"]]

    return summary.round(2)


def get_top_players_by_metric(
    club_df: pd.DataFrame, metrics: List[str], metric_display_names: Dict[str, str]
) -> pd.DataFrame:
    """
    Extract top player performance for each metric.

    For each metric, identifies the player with maximum value and their matchday.

    Args:
        club_df: Filtered club data
        metrics: List of metric column names to evaluate
        metric_display_names: Dictionary mapping column names to display names

    Returns:
        DataFrame with top player value per metric (columns as metrics, row as player info)
    """
    top_players = []

    valid_metrics = [m for m in metrics if m in club_df.columns]
    for metric in valid_metrics:
        idx = club_df[metric].idxmax()
        row = club_df.loc[idx]
        top_players.append(
            {
                "metric": metric,
                "player": row["p_name"].title(),
                "value": row[metric],
                "match_day": row["match_day"],
            }
        )

    top_players_df = pd.DataFrame(top_players)
    
    # Map metrics to display names
    top_players_df["metric"] = top_players_df["metric"].map(metric_display_names).fillna(top_players_df["metric"])
    
    # Rename for professional table display
    top_players_df = top_players_df.rename(columns={
        "metric": "Metric",
        "player": "Player Name",
        "value": "Value",
        "match_day": "Match Day"
    })

    # Drop specific metrics if needed (already handled by passing correct metrics list usually, but for safety)
    top_players_df = top_players_df[~top_players_df["Metric"].str.contains("Max Acceleration|Max Deceleration", na=False)]

    return top_players_df.round(2)


def get_average_metrics_by_position(
    club_df: pd.DataFrame,
    volume_metrics: List[str],
    intensity_metrics: List[str],
    metric_display_names: Dict[str, str],
) -> pd.DataFrame:
    """
    Compute average metrics grouped by player position.

    Args:
        club_df: Filtered club data
        volume_metrics: List of volume metric column names
        intensity_metrics: List of intensity metric column names
        metric_display_names: Dictionary mapping column names to display names

    Returns:
        DataFrame with metrics as rows and positions as columns
    """
    valid_vol = [m for m in volume_metrics if m in club_df.columns]
    valid_int = [m for m in intensity_metrics if m in club_df.columns]
    all_metrics = valid_vol + valid_int

    if not all_metrics:
        return pd.DataFrame()

    # Group by position and compute mean
    avg_by_position = (
        club_df.groupby("general_position")[all_metrics].mean().round(2)
    )

    # Transpose so metrics are rows, positions are columns
    res = avg_by_position.T
    res = res.reset_index().rename(columns={"index": "Metric"})
    
    # Map metric names
    res["Metric"] = res["Metric"].map(metric_display_names).fillna(res["Metric"])
    
    # Filter out redundant max metrics
    res = res[~res["Metric"].str.contains("Max Acceleration|Max Deceleration", na=False)]

    return res


def get_total_metrics_by_position(
    club_df: pd.DataFrame,
    volume_metrics: List[str],
    metric_display_names: Dict[str, str],
) -> pd.DataFrame:
    """
    Compute total (cumulative) volume metrics grouped by player position.

    Args:
        club_df: Filtered club data
        volume_metrics: List of volume metric column names
        metric_display_names: Dictionary mapping column names to display names

    Returns:
        DataFrame with metrics as rows and positions as columns
    """
    valid_vol = [m for m in volume_metrics if m in club_df.columns]
    if not valid_vol:
        return pd.DataFrame()

    # Group by position and compute sum
    total_by_position = (
        club_df.groupby("general_position")[valid_vol].sum().round(2)
    )

    # Transpose
    res = total_by_position.T
    res = res.reset_index().rename(columns={"index": "Metric"})
    
    # Map metric names
    res["Metric"] = res["Metric"].map(metric_display_names).fillna(res["Metric"])

    return res


def get_average_metrics_per_matchday(
    club_df: pd.DataFrame,
    matchday_order: List[str],
    volume_metrics: List[str],
    intensity_metrics: List[str],
    metric_display_names: Dict[str, str],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute average metrics per matchday for trend analysis.

    Returns both display-ready (renamed) and raw (for plotting) versions.

    Args:
        club_df: Filtered club data
        matchday_order: Ordered list of matchday identifiers
        volume_metrics: List of volume metric column names
        intensity_metrics: List of intensity metric column names
        metric_display_names: Dictionary mapping column names to display names

    Returns:
        Tuple of (display_df, plot_df) where:
            - display_df: Renamed columns, formatted for tables
            - plot_df: Raw values, matches matchday_order
    """
    valid_vol = [m for m in volume_metrics if m in club_df.columns]
    valid_int = [m for m in intensity_metrics if m in club_df.columns]
    all_metrics = valid_vol + valid_int

    if not all_metrics:
        return pd.DataFrame(), pd.DataFrame()

    avg_per_matchday = club_df.groupby("match_day")[all_metrics].mean().reset_index()
    avg_per_matchday["match_day"] = pd.Categorical(
        avg_per_matchday["match_day"], categories=matchday_order, ordered=True
    )
    avg_per_matchday = avg_per_matchday.sort_values(by="match_day")

    # Keep raw version for plotting
    plot_df = avg_per_matchday.copy().round(2)

    # Create display version with renamed columns
    display_df = avg_per_matchday.rename(
        columns={"match_day": "Match Day", **metric_display_names}
    )

    # Drop acceleration/deceleration max columns if they exist
    cols_to_drop = [
        col
        for col in display_df.columns
        if "Max Acceleration" in col or "Max Deceleration" in col
    ]
    display_df = display_df.drop(columns=cols_to_drop, errors="ignore")

    return display_df.round(1), plot_df


def club_vs_season_comparison(
    club_df: pd.DataFrame,
    season_df: pd.DataFrame,
    volume_metrics: List[str],
    intensity_metrics: List[str],
    metric_display_names: Dict[str, str],
) -> pd.DataFrame:
    """
    Compare club average metrics against season-wide averages.

    Computes percentage difference for each metric.

    Args:
        club_df: Filtered club data
        season_df: Full season data for all clubs
        volume_metrics: List of volume metric column names
        intensity_metrics: List of intensity metric column names
        metric_display_names: Dictionary mapping column names to display names

    Returns:
        DataFrame with columns: Metric, Club Average, Season Average, % Difference
    """
    valid_vol = [m for m in volume_metrics if m in club_df.columns and m in season_df.columns]
    valid_int = [m for m in intensity_metrics if m in club_df.columns and m in season_df.columns]
    all_metrics = valid_vol + valid_int

    if not all_metrics:
        return pd.DataFrame()

    club_avg = club_df[all_metrics].mean().to_frame(name="Club Average")
    season_avg = season_df[all_metrics].mean().to_frame(name="Season Average")

    comparison = club_avg.join(season_avg)

    # Calculate percentage difference
    comparison["% Difference"] = (
        (comparison["Club Average"] - comparison["Season Average"])
        / comparison["Season Average"]
    ) * 100

    # Rename metrics
    comparison.index = [metric_display_names.get(m, m) for m in comparison.index]

    # Filter out max metrics
    comparison = comparison[~comparison.index.str.contains("Max Acceleration|Max Deceleration", na=False)]

    comparison = comparison.reset_index().rename(columns={"index": "Metric"})
    return comparison[["Metric", "Club Average", "Season Average", "% Difference"]]


def positional_comparison_vs_season(
    club_df: pd.DataFrame,
    season_df: pd.DataFrame,
    volume_metrics: List[str],
    intensity_metrics: List[str],
    metric_display_names: Dict[str, str],
) -> pd.DataFrame:
    """
    Compare club positional averages against season positional averages.

    For each position and metric, computes club vs season comparison with % difference.

    Args:
        club_df: Filtered club data
        season_df: Full season data for all clubs
        volume_metrics: List of volume metric column names
        intensity_metrics: List of intensity metric column names
        metric_display_names: Dictionary mapping column names to display names

    Returns:
        DataFrame structured as: Index = Metric, Columns = Positions (Club/Season/% Diff for each)
    """
    valid_vol = [m for m in volume_metrics if m in club_df.columns and m in season_df.columns]
    valid_int = [m for m in intensity_metrics if m in club_df.columns and m in season_df.columns]
    all_metrics = valid_vol + valid_int

    if not all_metrics:
        return pd.DataFrame()

    club_pos_avg = (
        club_df.groupby("general_position")[all_metrics].mean().add_prefix("Club_")
    )
    season_pos_avg = (
        season_df.groupby("general_position")[all_metrics].mean().add_prefix("Season_")
    )

    combined = club_pos_avg.join(season_pos_avg)

    # Calculate percentage differences
    for metric in all_metrics:
        club_col = f"Club_{metric}"
        season_col = f"Season_{metric}"
        if club_col in combined.columns and season_col in combined.columns:
            combined[f"PctDiff_{metric}"] = (
                (combined[club_col] - combined[season_col]) / combined[season_col]
            ) * 100

    # Reorder columns for display
    ordered_cols = []
    for metric in all_metrics:
        ordered_cols.extend([f"Club_{metric}", f"Season_{metric}", f"PctDiff_{metric}"])

    comparison_by_position = combined[ordered_cols].round(2).T
    comparison_by_position.reset_index(inplace=True)
    comparison_by_position.rename(columns={"index": "Metric"}, inplace=True)

    # Apply display name mappings
    for old_name, new_name in metric_display_names.items():
        comparison_by_position["Metric"] = comparison_by_position["Metric"].str.replace(
            f"Club_{old_name}", f"Club {new_name}", regex=False
        )
        comparison_by_position["Metric"] = comparison_by_position["Metric"].str.replace(
            f"Season_{old_name}", f"Season {new_name}", regex=False
        )
        comparison_by_position["Metric"] = comparison_by_position["Metric"].str.replace(
            f"PctDiff_{old_name}", f"% Diff {new_name}", regex=False
        )

    return comparison_by_position


def get_speed_zone_breakdown(
    club_df: pd.DataFrame,
    season: str = "2025/26"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregate distance by speed zone and position.

    Returns both absolute distances and percentages by position.
    
    Handles missing speed zone columns gracefully by dynamically discovering
    available columns and returning empty DataFrames if none are found.

    Args:
        club_df: Filtered club data
        season: Season string for zone label lookup

    Returns:
        Tuple of (zone_distances_df, zone_percentages_df)
    """
    # Expected column names (try multiple naming patterns)
    speed_zone_patterns = [
        # Pattern 1: Single underscore (as expected by reports)
        [
            "distance_in_speed_zone_1_km",
            "distance_in_speed_zone_2_km",
            "distance_in_speed_zone_3_km",
            "distance_in_speed_zone_4_km",
            "distance_in_speed_zone_5_km",
        ],
        # Pattern 2: Double underscore (from standardize_columns)
        [
            "distance_in_speed_zone_1__km",
            "distance_in_speed_zone_2__km",
            "distance_in_speed_zone_3__km",
            "distance_in_speed_zone_4__km",
            "distance_in_speed_zone_5__km",
        ],
    ]
    
    # Find which pattern exists in the dataframe
    speed_zone_cols = []
    for pattern in speed_zone_patterns:
        existing = [c for c in pattern if c in club_df.columns]
        if len(existing) > len(speed_zone_cols):
            speed_zone_cols = existing
    
    # Also try dynamic discovery as fallback
    if not speed_zone_cols:
        speed_zone_cols = [
            c for c in club_df.columns 
            if 'distance' in c.lower() and 'speed' in c.lower() and 'zone' in c.lower()
        ]
        # Sort to ensure consistent ordering (Zone 1, 2, 3, 4, 5)
        speed_zone_cols = sorted(speed_zone_cols)
    
    # If no speed zone columns found, return empty DataFrames with warning
    if not speed_zone_cols:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "Speed zone columns not found in dataset. "
            "Speed zone breakdown will be unavailable."
        )
        # Debug helper: print a few columns to see what's actually there
        logger.warning(f"Available columns sample: {list(club_df.columns)[:20]}")
        # Check specifically for any 'zone' columns
        zone_cols_debug = [c for c in club_df.columns if 'zone' in c.lower()]
        logger.warning(f"Columns containing 'zone': {zone_cols_debug}")
        
        return pd.DataFrame(), pd.DataFrame()
    # Group by position and sum distances
    zone_by_position = club_df.groupby("general_position")[speed_zone_cols].sum()

    # Create position labels
    zone_by_position.index = [f"{pos}s" for pos in zone_by_position.index]

    # Rename columns with dynamic thresholds
    zones_dict = get_speed_zones(season)
    zone_labels = []
    for i in range(len(speed_zone_cols)):
        zone_key = f"Zone {i + 1}"
        if zone_key in zones_dict:
            zone_labels.append(f"{zone_key} ({zones_dict[zone_key]['range']} km/h)")
        else:
            zone_labels.append(zone_key)
            
    zone_by_position.columns = zone_labels

    # Convert to percentages
    zone_pct = zone_by_position.div(zone_by_position.sum(axis=1), axis=0) * 100

    return zone_by_position, zone_pct.round(2)


def compute_coverage_summary(
    club_df: pd.DataFrame, matchday_order: List[str]
) -> Dict[str, int]:
    """
    Compute basic coverage statistics for a club.

    Args:
        club_df: Filtered club data
        matchday_order: Ordered list of matchday identifiers

    Returns:
        Dictionary with coverage metrics
    """
    return {
        "total_matchdays_available": len(matchday_order),
        "matchdays_with_data": club_df["match_day"].nunique(),
        "unique_players": club_df["p_name"].nunique(),
        "total_sessions": len(club_df),
    }
