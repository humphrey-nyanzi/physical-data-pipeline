"""
Global constants, thresholds, and metric definitions for data cleaning,
analysis, and reporting.

This module consolidates all hardcoded values, file paths, and metric
definitions to enable centralized configuration management.
"""

# ============================================================================
# Data Validation Thresholds
# ============================================================================

# Minimum duration for a valid match session (in minutes)
MIN_SESSION_DURATION_MINUTES = 60

# Minimum distance for a valid player performance (in kilometers)
MIN_SESSION_DISTANCE_KM = 2.0

# Interquartile Range multiplier for outlier detection
OUTLIER_IQR_MULTIPLIER = 1.5

# Sparsity threshold for dropping columns (% of zeros)
SPARSE_COLUMN_THRESHOLD = 0.95

# ============================================================================
# Match Split Names (standardized naming)
# ============================================================================

SPLIT_NAMES = {
    "raw_1st": "1st.half",
    "raw_2nd": "2nd.half",
    "standard_1st": "1st Half",
    "standard_2nd": "2nd Half",
}

# ============================================================================
# Metric Categories for Analysis
# ============================================================================

VOLUME_METRICS = [
    "distance_km",
    "sprint_distance_m",
    "power_plays",
    "energy_kcal",
    "impacts",
    "total_accelerations",
    "total_decelerations",
    "total_actions",
]

INTENSITY_METRICS = [
    "player_load",
    "top_speed_ms",
    "top_speed_kmh",
    "distance_per_min_mmin",
    "power_score_wkg",
    "work_ratio",
    "max_acceleration_mss",
    "max_deceleration_mss",
    "acc_counts_per_min",
    "dec_counts_per_min",
]

# ============================================================================
# Core Metric Definitions
# ============================================================================

# Metrics of primary interest for analysis and reporting
CORE_METRICS = [
    "duration",
] + VOLUME_METRICS + INTENSITY_METRICS + [
    # Speed zone distance columns (required for speed zone breakdown analysis)
    "distance_in_speed_zone_1_km",
    "distance_in_speed_zone_2_km",
    "distance_in_speed_zone_3_km",
    "distance_in_speed_zone_4_km",
    "distance_in_speed_zone_5_km",
    # Acceleration zone count columns (needed for total_accelerations computation)
    "accelerations_zone_count:_1__2_mss",
    "accelerations_zone_count:_2__3_mss",
    "accelerations_zone_count:_3__4_mss",
    "accelerations_zone_count:_>_4_mss",
    # Deceleration zone count columns (needed for total_decelerations computation)
    "deceleration_zone_count:_1__2_mss",
    "deceleration_zone_count:_2__3_mss",
    "deceleration_zone_count:_3__4_mss",
    "deceleration_zone_count:_>_4_mss",
]

# ============================================================================
# Acceleration/Deceleration Zone Definitions
# ============================================================================

# Column names for acceleration zones in raw Catapult data
ACCELERATION_ZONE_COLUMNS = [
    "accelerations_zone_count:_1__2_mss",
    "accelerations_zone_count:_2__3_mss",
    "accelerations_zone_count:_3__4_mss",
    "accelerations_zone_count:_>_4_mss",
]

# Column names for deceleration zones in raw Catapult data
DECELERATION_ZONE_COLUMNS = [
    "deceleration_zone_count:_1__2_mss",
    "deceleration_zone_count:_2__3_mss",
    "deceleration_zone_count:_3__4_mss",
    "deceleration_zone_count:_>_4_mss",
]

# Computed metric names
COMPUTED_METRICS = {
    "acc_counts_per_min": ("total_accelerations", "duration"),
    "dec_counts_per_min": ("total_decelerations", "duration"),
    "total_accelerations": ACCELERATION_ZONE_COLUMNS,
    "total_decelerations": DECELERATION_ZONE_COLUMNS,
}

# ============================================================================
# Merge Configuration for Half-by-Half Data
# ============================================================================

# Keys used to identify unique player-match combinations
MERGE_KEYS = [
    "p_name",
    "player_club_",
    "club_for",
    "club_against",
    "match_day",
    "general_position",
    "player_position",
    "result",
    "location",
]

# Metrics to aggregate via SUM when merging halves
AGGREGATE_SUM_METRICS = [
    col
    for col in CORE_METRICS
    if col
    not in [
        "top_speed_ms",
        "top_speed_kmh",
        "distance_per_min_mmin",
        "max_acceleration_mss",
        "max_deceleration_mss",
        "acc_counts_per_min",
        "dec_counts_per_min",
    ]
]

# Metrics to aggregate via MAX when merging halves
AGGREGATE_MAX_METRICS = [
    "top_speed_ms",
    "top_speed_kmh",
    "max_acceleration_mss",
    "max_deceleration_mss",
]

# Rate metrics that are re-computed AFTER aggregation (not carried through directly)
AGGREGATE_RECOMPUTE_METRICS = [
    "distance_per_min_mmin",
    "acc_counts_per_min",
    "dec_counts_per_min",
]

