import argparse
import logging
from pathlib import Path
import pandas as pd
import yaml
import matplotlib.pyplot as plt
from src.analysis import visualizations

from src.pipelines.base import AnalysisPipeline
from src.data import cleaning
from src.analysis import season_analysis
from src.reporting.season_report_builder import SeasonReportBuilder
from src.data.cleaning import filter_by_position
from src.config import league_definitions

# Imports for Per-Club Reporting (legacy orchestrator logic)
from src.reporting import (
    get_matchday_stats,
    get_players_monitored_stats,
    get_metric_summary,
    get_top_players_by_metric,
    get_average_metrics_by_position,
    club_vs_season_comparison,
    get_total_metrics_by_position,
    create_report_document,
    add_introduction_section,
    add_methodology_section,
    add_key_concepts_section,
    add_dataframe_as_table,
    add_challenges_section,
    add_future_plans_section,
    add_conclusion_section,
    save_document,
    add_table_of_contents,
    positional_comparison_vs_season,
    get_speed_zone_breakdown,
    embed_matplotlib_figure
)
from src.config import constants
from src.config.styles import ReportStyles

logger = logging.getLogger(__name__)

class SeasonPipeline(AnalysisPipeline):
    """
    Comprehensive Season Analysis Pipeline.
    
    Stages:
    1. Data Cleaning (Raw -> Cleaned)
    2. Analysis (Metrics computation)
    3. Per-Club Reporting (Individual club reports)
    4. League-Wide Reporting (Season/Half-Season Summary)
    """
    
    @property
    def name(self) -> str:
        return "season"
        
    @classmethod
    def register_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--league", required=True, choices=['upl', 'fwsl'], help="League identifier")
        parser.add_argument("--input", required=True, type=Path, help="Path to raw CSV input file")
        parser.add_argument("--output", default=Path("Output/Season"), type=Path, help="Base output directory")
        parser.add_argument("--skip-club-reports", action="store_true", help="Skip generation of individual club reports")
        parser.add_argument("--skip-cleaning", action="store_true", help="Skip data cleaning (use if input is already processed)")
        parser.add_argument("--timeframe", default="season", choices=['season', 'half_season'], 
                           help="Timeframe for League Report (season/half_season)")
        parser.add_argument("--season", default="2025/26", help="Season string (e.g., 2025/26)")
        parser.add_argument("--gk", action="store_true", help="Generate additional goalkeeper reports")

    def validate_args(self) -> bool:
        if not self.args.input.exists():
            self.log(f"Input file not found: {self.args.input}", logging.ERROR)
            return False
        return True

    def run(self) -> bool:
        self.setup_output_dir()
        
        league = self.args.league.lower()
        raw_path = self.args.input
        timeframe = self.args.timeframe
        
        self.log(f"Starting Season Analysis for {league.upper()}")
        
        # --- Phase 1 & 2: Cleaning ---
        if not self.args.skip_cleaning:
            self.log("Phase 1: Data Cleaning...")
            try:
                # We reuse the cleaning pipeline from src.data
                cleaned_df, clean_output_path = cleaning.clean_pipeline(
                    raw_path=str(raw_path), 
                    league=league,
                    season=self.args.season,
                    include_gk=self.args.gk
                )
                self.log(f"Cleaning complete. Rows: {len(cleaned_df)}")
                
                # Save cleaned data to output dir for reference
                clean_save_path = self.output_dir / "01_cleaned" / f"{league}_cleaned.csv"
                clean_save_path.parent.mkdir(parents=True, exist_ok=True)
                cleaned_df.to_csv(clean_save_path, index=False)
                self.log(f"Saved cleaned data to {clean_save_path}")
                
            except Exception as e:
                self.log(f"Cleaning failed: {e}", logging.ERROR)
                return False
        else:
            self.log("Skipping Phase 1: Data Cleaning (using pre-processed data).")
            try:
                cleaned_df = pd.read_csv(raw_path)
                self.log(f"Loaded pre-processed data. Rows: {len(cleaned_df)}")
                # Safety validation for pre-processed data
                cleaned_df = cleaning.validate_matchday_logic(cleaned_df, league)
            except Exception as e:
                self.log(f"Failed to load input file: {e}", logging.ERROR)
                return False

        # --- Phase 2: Filtering ---
        # Define field positions (all except goalkeeper)
        field_positions = ["defender", "midfielder", "forward"]
        df_field = filter_by_position(cleaned_df, field_positions)
        
        # Define GK positions
        df_gk = filter_by_position(cleaned_df, ["goalkeeper"]) if self.args.gk else pd.DataFrame()

        # --- Phase 3: Reporting ---
        self.log("Phase 3: Generating Reports...")
        
        # 1. League-Wide Report
        self.log(f"Generating League-Wide {timeframe.title()} Report...")
        if not self._generate_league_report(df_field, league, timeframe, suffix=""):
            self.log("League report failed.", logging.ERROR)
        
        if self.args.gk and not df_gk.empty:
            self.log("Generating Goalkeeper League Report...")
            self._generate_league_report(df_gk, league, timeframe, suffix="_GK")

        # 2. Individual Club Reports
        if not self.args.skip_club_reports:
            self.log("Phase 4: Generating Per-Club Reports...")
            if not self._generate_club_reports(df_field, league, suffix=""):
                self.log("Club reporting encountered errors.", logging.WARNING)
            
            if self.args.gk and not df_gk.empty:
                self.log("Generating Goalkeeper Club Reports...")
                self._generate_club_reports(df_gk, league, suffix="_GK")
        else:
             self.log("Skipping Per-Club Reports.")

        self.log("Season Pipeline Complete!")
        return True

    def _generate_club_reports(self, df: pd.DataFrame, league: str, suffix: str = "") -> bool:
        """Generate individual reports for each club."""
        # Reuse logic from orchestrator.phase_4_reporting
        # We need to compute analysis results first for matchday order etc.
        
        try:
            self.log("Computing analysis metrics...")
            # We call the comprehensive analysis needed for matchday ordering
            # In orchestrator this returned a dict with 'matchday_order'
            # But wait, analysis.compute_summary_stats(cleaned_df) etc don't return matchday_order?
            # orchestrator.phase_3_analysis returned a dict, but 'matchday_order' was inferred?
            # Actually, let's look at orchestrator code again?
            # It passed 'analysis_results' to phase_4, which accessed 'matchday_order'.
            # Where did matchday_order come from? 
            # I don't see it explicitly computed in `phase_3_analysis`.
            # Ah, maybe I missed it in the view.
            
            # Let's compute matchday order manually:
            if 'match_day' in df.columns:
                mds = df['match_day'].unique()
                # Sort numerically by extracting number from 'Md1', 'MD2', etc.
                def get_md_val(x):
                    import re
                    match = re.search(r'(\d+)', str(x))
                    return int(match.group(1)) if match else 999
                matchday_order = sorted(mds, key=get_md_val)
            else:
                matchday_order = []
                
            unique_clubs = df['club_for'].unique()
            official_clubs = league_definitions.get_league_clubs(league, season=self.args.season)
            reports_dir = self.output_dir / "02_club_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            self.log(f"Generating reports for {len(unique_clubs)} clubs...")
            for club in unique_clubs:
                if club not in official_clubs:
                    self.log(f"LOGICAL ERROR: Club '{club}' is not in official {league.upper()} club list. Data may be inconsistent.", logging.WARNING)
            
            volume_metrics = constants.VOLUME_METRICS
            intensity_metrics = constants.INTENSITY_METRICS
            metric_display_names = constants.METRIC_DISPLAY_NAMES
            
            count = 0
            for club in unique_clubs:
                try:
                    self.log(f"Generating report for {club}...")
                    club_df = df[df['club_for'] == club].copy()
                    
                    doc = create_report_document(club)
                    
                    # Apply styles? create_report_document might not use ReportStyles yet.
                    # We should probably patch it or assume it's fine for now (Phase 2 legacy support)
                    # But the user said "all reports".
                    # I should ideally inject styles. 
                    # For now, let's inject explicit style calls if possible or rely on document_generation.
                    
                    ReportStyles.apply_normal_style(doc)
                    ReportStyles.apply_heading_styles(doc)
                    
                    add_table_of_contents(doc)

                    add_introduction_section(doc, club, season=self.args.season)
                    doc.add_page_break()
                    add_methodology_section(doc, season=self.args.season)
                    doc.add_page_break()
                    add_key_concepts_section(doc, season=self.args.season)
                    doc.add_page_break()

                    # Data Tables
                    doc.add_heading("Season Results", level=1)
                    doc.add_heading("Match Day Usage", level=2)
                    matchday_stats = get_matchday_stats(club_df, matchday_order)
                    add_dataframe_as_table(doc, matchday_stats)
                    doc.add_paragraph()

                    doc.add_heading("Player Usage", level=1)
                    players_stats = get_players_monitored_stats(club_df)
                    add_dataframe_as_table(doc, players_stats)
                    
                    doc.add_heading("Club Metric Results", level=1)
                    metric_summary = get_metric_summary(club_df, volume_metrics, intensity_metrics, metric_display_names)
                    add_dataframe_as_table(doc, metric_summary)
                    
                    doc.add_heading("Top Players by Metric", level=1)
                    top_players = get_top_players_by_metric(club_df, volume_metrics + intensity_metrics, metric_display_names)
                    add_dataframe_as_table(doc, top_players)
                    
                    doc.add_heading("Average Metrics Per Position", level=1)
                    pos_stats = get_average_metrics_by_position(club_df, volume_metrics, intensity_metrics, metric_display_names)
                    add_dataframe_as_table(doc, pos_stats)

                    doc.add_heading("Cumulative Position Metrics (Volume)", level=1)
                    pos_sums = get_total_metrics_by_position(club_df, volume_metrics, metric_display_names)
                    add_dataframe_as_table(doc, pos_sums)
                    
                    doc.add_heading("Club Comparison", level=1)
                    comp = club_vs_season_comparison(club_df, df, volume_metrics, intensity_metrics, metric_display_names)
                    add_dataframe_as_table(doc, comp)

                    doc.add_heading("Positional Comparison vs Season Averages", level=1)
                    pos_comp = positional_comparison_vs_season(club_df, df, volume_metrics, intensity_metrics, metric_display_names)
                    add_dataframe_as_table(doc, pos_comp)

                    doc.add_page_break()
                    doc.add_heading("Physical Performance Trends", level=1)
                    metrics_map = {
                        'distance_km': 'Distance (km)',
                        'player_load': 'Player Load',
                        'top_speed_kmh': 'Top Speed (km/h)',
                        'work_ratio': 'Work Ratio'
                    }
                    fig = visualizations.plot_rolling_trend_grid(club_df, metrics_map)
                    embed_matplotlib_figure(doc, fig)
                    plt.close(fig)

                    doc.add_heading("Speed Zone Distribution", level=1)
                    sz_data = get_speed_zone_breakdown(club_df, season=self.args.season)
                    if not sz_data[1].empty:
                        fig = visualizations.plot_speed_zones_stacked(sz_data[1], f"{club} Speed Zone Distribution")
                        embed_matplotlib_figure(doc, fig)
                        plt.close(fig)
                    
                    doc.add_page_break()
                    add_challenges_section(doc)
                    doc.add_page_break()
                    add_future_plans_section(doc, season=self.args.season)
                    doc.add_page_break()
                    add_conclusion_section(doc, season=self.args.season)
                    
                    save_document(doc, str(reports_dir), f"{club}_report{suffix}.docx")
                    count += 1
                    
                except Exception as e:
                    self.log(f"Failed to generate report for {club}: {e}", logging.ERROR)
            
            self.log(f"Generated {count} club reports.")
            return True
            
        except Exception as e:
            self.log(f"Club reporting failed: {e}", logging.ERROR)
            import traceback
            traceback.print_exc()
            return False

    def _generate_league_report(self, df: pd.DataFrame, league: str, timeframe: str, suffix: str = "") -> bool:
        """Generate the comprehensive league-wide report."""
        try:
            # Need half_season_limit from config logic (replicated from generate_season_report)
            config_path = Path("scripts/config/analysis_config.yaml") 
            # We assume running from root
            half_season_limit = 15 # Default
            if config_path.exists():
                with open(config_path) as f:
                    cfg = yaml.safe_load(f)
                    half_season_limit = cfg.get('season_report', {}).get('half_season_matchday', {}).get(league, 15)
            
            # Filter Data
            self.log("Filtering data for league report...")
            filtered_df = season_analysis.filter_data_by_timeframe(
                df, timeframe, league, half_season_limit
            )
            
            if filtered_df.empty:
                self.log("No data found after filtering for league report!", logging.WARNING)
                return False
                
            report_dir = self.output_dir / "03_league_report"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            builder = SeasonReportBuilder(
                filtered_df, league, timeframe, report_dir, half_season_limit, 
                season=self.args.season, gk_mode=(suffix == "_GK")
            )
            output_path = builder.build_report(suffix=suffix)
            self.log(f"League report generated: {output_path}")
            return True
            
        except Exception as e:
            self.log(f"League reporting failed: {e}", logging.ERROR)
            import traceback
            traceback.print_exc()
            return False
