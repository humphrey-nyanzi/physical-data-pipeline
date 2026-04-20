"""
Configuration package for Match Analysis pipeline.

Exposes league definitions, constants, and configuration utilities.
"""

from .league_definitions import (
    WOMENS_LEAGUE_CLUBS,
    MENS_LEAGUE_CLUBS,
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
    CLUB_CORRECTIONS_WOMENS,
    CLUB_CORRECTIONS_MENS,
    SUMMARY_STATISTICS,
    METRIC_DISPLAY_NAMES,
    get_merge_keys,
    get_summary_statistics,
    get_metric_display_name,
    get_all_metrics,
    get_volume_and_intensity_metrics,
)

import yaml
from pathlib import Path
from typing import Any, Dict, Optional


# Cached configuration for analysis_config()
_analysis_config_cache: Optional[Dict[str, Any]] = None


def analysis_config(reload: bool = False) -> Dict[str, Any]:
    """
    Load and return the analysis configuration from analysis_config.yaml.

    The result is cached by default. Pass reload=True to force a fresh read.
    """
    global _analysis_config_cache
    if reload or _analysis_config_cache is None:
        config_path = Path(__file__).parent / "analysis_config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as f:
            _analysis_config_cache = yaml.safe_load(f) or {}
    return _analysis_config_cache


__all__ = [
    # League definitions
    "WOMENS_LEAGUE_CLUBS",
    "MENS_LEAGUE_CLUBS",
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
    "CLUB_CORRECTIONS_WOMENS",
    "CLUB_CORRECTIONS_MENS",
    "SUMMARY_STATISTICS",
    "METRIC_DISPLAY_NAMES",
    "get_merge_keys",
    "get_summary_statistics",
    "get_metric_display_name",
    "get_all_metrics",
    "get_volume_and_intensity_metrics",
    "analysis_config",
]
