"""
Pipeline Orchestrator - Master Coordination Module

Coordinates all phases of the Match-Analysis pipeline:
  Phase 1: Configuration & Utilities (config, utils)
  Phase 2: Data Cleaning (raw CSV → cleaned CSV)
  Phase 3: Analysis (cleaned CSV → computed metrics)
  Phase 4: Reporting (metrics → aggregated summaries)
  Phase 5: Orchestration (coordinates all phases)

This module provides functions to:
  1. Execute individual phases
  2. Run full end-to-end pipeline
  3. Validate data at each stage
  4. Handle errors and provide logging
  5. Generate performance metrics

Author: FUFA Research, Science & Technology Unit
Version: 1.0
"""

import os
import sys
import time
import logging
from typing import Tuple, Dict, Any, Optional
from datetime import datetime

import pandas as pd

# Import all phases
from src.data import cleaning
from src.analysis import analysis
from src.reporting import (
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
)

from src.config import league_definitions, constants


# Configure logging
def setup_logging(log_dir: str = "./logs") -> logging.Logger:
    """Set up logging for pipeline execution."""
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(
        log_dir, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    return logging.getLogger(__name__)


logger = setup_logging()


class PipelineExecutor:
    """Orchestrates full pipeline execution."""

    def __init__(self, league: str, season: str = "2025/26", include_gk: bool = False):
        """
        Initialize pipeline executor.

        Args:
            league: 'fwsl' or 'upl'
            season: Football season (e.g., '2025/26')
            include_gk: Whether to include goalkeepers in main reports
        """
        self.league = league.lower()
        self.season = season
        self.include_gk = include_gk
        if self.league not in ["fwsl", "upl"]:
            raise ValueError(f"Invalid league: {league}. Must be 'fwsl' or 'upl'")

        self.execution_log = {
            "league": self.league,
            "start_time": time.time(),
            "end_time": None,
            "phases": {},
        }

    def phase_1_config(self) -> Dict[str, Any]:
        """
        Phase 1: Load configuration and utilities.

        Returns:
            Dictionary with league configuration
        """
        logger.info(f"[PHASE 1] Loading configuration for {self.league.upper()}")

        start = time.time()

        try:
            # Load league-specific configuration from LEAGUE_CONFIG
            league_config = league_definitions.LEAGUE_CONFIG[self.league]

            elapsed = time.time() - start
            logger.info(f"[PHASE 1] Configuration loaded in {elapsed:.2f}s")

            self.execution_log["phases"]["phase_1"] = {
                "status": "success",
                "elapsed_seconds": elapsed,
                "config_keys": list(league_config.keys()),
            }

            return league_config

        except Exception as e:
            logger.error(f"[PHASE 1] Configuration loading failed: {e}")
            self.execution_log["phases"]["phase_1"] = {
                "status": "error",
                "error": str(e),
            }
            raise

    def phase_2_cleaning(
        self, raw_path: str, league_config: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, str]:
        """
        Phase 2: Data cleaning pipeline.

        Args:
            raw_path: Path to raw CSV file
            league_config: Configuration from Phase 1

        Returns:
            Tuple of (cleaned_df, output_path)
        """
        logger.info(f"[PHASE 2] Starting data cleaning for {self.league.upper()}")
        logger.info(f"[PHASE 2] Input file: {raw_path}")

        start = time.time()

        try:
            cleaned_df, output_path = cleaning.clean_pipeline(
                raw_path=raw_path, league=self.league, season=self.season
            )

            elapsed = time.time() - start

            logger.info(f"[PHASE 2] Cleaning complete in {elapsed:.2f}s")
            logger.info(
                f"[PHASE 2] Rows: {len(cleaned_df)} | Columns: {len(cleaned_df.columns)}"
            )
            logger.info(f"[PHASE 2] Output saved to: {output_path}")

            self.execution_log["phases"]["phase_2"] = {
                "status": "success",
                "elapsed_seconds": elapsed,
                "input_rows": len(cleaned_df),
                "input_columns": len(cleaned_df.columns),
                "output_path": output_path,
            }

            return cleaned_df, output_path

        except Exception as e:
            logger.error(f"[PHASE 2] Data cleaning failed: {e}")
            self.execution_log["phases"]["phase_2"] = {
                "status": "error",
                "error": str(e),
            }
            raise

    def phase_3_analysis(
        self, cleaned_df: pd.DataFrame, league_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 3: Analysis and computations.

        Args:
            cleaned_df: Cleaned data from Phase 2
            league_config: Configuration from Phase 1

        Returns:
            Dictionary with analysis results
        """
        logger.info(f"[PHASE 3] Starting analysis computations")

        start = time.time()

        try:
            # Run analysis functions
            summary_stats = analysis.compute_summary_stats(cleaned_df)
            unique_players = analysis.unique_players_per_club(cleaned_df)
            players_per_club_md = analysis.players_per_club_per_matchday(cleaned_df)
            matchdays_per_club = analysis.matchdays_per_club(cleaned_df)
            club_coverage = analysis.club_coverage_analysis(cleaned_df, self.league)
            top_players = analysis.top_players_by_matchdays(cleaned_df, top_n=10)

            # Positional analysis (with default metric 'distance')
            positional_stats = analysis.compute_positional_stats(
                cleaned_df, metric="distance"
            )
            positional_comp = analysis.positional_comparison_all_metrics(cleaned_df)

            # Trends
            players_per_md = analysis.total_players_per_matchday(cleaned_df)
            clubs_per_md = analysis.clubs_per_matchday(cleaned_df)
            trend_metrics = analysis.matchday_trend_metrics(
                cleaned_df, metric="distance"
            )

            # Coverage grid
            coverage_grid = analysis.matchday_club_coverage_grid(cleaned_df)
            coverage_summary = analysis.coverage_summary(cleaned_df)

            elapsed = time.time() - start

            logger.info(f"[PHASE 3] Analysis complete in {elapsed:.2f}s")
            logger.info(f"[PHASE 3] Computed {9} analysis datasets")

            analysis_results = {
                "summary_stats": summary_stats,
                "unique_players": unique_players,
                "players_per_club_md": players_per_club_md,
                "matchdays_per_club": matchdays_per_club,
                "club_coverage": club_coverage,
                "top_players": top_players,
                "positional_stats": positional_stats,
                "positional_comparison": positional_comp,
                "players_per_md": players_per_md,
                "clubs_per_md": clubs_per_md,
                "trend_metrics": trend_metrics,
                "coverage_grid": coverage_grid,
                "coverage_summary": coverage_summary,
            }

            self.execution_log["phases"]["phase_3"] = {
                "status": "success",
                "elapsed_seconds": elapsed,
                "datasets_computed": 9,
                "analysis_keys": list(analysis_results.keys()),
            }

            return analysis_results

        except Exception as e:
            logger.error(f"[PHASE 3] Analysis failed: {e}")
            self.execution_log["phases"]["phase_3"] = {
                "status": "error",
                "error": str(e),
            }
            raise

    def phase_4_reporting(
        self,
        cleaned_df: pd.DataFrame,
        analysis_results: Dict[str, Any],
        output_dir: str = "./reports",
    ) -> Dict[str, str]:
        """
        Phase 4: Report generation for all clubs.

        Args:
            cleaned_df: Cleaned data from Phase 2
            analysis_results: Analysis results from Phase 3
            output_dir: Output directory for reports

        Returns:
            Dictionary mapping club names to report paths
        """
        logger.info(f"[PHASE 4] Starting report generation")
        
        # Filter GK if needed
        if not self.include_gk:
            logger.info("[PHASE 4] Excluding goalkeepers from reports")
            cleaned_df = cleaned_df[cleaned_df["general_position"] != "goalkeeper"].copy()

        start = time.time()

        try:
            volume_metrics = constants.VOLUME_METRICS
            intensity_metrics = constants.INTENSITY_METRICS
            metric_display_names = constants.METRIC_DISPLAY_NAMES
            matchday_order = analysis_results["matchday_order"]

            # Get unique clubs
            unique_clubs = cleaned_df["club_for"].unique()
            logger.info(f"[PHASE 4] Generating reports for {len(unique_clubs)} clubs")

            report_paths = {}

            for club in unique_clubs:
                try:
                    club_df = cleaned_df[cleaned_df["club_for"] == club].copy()

                    # Create document
                    doc = create_report_document(club)

                    # Add standardized sections
                    add_introduction_section(doc, club, season=self.season)
                    doc.add_page_break()
                    add_methodology_section(doc, season=self.season)
                    doc.add_page_break()
                    add_key_concepts_section(doc, season=self.season)
                    doc.add_page_break()

                    # Add data tables
                    doc.add_heading("Season Results", level=1)
                    doc.add_heading("Match Day Usage", level=2)

                    matchday_stats = get_matchday_stats(club_df, matchday_order)
                    add_dataframe_as_table(doc, matchday_stats)
                    doc.add_paragraph()

                    doc.add_heading("Player Usage", level=1)
                    players_stats = get_players_monitored_stats(club_df)
                    add_dataframe_as_table(doc, players_stats)
                    doc.add_paragraph()

                    doc.add_heading("Club Metric Results", level=1)
                    metric_summary = get_metric_summary(
                        club_df, volume_metrics, intensity_metrics, metric_display_names
                    )
                    add_dataframe_as_table(doc, metric_summary)
                    doc.add_paragraph()

                    doc.add_heading("Top Players by Metric", level=1)
                    top_players_table = get_top_players_by_metric(
                        club_df,
                        volume_metrics + intensity_metrics,
                        metric_display_names,
                    )
                    add_dataframe_as_table(doc, top_players_table)
                    doc.add_paragraph()

                    doc.add_heading("Average Metrics Per Position", level=1)
                    position_stats = get_average_metrics_by_position(
                        club_df, volume_metrics, intensity_metrics, metric_display_names
                    )
                    add_dataframe_as_table(doc, position_stats)
                    doc.add_paragraph()

                    doc.add_heading("Club Comparison", level=1)
                    club_comparison = club_vs_season_comparison(
                        club_df,
                        cleaned_df,
                        volume_metrics,
                        intensity_metrics,
                        metric_display_names,
                    )
                    add_dataframe_as_table(doc, club_comparison)
                    doc.add_paragraph()

                    # Add challenges and future plans
                    doc.add_page_break()
                    add_challenges_section(doc)
                    doc.add_page_break()
                    add_future_plans_section(doc, season=self.season)
                    doc.add_page_break()
                    add_conclusion_section(doc, season=self.season)

                    # Save report
                    report_path = save_document(doc, output_dir, f"{club}_report.docx")
                    report_paths[club] = report_path
                    logger.info(f"[PHASE 4] Generated report: {club}")

                except Exception as e:
                    logger.warning(
                        f"[PHASE 4] Failed to generate report for {club}: {e}"
                    )
                    continue

            elapsed = time.time() - start

            logger.info(f"[PHASE 4] Report generation complete in {elapsed:.2f}s")
            logger.info(f"[PHASE 4] Generated {len(report_paths)} reports")

            self.execution_log["phases"]["phase_4"] = {
                "status": "success",
                "elapsed_seconds": elapsed,
                "reports_generated": len(report_paths),
                "output_directory": output_dir,
            }

            return report_paths

        except Exception as e:
            logger.error(f"[PHASE 4] Report generation failed: {e}")
            self.execution_log["phases"]["phase_4"] = {
                "status": "error",
                "error": str(e),
            }
            raise

    def execute_full_pipeline(
        self, raw_path: str, output_dir: str = "./output"
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end pipeline.

        Args:
            raw_path: Path to raw CSV input file
            output_dir: Base output directory

        Returns:
            Execution summary with all results
        """
        self.execution_log["start_time"] = datetime.now().isoformat()
        start_total = time.time()

        logger.info("=" * 70)
        logger.info(f"PIPELINE EXECUTION START - {self.league.upper()}")
        logger.info("=" * 70)

        try:
            # Phase 1: Configuration
            league_config = self.phase_1_config()

            # Phase 2: Cleaning
            cleaned_df, clean_output_path = self.phase_2_cleaning(
                raw_path, league_config
            )

            # Phase 3: Analysis
            analysis_results = self.phase_3_analysis(cleaned_df, league_config)

            # Phase 4: Reporting
            reporting_output_dir = os.path.join(
                output_dir, "reports", self.league.upper()
            )
            report_paths = self.phase_4_reporting(
                cleaned_df, analysis_results, reporting_output_dir
            )

            elapsed_total = time.time() - start_total
            self.execution_log["end_time"] = datetime.now().isoformat()
            self.execution_log["total_elapsed_seconds"] = elapsed_total
            self.execution_log["status"] = "success"

            logger.info("=" * 70)
            logger.info(f"PIPELINE EXECUTION COMPLETE - {elapsed_total:.2f}s")
            logger.info(f"Reports generated: {len(report_paths)}")
            logger.info(f"Output directory: {reporting_output_dir}")
            logger.info("=" * 70)

            return {
                "status": "success",
                "league": self.league,
                "total_elapsed_seconds": elapsed_total,
                "cleaned_data_path": clean_output_path,
                "report_paths": report_paths,
                "analysis_summary": {
                    "unique_clubs": len(report_paths),
                    "total_rows_processed": len(cleaned_df),
                },
            }

        except Exception as e:
            self.execution_log["status"] = "error"
            self.execution_log["error"] = str(e)

            logger.error("=" * 70)
            logger.error(f"PIPELINE EXECUTION FAILED: {e}")
            logger.error("=" * 70)

            return {"status": "error", "league": self.league, "error": str(e)}


def execute_pipeline(
    league: str, raw_path: str, output_dir: str = "./output", season: str = "2025/26", include_gk: bool = False
) -> Dict[str, Any]:
    """
    Execute full pipeline for specified league.

    High-level convenience function.

    Args:
        league: 'fwsl' or 'upl'
        raw_path: Path to raw CSV
        output_dir: Output directory base

    Returns:
        Execution summary
    """
    executor = PipelineExecutor(league, season=season, include_gk=include_gk)
    return executor.execute_full_pipeline(raw_path, output_dir)
