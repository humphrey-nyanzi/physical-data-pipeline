"""
Season Report Builder Module

Orchestrates the creation of the Season/Half-Season report.
Uses analysis statistics and visualizations to populate a DOCX template.
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

from ..analysis import season_analysis
from ..analysis import visualizations
from . import document_generation as doc_gen
from src.config.styles import ReportStyles
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class SeasonReportBuilder:
    def __init__(
        self, 
        df: pd.DataFrame, 
        league: str, 
        timeframe: str, 
        output_dir: Path,
        half_season_md: int,
        season: str = "2025/26",
        gk_mode: bool = False
    ):
        self.df = df
        self.league = league
        self.timeframe = timeframe
        self.output_dir = output_dir
        self.half_season_md = half_season_md
        self.season = season
        self.gk_mode = gk_mode
        
        # Load config
        self.config_path = Path(__file__).parents[2] / "scripts" / "config" / "analysis_config.yaml"
        # Use simpler relative path if possible or keep as is? 
        # Path(__file__).parents[2] is src/.. -> root?
        # scripts/config is relative to root.
        
        # Safe loading
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
             self.config = {} # improved error handling during refactor

        self.doc = Document()
        self._configure_styles()
    
    def _configure_styles(self):
        """Apply centralized styles."""
        ReportStyles.apply_normal_style(self.doc)
        ReportStyles.apply_heading_styles(self.doc)
        
    def build_report(self, suffix: str = ""):
        """Execute the full report generation pipeline."""
        logger.info(f"Building {self.timeframe} report for {self.league} (suffix: {suffix})...")
        
        # 1. Title Page
        base_title = f"{self.league.upper()} {self.timeframe.replace('_', ' ').title()} Report"
        title = f"Goalkeeper {base_title}" if self.gk_mode else base_title
        self._add_title_page(title)
        
        # Insert Table of Contents
        doc_gen.add_table_of_contents(self.doc)
        
        # 2. Introduction
        self._add_intro_section()
        
        # 3. Usage Analysis
        self._add_usage_section()
        
        # 4. Performance Analysis
        self._add_performance_section()
        
        # 5. Conclusion
        self._add_conclusion_section()
        
        # Save
        filename = f"{self.league}_{self.timeframe}_report{suffix}.docx"
        output_path = self.output_dir / filename
        self.doc.save(output_path)
        logger.info(f"Report saved to {output_path}")
        return output_path

    def _add_title_page(self, title: str):
        """Create a custom title page."""
        self.doc.add_paragraph('FUFA Research, Science and Technology Unit', style='Title')
        
        self.doc.add_paragraph("\n" * 4)
        
        p = self.doc.add_paragraph(style='Title')
        run = p.add_run(f"{title}\nSeason: {self.season}")
        run.bold = True
        
        self.doc.add_paragraph("\n" * 4)
        
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"Generated on: {pd.Timestamp.now().strftime('%B %d, %Y')}")
        self.doc.add_page_break()

    def _add_intro_section(self):
        self.doc.add_heading("1. Introduction", level=1)
        self.doc.add_paragraph(
            f"This report presents a comprehensive analysis of the {self.league.upper()} "
            f"competitions for the {self.season} {self.timeframe.replace('_', ' ')}. "
            "The data collected via Catapult wearable technology provides insights into the physical demands "
            "and performance characteristics of the league."
        )
        self.doc.add_paragraph(
            "The report is divided into two main sections: Usage Analysis, which details data coverage "
            "and participation, and Performance Analysis, which delves into the physical metrics."
        )

    # ========================================================================
    # USAGE SECTION
    # ========================================================================
    def _add_usage_section(self):
        self.doc.add_heading("2. Usage Analysis", level=1)
        self.doc.add_paragraph(
            "This section outlines the extent of data collection, highlighting club participation "
            "and consistency across matchdays."
        )
        
        usage_stats = season_analysis.get_usage_stats(self.df)
        
        # 2.1 Unique Players per Club
        self.doc.add_heading("2.1 Player Participation per Club", level=2)
        top_club = usage_stats['unique_players_per_club'].iloc[0]
        doc_gen.add_dataframe_as_table(self.doc, usage_stats['unique_players_per_club'])
        self.doc.add_paragraph(
            f"{top_club['club_for']} had the highest number({top_club['unique_players']}) of unique players analyzed, "
            "indicating significant squad rotation or broad data capture."
        )
        
        # 2.2 Participation Trends (Players & Clubs per Matchday)
        self.doc.add_heading("2.2 Matchday Participation Trends", level=2)
        
        # Plot Players per MD
        fig = visualizations.plot_league_trend(
            usage_stats['players_per_md_trend'], 'total_players', 'Total Unique Players Captured'
        )
        doc_gen.embed_matplotlib_figure(self.doc, fig)
        plt.close(fig)
        
        # Plot Clubs per MD
        fig = visualizations.plot_league_trend(
            usage_stats['clubs_per_md_trend'], 'total_clubs', 'Total Clubs Submitting Data'
        )
        doc_gen.embed_matplotlib_figure(self.doc, fig)
        plt.close(fig)
        
        self.doc.add_paragraph(
            "The charts above illustrate the volume of data captured over time. "
            "Peaks typically correspond to full matchday rounds where most clubs uploaded data."
        )
        
        # 2.3 Coverage Heatmap
        self.doc.add_heading("2.3 Data Coverage Grid", level=2)
        self.doc.add_paragraph(
            "The grid below visualizes which clubs uploaded data for each matchday (Green = Uploaded)."
        )
        grid_df = season_analysis.get_coverage_grid(self.df)
        fig = visualizations.plot_coverage_heatmap(grid_df)
        doc_gen.embed_matplotlib_figure(self.doc, fig)
        plt.close(fig)

    # ========================================================================
    # PERFORMANCE SECTION
    # ========================================================================
    def _add_performance_section(self):
        self.doc.add_heading("3. Performance Analysis", level=1)
        self.doc.add_paragraph(
            "This section analyzes the physical output of players, categorized by volume "
            "(total work done) and intensity (rate of work)."
        )
        
        perf_stats = season_analysis.get_performance_stats(self.df)
        
        # 3.1 Metric Distributions (Histograms)
        self.doc.add_heading("3.1 Metric Distributions", level=2)
        self.doc.add_paragraph("Distribution of key volume (Distance) and intensity (Player Load) metrics.")
        
        # Distance Histogram
        fig = visualizations.plot_metric_histogram(self.df, 'distance_km', 'Total Distance (km)')
        doc_gen.embed_matplotlib_figure(self.doc, fig)
        plt.close(fig)
        
        # Player Load Histogram
        fig = visualizations.plot_metric_histogram(self.df, 'player_load', 'Player Load')
        doc_gen.embed_matplotlib_figure(self.doc, fig)
        plt.close(fig)
        
        # 3.2 Aggregated Metrics
        self.doc.add_heading("3.2 League Averages", level=2)
        self.doc.add_heading("Volume Metrics", level=3)
        doc_gen.add_dataframe_as_table(self.doc, perf_stats['volume'].round(2))
        
        self.doc.add_heading("Intensity Metrics", level=3)
        doc_gen.add_dataframe_as_table(self.doc, perf_stats['intensity'].round(2))
        
        # 3.3 Positional Breakdown
        self.doc.add_heading("3.3 League Averages by Position", level=2)
        from . import report_builder
        from ..config import constants
        pos_stats = report_builder.get_average_metrics_by_position(
            self.df, 
            constants.VOLUME_METRICS, 
            constants.INTENSITY_METRICS, 
            constants.METRIC_DISPLAY_NAMES
        )
        doc_gen.add_dataframe_as_table(self.doc, pos_stats.round(2))
        
        # 3.4 Club Level Comparisons
        self.doc.add_heading("3.4 Club Level Comparisons", level=2)
        club_stats = season_analysis.get_club_comparison(self.df)
        
        if 'volume' in club_stats:
            self.doc.add_heading("Volume Metrics by Club", level=3)
            vol_df = club_stats['volume'].rename(columns=constants.METRIC_DISPLAY_NAMES).reset_index().rename(columns={'club_for': 'Club'})
            doc_gen.add_dataframe_as_table(self.doc, vol_df.round(2))
            
        if 'intensity' in club_stats:
            self.doc.add_heading("Intensity Metrics by Club", level=3)
            int_df = club_stats['intensity'].rename(columns=constants.METRIC_DISPLAY_NAMES).reset_index().rename(columns={'club_for': 'Club'})
            doc_gen.add_dataframe_as_table(self.doc, int_df.round(2))
        
        # 3.5 Contextual Analysis
        self.doc.add_heading("3.5 Contextual Analysis", level=2)
        context_stats = season_analysis.get_contextual_stats(self.df)
        
        if 'location' in context_stats:
            self.doc.add_heading("Home vs Away", level=3)
            # Plot specific metric comparison, e.g. PL
            fig = visualizations.plot_context_comparison(
                context_stats['location'], 'player_load', 'Player Load', 'Location'
            )
            doc_gen.embed_matplotlib_figure(self.doc, fig)
            plt.close(fig)
            
        if 'result' in context_stats:
            self.doc.add_heading("Match Result (Win/Draw/Loss)", level=3)
            fig = visualizations.plot_context_comparison(
                context_stats['result'], 'distance_km', 'Distance (km)', 'Result'
            )
            doc_gen.embed_matplotlib_figure(self.doc, fig)
            plt.close(fig)
            
        # 3.6 Rolling Trends
        self.doc.add_heading("3.6 Seasonal Metric Trends", level=2)
        self.doc.add_paragraph("Rolling averages (3-matchday window) for key performance indicators.")
        metrics_map = {
            'distance_km': 'Distance (km)',
            'player_load': 'Player Load',
            'top_speed_kmh': 'Top Speed (km/h)',
            'work_ratio': 'Work Ratio'
        }
        fig = visualizations.plot_rolling_trend_grid(self.df, metrics_map)
        doc_gen.embed_matplotlib_figure(self.doc, fig)
        plt.close(fig)
        
        # 3.7 Speed Zones
        self.doc.add_heading("3.7 Speed Zone Analysis", level=2)
        sz_stats = season_analysis.get_speed_zone_stats(self.df)
        if 'dist_pct' in sz_stats:
            self.doc.add_heading("Distance in Speed Zones", level=3)
            fig = visualizations.plot_speed_zones_stacked(
                sz_stats['dist_pct'], "Distance Distribution by Speed Zone"
            )
            doc_gen.embed_matplotlib_figure(self.doc, fig)
            plt.close(fig)
            
        self._add_record_breakers()
        
    def _add_record_breakers(self):
        self.doc.add_heading("3.8 Record Breakers", level=2)
        self.doc.add_paragraph(
            "The following tables highlight the highest single-match values recorded for key metrics."
        )
        
        metrics = ['distance_km', 'top_speed_kmh', 'player_load', 'sprint_distance_m']
        records = season_analysis.get_max_performers(self.df, metrics)
        
        for metric, df in records.items():
            if not df.empty:
                top_p = df.iloc[0]
                self.doc.add_paragraph(
                    f"Highest {metric}: {top_p['p_name']} ({top_p['club_for']}) - {top_p[metric]:.2f}"
                )
                safe_df = df.copy() # Avoid modification
                doc_gen.add_dataframe_as_table(self.doc, safe_df.round(2))

    def _add_conclusion_section(self):
        doc_gen.add_conclusion_section(self.doc, season=self.season)
