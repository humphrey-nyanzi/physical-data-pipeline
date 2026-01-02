"""
Utilities package for FUFA Match Analysis.

Consolidates reusable functions for text processing, normalization,
styling, and document formatting.
"""

from .text_cleaning import (
    clean_text,
    normalize_name,
    best_match,
    normalize_club_names,
    normalize_positions,
    fix_player_name_format,
    extract_player_info,
    apply_text_cleaning_to_columns,
)

from .styling import (
    style_table_for_docs,
    style_metric_summary_table,
    apply_chart_theme,
    get_usage_tier_color,
    create_usage_tier_color_map,
    format_metric_label,
    format_club_name,
    get_cell_color_rgb,
    USAGE_TIER_COLORS,
    CHART_COLORS,
    STACKED_COLORS,
)

__all__ = [
    # Text cleaning functions
    "clean_text",
    "normalize_name",
    "best_match",
    "normalize_club_names",
    "normalize_positions",
    "fix_player_name_format",
    "extract_player_info",
    "apply_text_cleaning_to_columns",
    # Styling functions
    "style_table_for_docs",
    "style_metric_summary_table",
    "apply_chart_theme",
    "get_usage_tier_color",
    "create_usage_tier_color_map",
    "format_metric_label",
    "format_club_name",
    "get_cell_color_rgb",
    # Color constants
    "USAGE_TIER_COLORS",
    "CHART_COLORS",
    "STACKED_COLORS",
]
