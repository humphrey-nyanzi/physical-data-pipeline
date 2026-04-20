"""
Reporting Module

Consolidates report generation logic for creating comprehensive club-level
GPS performance reports.

Submodules:
    - report_builder: Data aggregation and metric computation
    - document_generation: DOCX document creation and formatting
"""

from .report_builder import (
    get_matchday_stats,
    get_players_monitored_stats,
    get_metric_summary,
    get_top_players_by_metric,
    get_average_metrics_by_position,
    get_average_metrics_per_matchday,
    club_vs_season_comparison,
    positional_comparison_vs_season,
    get_speed_zone_breakdown,
    compute_coverage_summary,
    get_total_metrics_by_position,
)

from .document_generation import (
    fmt_cell_value,
    add_dataframe_as_table,
    add_introduction_section,
    add_methodology_section,
    add_key_concepts_section,
    add_challenges_section,
    add_future_plans_section,
    add_conclusion_section,
    embed_matplotlib_figure,
    embed_matplotlib_axis,
    save_document,
    create_report_document,
    add_table_of_contents,
)

__all__ = [
    # report_builder
    "get_matchday_stats",
    "get_players_monitored_stats",
    "get_metric_summary",
    "get_top_players_by_metric",
    "get_average_metrics_by_position",
    "get_average_metrics_per_matchday",
    "club_vs_season_comparison",
    "positional_comparison_vs_season",
    "get_speed_zone_breakdown",
    "compute_coverage_summary",
    "get_total_metrics_by_position",
    # document_generation
    "fmt_cell_value",
    "add_dataframe_as_table",
    "add_introduction_section",
    "add_methodology_section",
    "add_key_concepts_section",
    "add_challenges_section",
    "add_future_plans_section",
    "add_conclusion_section",
    "embed_matplotlib_figure",
    "embed_matplotlib_axis",
    "save_document",
    "create_report_document",
    "add_table_of_contents",
]
