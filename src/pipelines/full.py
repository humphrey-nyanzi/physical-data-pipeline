"""
Full Pipeline - Complete 4-Phase Analysis

Migrated from legacy src/pipeline/orchestrator.py:PipelineExecutor

Phases:
    1. Configuration: Load league configuration
    2. Data Cleaning: Raw CSV → Cleaned CSV
    3. Analysis: Compute statistical metrics
    4. Reporting: Generate per-club Word documents
"""

import argparse
import logging
import re
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd

from src.pipelines.base import AnalysisPipeline
from src.data import cleaning
from src.analysis import analysis
from src.reporting.club_report_builder import ClubReportBuilder
from src.reporting.season_report_builder import SeasonReportBuilder
from src.analysis import season_analysis
from src.config import league_definitions
from src.utils.console import Console
import yaml

logger = logging.getLogger(__name__)


class FullPipeline(AnalysisPipeline):
    """
    Complete 4-phase pipeline: Config → Clean → Analyze → Report.
    
    Replaces legacy src/pipeline/orchestrator.py
    """

    @property
    def name(self) -> str:
        return "full"

    @classmethod
    def register_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """Register CLI arguments for full pipeline."""
        parser.add_argument(
            "--league",
            required=True,
            choices=["mens_league", "womens_league"],
            help="League identifier (mens_league or womens_league)"
        )
        parser.add_argument(
            "--input",
            required=True,
            type=Path,
            help="Path to raw GPS tracking CSV input file"
        )
        parser.add_argument(
            "--output",
            default=Path("Output"),
            type=Path,
            help="Base output directory"
        )
        parser.add_argument(
            "--season",
            default="2025/26",
            help="Football season (e.g., 2025/26)"
        )
        parser.add_argument(
            "--include-gk",
            action="store_true",
            help="Include goalkeepers in main reports"
        )
        parser.add_argument(
            "--skip-club-reports",
            action="store_true",
            help="Skip generation of individual club reports"
        )
        parser.add_argument(
            "--timeframe",
            default="season",
            choices=["season", "half_season"],
            help="Timeframe for League Report (season/half_season)"
        )
        parser.add_argument(
            "--gk",
            action="store_true",
            help="Include/Generate goalkeeper reports"
        )

    def validate_args(self) -> bool:
        """Validate input file exists and league is valid."""
        if not self.args.input.exists():
            self.log(f"Input file not found: {self.args.input}", logging.ERROR)
            return False
        
        if self.args.league.lower() not in ["mens_league", "womens_league"]:
            self.log(f"Invalid league: {self.args.league}", logging.ERROR)
            return False
        
        return True

    def run(self) -> bool:
        """Execute full 4-phase pipeline."""
        league = self.args.league.lower()
        season = self.args.season.replace("/", "-")
        include_gk = self.args.include_gk
        
        self.log(f"Starting Full Pipeline for {league.upper()} ({season})")
        
    def run(self) -> bool:
        """Execute full 4-phase pipeline."""
        league = self.args.league.lower()
        season = self.args.season.replace("/", "-")
        include_gk = self.args.include_gk
        
        Console.section(f"Full Analysis  ·  {league.upper()}  ·  {self.args.season}")
        self.log(f"Starting Full Pipeline for {league.upper()} ({season})")
        
        try:
            # Build rejection audit directory
            rejection_dir = str(Path("logs") / season / league.upper() / "rejected" / self.run_id)

            # ===== PHASE 1: Configuration =====
            Console.section("Phase 1 · Loading Configuration")
            self.log("Phase 1: Loading Configuration...")
            self._phase_1_config(league)
            Console.section_end()
            
            # ===== PHASE 2: Data Cleaning =====
            Console.section("Phase 2 · Data Cleaning & Audit")
            self.log("Phase 2: Data Cleaning...")
            cleaned_df, _ = self._phase_2_cleaning(
                str(self.args.input), league, self.args.season, rejection_dir
            )
            Console.stat("Rows retained", len(cleaned_df))
            self.update_metrics({"total_rows_cleaned": len(cleaned_df)})
            
            # Save cleaned data for reference
            clean_dir = self.output_dir / "01_cleaned"
            clean_dir.mkdir(parents=True, exist_ok=True)
            clean_filename = f"{league.upper()}_{season}_Full_Cleaned_{self.run_id}.csv"
            clean_path = clean_dir / clean_filename
            cleaned_df.to_csv(clean_path, index=False)
            Console.saved("Run copy (cleaned)", str(clean_path))
            Console.section_end()
            
            # ===== PHASE 3: Analysis =====
            Console.section("Phase 3 · Processing Metrics")
            self.log("Phase 3: Analysis...")
            analysis_results = self._phase_3_analysis(cleaned_df)
            Console.stat("Analysis datasets", len(analysis_results))
            Console.section_end()
            
            # ===== PHASE 4: Reporting =====
            Console.section("Phase 4 · Generating Reports")
            self.log("Phase 4: Reporting...")
            
            # 1. League-Wide Report (Season/Half-Season)
            Console.info(f"Generating League-Wide {self.args.timeframe.title()} Report...")
            self._phase_4_league_reporting(cleaned_df, league)
            
            # 2. Individual Club Reports
            if not self.args.skip_club_reports:
                Console.info("Generating Individual Club Documents...")
                report_count = self._phase_4_club_reporting(
                    cleaned_df, league, season, include_gk or self.args.gk, analysis_results
                )
                Console.stat("Club reports generated", report_count)
            else:
                Console.info("Club reports skipped (--skip-club-reports)")
            
            Console.section_end()
            return True
            
        except Exception as e:
            self.log(f"Pipeline failed: {e}", logging.ERROR)
            return False

    # =========================================================================
    # PHASE 1: Configuration
    # =========================================================================
    
    def _phase_1_config(self, league: str) -> Dict[str, Any]:
        """
        Load league configuration.
        
        Args:
            league: 'mens_league' or 'womens_league'
            
        Returns:
            League configuration dictionary
            
        Raises:
            KeyError if league not found in LEAGUE_CONFIG
        """
        try:
            league_config = league_definitions.LEAGUE_CONFIG[league]
            self.log(f"  Loaded config for {league.upper()}")
            return league_config
        except KeyError as e:
            self.log(f"Config loading failed: {e}", logging.ERROR)
            raise

    # =========================================================================
    # PHASE 2: Data Cleaning
    # =========================================================================
    
    def _phase_2_cleaning(
        self, raw_path: str, league: str, season: str, rejection_dir: str = ""
    ) -> Tuple[pd.DataFrame, str]:
        """Execute data cleaning pipeline."""
        try:
            cleaned_df, output_path = cleaning.clean_pipeline(
                raw_path=raw_path,
                league=league,
                season=season,
                run_id=self.run_id,
                rejection_log_dir=rejection_dir
            )
            return cleaned_df, output_path
        except Exception as e:
            self.log(f"Cleaning failed: {e}", logging.ERROR)
            raise

    # =========================================================================
    # PHASE 3: Analysis
    # =========================================================================
    
    def _phase_3_analysis(self, cleaned_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute analysis metrics (summary statistics, positional analysis, etc.).
        
        Args:
            cleaned_df: Cleaned dataframe from Phase 2
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Compute matchday order for later use in reporting
            matchday_order = self._compute_matchday_order(cleaned_df)
            
            # Run analysis functions
            results = {
                "matchday_order": matchday_order,
                "summary_stats": analysis.compute_summary_stats(cleaned_df),
                "unique_players": analysis.unique_players_per_club(cleaned_df),
                "players_per_club_md": analysis.players_per_club_per_matchday(cleaned_df),
                "matchdays_per_club": analysis.matchdays_per_club(cleaned_df),
                "top_players": analysis.top_players_by_matchdays(cleaned_df, top_n=10),
            }
            return results
        except Exception as e:
            self.log(f"Analysis failed: {e}", logging.ERROR)
            raise

    def _compute_matchday_order(self, cleaned_df: pd.DataFrame) -> list:
        """
        Extract and sort matchdays from cleaned dataframe.
        
        Handles formats like 'Md1', 'MD1', 'Md22', etc.
        
        Args:
            cleaned_df: Cleaned dataframe with 'match_day' column
            
        Returns:
            Sorted list of unique matchdays
        """
        if "match_day" not in cleaned_df.columns:
            return []
        
        mds = cleaned_df["match_day"].unique()
        
        def get_md_value(x: str) -> int:
            """Extract numeric matchday value."""
            match = re.search(r"(\d+)", str(x))
            return int(match.group(1)) if match else 999
        
        return sorted(mds, key=get_md_value)

    # =========================================================================
    # PHASE 4: Report Generation
    # =========================================================================
    
    def _phase_4_club_reporting(
        self,
        cleaned_df: pd.DataFrame,
        league: str,
        season: str,
        include_gk: bool,
        analysis_results: Dict[str, Any]
    ) -> int:
        """Generate per-club premium Word reports using ClubReportBuilder."""
        reports_dir = self.output_dir / "02_club_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        matchday_order = analysis_results.get("matchday_order", [])
        unique_clubs = cleaned_df["club_for"].unique()
        report_count = 0

        for club in unique_clubs:
            try:
                club_df = cleaned_df[cleaned_df["club_for"] == club].copy()
                if not include_gk:
                    club_df = club_df[club_df["general_position"] != "goalkeeper"].copy()

                builder = ClubReportBuilder(
                    club=club,
                    club_df=club_df,
                    season_df=cleaned_df,
                    league=league,
                    season=season,
                    output_dir=reports_dir,
                    matchday_order=matchday_order,
                    include_gk=include_gk
                )
                builder.build()
                report_count += 1
            except Exception as e:
                self.log(f"  Warning: Failed to generate report for {club}: {e}", logging.WARNING)

        return report_count

    def _phase_4_league_reporting(self, df: pd.DataFrame, league: str) -> bool:
        """Generate league-wide summary report."""
        try:
            timeframe = self.args.timeframe
            self.log(f"  Generating League-Wide {timeframe.title()} Report...")

            # Get half_season_limit from config (consistent with SeasonPipeline)
            config_path = Path(__file__).parents[1] / "config" / "analysis_config.yaml"
            half_season_limit = 15
            if config_path.exists():
                with open(config_path) as f:
                    cfg = yaml.safe_load(f)
                    half_season_limit = cfg.get('season_report', {}).get('half_season_matchday', {}).get(league, 15)

            # Filter for League-Wide context
            filtered_df = season_analysis.filter_data_by_timeframe(df, timeframe, league, half_season_limit)

            if filtered_df.empty:
                self.log("  Warning: No data found after timeframe filtering.", logging.WARNING)
                return False

            report_dir = self.output_dir / "03_league_report"
            report_dir.mkdir(parents=True, exist_ok=True)

            builder = SeasonReportBuilder(
                filtered_df, league, timeframe, report_dir, half_season_limit,
                season=self.args.season, gk_mode=self.args.gk, run_id=self.run_id
            )
            builder.build_report()
            return True
        except Exception as e:
            self.log(f"  Warning: League reporting failed: {e}", logging.WARNING)
            return False