# ============================================================================
# File I/O Paths and Extensions
# ============================================================================

# Raw data file location
RAW_DATA_FILE = "./data/raw/all_catapult_data_16_Jul_25.csv"

# Processed data output paths
PROCESSED_DATA_DIR = "./data/processed/"
OUTPUT_REPORTS_DIR = "./reports/"
OUTPUT_REPORTS_FWSL_DIR = "./reports/FWSL/"
OUTPUT_REPORTS_UPL_DIR = "./reports/UPL/"

# Processed CSV output naming
FWSL_PROCESSED_OUTPUT = "FWSL25_matches_clean.csv"
UPL_PROCESSED_OUTPUT = "UPL25_matches_clean.csv"

# ============================================================================
# Column Rename Mappings (for display in reports)
# ============================================================================

METRIC_DISPLAY_NAMES = {
    "distance_km": "Distance",
    "sprint_distance_m": "Sprint Distance",
    "power_plays": "Power Plays",
    "energy_kcal": "Energy",
    "impacts": "Impacts",
    "total_accelerations": "Accelerations",
    "total_decelerations": "Decelerations",
    "total_actions": "Total Actions",
    "player_load": "Player Load",
    "top_speed_kmh": "Top Speed",
    "distance_per_min_mmin": "Distance per Minute",
    "power_score_wkg": "Power Score",
    "work_ratio": "Work Ratio",
    "max_acceleration_mss": "Max Acceleration",
    "max_deceleration_mss": "Max Deceleration",
    "acc_counts_per_min": "Acceleration Counts per Min",
    "dec_counts_per_min": "Deceleration Counts per Min",
}

GENERAL_DISPLAY_NAMES = {
    "p_name": "Player Name",
    "club_for": "Club",
    "club_against": "Opponent",
    "match_day": "Match Day",
    "general_position": "Position",
    "player_position": "Position",
    "unique_players": "Number of Players",
    "total_sessions": "Total Sessions",
    "total_players": "Total Players",
    "total_clubs": "Total Clubs",
    "matchdays_uploaded": "Matches Uploaded",
    "avg_players": "Avg Players",
    "unique_players_per_club": "Players per Club",
}

# ============================================================================
# Aggregation Functions for Summary Statistics
# ============================================================================

# Default statistics to compute for metric summaries
SUMMARY_STATISTICS = ["sum", "max", "min", "mean", "std"]

SUMMARY_STATISTICS_VOLUME = ["sum", "mean", "std"]
SUMMARY_STATISTICS_INTENSITY = ["max", "mean", "std"]

# ============================================================================
# Text Processing Constants
# ============================================================================

# Club name normalization rules
CLUB_CORRECTIONS_FWSL = {
    "Uganda Martyrs Hs": "Uganda Martyrs Lubaga WFC",
    "Uganda Martyr'S Hs": "Uganda Martyrs Lubaga WFC",
    "Uganda Martrys": "Uganda Martyrs Lubaga WFC",
    "She Corporate Wfc": "She Corporates FC",
    "Olila High School": "Olila HS WFC",
    "Wakiso Hills": "Wakiso Hill WFC",
    "She Coperates": "She Corporates FC",
}

# Club name normalization rules for UPL
CLUB_CORRECTIONS_UPL = {
    "Solitilo Bright Stars": "Soltilo Bright Stars FC",
    "Soltito Bright Stars": "Soltilo Bright Stars FC",
    "Solitilo": "Soltilo Bright Stars FC",
    "Soliyilo": "Soltilo Bright Stars FC",
    "Lugzi": "Lugazi FC",
}

# ============================================================================
# Configuration Dictionaries
# ============================================================================


def get_merge_keys() -> list:
    """Return the standard merge keys for combining half-split data."""
    return MERGE_KEYS.copy()


def get_summary_statistics(metric_type: str = "all") -> list:
    """
    Get appropriate summary statistics based on metric type.

    Args:
        metric_type (str): One of 'all', 'volume', or 'intensity'

    Returns:
        list: List of statistics to compute
    """
    if metric_type == "volume":
        return SUMMARY_STATISTICS_VOLUME
    elif metric_type == "intensity":
        return SUMMARY_STATISTICS_INTENSITY
    else:
        return SUMMARY_STATISTICS


def get_metric_display_name(metric: str) -> str:
    """
    Get the human-readable display name for a metric.

    Args:
        metric (str): Internal metric name

    Returns:
        str: Display name, or metric name if not found
    """
    return METRIC_DISPLAY_NAMES.get(metric, metric)


def get_all_metrics() -> list:
    """Get all defined metrics (core + computed)."""
    return CORE_METRICS + list(COMPUTED_METRICS.keys())


def get_volume_and_intensity_metrics() -> tuple:
    """
    Get volume and intensity metric lists.

    Returns:
        tuple: (volume_metrics, intensity_metrics)
    """
    return VOLUME_METRICS, INTENSITY_METRICS
