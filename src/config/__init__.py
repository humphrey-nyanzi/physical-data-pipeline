"""
Configuration package for FUFA Match Analysis pipeline.

Exposes league definitions, constants, and configuration utilities.
"""

from .league_definitions import (
    FWSL_CLUBS,
    UPL_CLUBS,
    LEAGUE_CONFIG,
    get_league_clubs,
    get_league_session_pattern,
    get_league_config,
    POSITION_MAPPING,
    MATCH_LOCATIONS,
    MATCH_RESULTS,
    MATCH_LEAGUE_TYPES,
)

from .constants import (
    CORE_METRICS,
    VOLUME_METRICS,
    INTENSITY_METRICS,
    ACCELERATION_ZONE_COLUMNS,
    DECELERATION_ZONE_COLUMNS,
    COMPUTED_METRICS,
    MERGE_KEYS,
    MIN_SESSION_DURATION_MINUTES,
    MIN_SESSION_DISTANCE_KM,
    OUTLIER_IQR_MULTIPLIER,
    SPARSE_COLUMN_THRESHOLD,
    CLUB_CORRECTIONS_FWSL,
    CLUB_CORRECTIONS_UPL,
    SUMMARY_STATISTICS,
    METRIC_DISPLAY_NAMES,
    get_merge_keys,
    get_summary_statistics,
    get_metric_display_name,
    get_all_metrics,
    get_volume_and_intensity_metrics,
)

__all__ = [
    # League definitions
    "FWSL_CLUBS",
    "UPL_CLUBS",
    "LEAGUE_CONFIG",
    "get_league_clubs",
    "get_league_session_pattern",
    "get_league_config",
    "POSITION_MAPPING",
    "MATCH_LOCATIONS",
    "MATCH_RESULTS",
    "MATCH_LEAGUE_TYPES",
    # Metrics and constants
    "CORE_METRICS",
    "VOLUME_METRICS",
    "INTENSITY_METRICS",
    "ACCELERATION_ZONE_COLUMNS",
    "DECELERATION_ZONE_COLUMNS",
    "COMPUTED_METRICS",
    "MERGE_KEYS",
    "MIN_SESSION_DURATION_MINUTES",
    "MIN_SESSION_DISTANCE_KM",
    "OUTLIER_IQR_MULTIPLIER",
    "SPARSE_COLUMN_THRESHOLD",
    "CLUB_CORRECTIONS_FWSL",
    "CLUB_CORRECTIONS_UPL",
    "SUMMARY_STATISTICS",
    "METRIC_DISPLAY_NAMES",
    "get_merge_keys",
    "get_summary_statistics",
    "get_metric_display_name",
    "get_all_metrics",
    "get_volume_and_intensity_metrics",
]
