"""
Premium Club Report Builder
Consolidates the best reporting features from Full and Season pipelines.
"""

import logging
from pathlib import Path
from typing import List
import pandas as pd
import matplotlib.pyplot as plt

from . import (
    get_matchday_stats,
    get_players_monitored_stats,
    get_metric_summary,
    get_top_players_by_metric,
    get_average_metrics_by_position,
    get_average_metrics_per_matchday,
    get_total_metrics_by_position,
    club_vs_season_comparison,
    positional_comparison_vs_season,
    get_speed_zone_breakdown,
    compute_coverage_summary,
    add_dataframe_as_table,
    add_introduction_section,
    add_methodology_section,
    add_key_concepts_section,
    add_challenges_section,
    add_future_plans_section,
    add_conclusion_section,
    embed_matplotlib_figure,
    save_document,
    create_report_document,
    add_table_of_contents,
)
from ..analysis.visualizations import (
    plot_players_per_matchday,
    plot_club_metrics_trend,
    plot_speed_zone_by_position,
)
from src.config import constants
from src.config.styles import ReportStyles
from .document_generation import (
    add_title_page,
    add_branded_header,
    set_landscape,
    set_portrait
)

logger = logging.getLogger(__name__)

class ClubReportBuilder:
    """
    Orchestrates the creation of a premium Word report for a single club.
    Merges hierarchical structure from FullPipeline with styling from SeasonPipeline.
    """
    
    def __init__(
        self,
        club: str,
        club_df: pd.DataFrame,
        season_df: pd.DataFrame,
        league: str,
        season: str,
        output_dir: Path,
        matchday_order: List[str],
        include_gk: bool = False
    ):
        self.club = club
        self.club_df = club_df
        self.season_df = season_df
        self.league = league
        self.season = season
        self.output_dir = output_dir
        self.matchday_order = matchday_order
        self.include_gk = include_gk
        
        # Determine half-season mark for trend charts (UPL: 15, FWSL: 11)
        self.half_md = 15 if league.lower() == "upl" else 11

    def build(self) -> str:
        """Execute the full report generation sequence."""
        logger.info(f"Building premium report for {self.club}...")
        
        # 1. Initialize Document
        doc = create_report_document(self.club)
        
        # 2. Apply Brand Styles
        ReportStyles.apply_normal_style(doc)
        ReportStyles.apply_heading_styles(doc)
        
        # 3. Add Front Matter
        # Note: logo_path is optional; set to None or provide a custom logo path.
        add_title_page(
            doc, 
            title=f"Performance Analysis Report: {self.club}",
            subtitle=f"{self.league} | {self.season} Season",
            logo_path=None
        )
        
        add_table_of_contents(doc)
        
        add_introduction_section(doc, self.club, season=self.season)
        doc.add_page_break()
        
        add_methodology_section(doc, season=self.season)
        doc.add_page_break()
        
        add_key_concepts_section(doc, season=self.season)
        doc.add_page_break()
        
        # 4. Season Results (Hierarchical Level 1)
        self._add_season_results_section(doc)
        doc.add_page_break()
        
        # 5. Club Metric Results (Hierarchical Level 1)
        self._add_metric_results_section(doc)
        # 6. Physical Performance Trends (Hierarchical Level 1)
        self._add_trends_section(doc)
        
        # 7. Speed Zone Analysis (Hierarchical Level 1)
        self._add_speed_zones_section(doc)
        doc.add_page_break()
        
        # 8. Comparison Analysis (Hierarchical Level 1)
        self._add_comparison_section(doc)
        doc.add_page_break()
        
        # 9. Closing Sections
        add_challenges_section(doc)
        doc.add_page_break()
        add_future_plans_section(doc, season=self.season)
        doc.add_page_break()
        add_conclusion_section(doc, season=self.season)
        
        # 10. Save
        filename = f"{self.club}_Report.docx"
        output_path = save_document(doc, str(self.output_dir), filename)
        logger.info(f"Report saved to: {output_path}")
        return output_path

    def _add_season_results_section(self, doc):
        add_branded_header(doc, "Season Results", icon_path=None)
        
        # Coverage Summary Paragraph
        coverage = compute_coverage_summary(self.club_df, self.matchday_order)
        doc.add_paragraph(
            f"Number of Matches Analysed: {coverage['matchdays_with_data']} "
            f"out of {coverage['total_matchdays_available']} matchdays. "
            f"Unique Players Monitored: {coverage['unique_players']} | "
            f"Total Player-Sessions: {coverage['total_sessions']}."
        )
        doc.add_paragraph()
        
        doc.add_heading("Match Day Usage", level=2)
        matchday_stats = get_matchday_stats(self.club_df, self.matchday_order)
        add_dataframe_as_table(doc, matchday_stats, caption=f"Matches Monitored for {self.club}")
        
        # MD Usage Chart
        fig = plot_players_per_matchday(matchday_stats, club_name=self.club)
        embed_matplotlib_figure(doc, fig, caption=f"Matchday Participation for {self.club}")
        plt.close(fig)
        
        doc.add_heading("Player Usage", level=2)
        players_stats = get_players_monitored_stats(self.club_df)
        add_dataframe_as_table(doc, players_stats, caption=f"Player Usage and Availability for {self.club}")

    def _add_metric_results_section(self, doc):
        add_branded_header(doc, "Club Metric Results", icon_path=None)
        
        volume_metrics = constants.VOLUME_METRICS
        intensity_metrics = constants.INTENSITY_METRICS
        display_names = constants.METRIC_DISPLAY_NAMES

        doc.add_heading("Overall Metric Summary", level=2)
        metric_summary = get_metric_summary(self.club_df, volume_metrics, intensity_metrics, display_names)
        add_dataframe_as_table(doc, metric_summary, caption=f"Overall Metric Summary for {self.club}")

        doc.add_heading("Top Players by Metric", level=2)
        top_players = get_top_players_by_metric(self.club_df, volume_metrics + intensity_metrics, display_names)
        add_dataframe_as_table(doc, top_players, caption=f"Top Players per Physical Metric for {self.club}")

        doc.add_heading("Average Metrics Per Position", level=2)
        pos_stats = get_average_metrics_by_position(self.club_df, volume_metrics, intensity_metrics, display_names)
        add_dataframe_as_table(doc, pos_stats, caption=f"Average Metrics Per Position for {self.club}")

        doc.add_heading("Total Accumulated Metrics by Position", level=2)
        total_pos_stats = get_total_metrics_by_position(self.club_df, volume_metrics, display_names)
        add_dataframe_as_table(doc, total_pos_stats, caption=f"Total Accumulated Distances for {self.club}")

    def _add_trends_section(self, doc):
        add_branded_header(doc, "Physical Performance Trends", icon_path=None)
        
        volume_metrics = constants.VOLUME_METRICS
        intensity_metrics = constants.INTENSITY_METRICS
        display_names = constants.METRIC_DISPLAY_NAMES
        
        avg_per_md_display, avg_per_md_plot = get_average_metrics_per_matchday(
            self.club_df, self.matchday_order, volume_metrics, intensity_metrics, display_names
        )
        
        add_dataframe_as_table(doc, avg_per_md_display, caption=f"Average Metrics Per Matchday for {self.club}")
        
        # 2x2 Grid Trend Plot on Landscape Page
        set_landscape(doc)
        
        fig = plot_club_metrics_trend(
            avg_per_md_plot, self.matchday_order,
            half_season_md=self.half_md, club_name=self.club
        )
        embed_matplotlib_figure(doc, fig, width_inches=9.0, caption=f"Physical Performance Trends (3-Match Rolling Average) for {self.club}")
        plt.close(fig)
        
        set_portrait(doc)

    def _add_speed_zones_section(self, doc):
        add_branded_header(doc, "Speed Zone Analysis", icon_path=None)
        zone_distances, zone_pct = get_speed_zone_breakdown(self.club_df, season=self.season)
        
        if not zone_distances.empty:
            doc.add_heading("Distance by Speed Zone (per Position)", level=2)
            add_dataframe_as_table(
                doc, zone_distances.reset_index().rename(columns={"general_position": "Position"}).round(2),
                caption="Distance Covered in Each Speed Zone"
            )
            
            doc.add_heading("Speed Zone Distribution Chart", level=2)
            fig = plot_speed_zone_by_position(zone_pct, club_name=self.club)
            embed_matplotlib_figure(doc, fig, caption=f"Speed Zone Distribution by Position for {self.club}")
            plt.close(fig)
        else:
            doc.add_paragraph("Speed zone data not available.")

    def _add_comparison_section(self, doc):
        doc.add_heading("League Comparison", level=1)
        
        volume_metrics = constants.VOLUME_METRICS
        intensity_metrics = constants.INTENSITY_METRICS
        display_names = constants.METRIC_DISPLAY_NAMES

        doc.add_heading("Comparison Against Season Averages", level=2)
        club_comparison = club_vs_season_comparison(
            self.club_df, self.season_df, volume_metrics, intensity_metrics, display_names
        )
        add_dataframe_as_table(doc, club_comparison, caption=f"{self.club} vs Season Averages")

        doc.add_heading("Positional Comparison vs Season", level=2)
        pos_comparison = positional_comparison_vs_season(
            self.club_df, self.season_df, volume_metrics, intensity_metrics, display_names
        )
        add_dataframe_as_table(doc, pos_comparison, caption="Positional Benchmarks vs League Averages")
