import argparse
import logging
from pathlib import Path
from typing import List, Tuple
import pandas as pd

from src.pipelines.base import AnalysisPipeline
from src.utils.text_parsing import parse_matchday, parse_session_info
from src.processing.gps_aggregation import aggregate_halves, extract_metrics, compute_derived_metrics
from src.reporting.weekly_gps_report import WeeklyGPSReportBuilder
from src.config import constants, league_definitions
from src.data.cleaning import filter_by_position, RejectionLog
from src.utils.console import Console

logger = logging.getLogger(__name__)

class WeeklyPipeline(AnalysisPipeline):
    """
    Pipeline for generating Weekly GPS Reports.
    """
    
    @property
    def name(self) -> str:
        return "weekly"
    
    @classmethod
    def register_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """Register arguments for weekly report."""
        parser.add_argument("--md", type=int, required=True, help="Matchday Number (e.g., 12)")
        parser.add_argument("--input", type=Path, default=Path("data/01_raw/weekly"), 
                           help="Input directory containing GPS tracking CSVs")
        parser.add_argument("--output", type=Path, default=Path("reports"), 
                           help="Output directory for reports")
        parser.add_argument("--season", default="2025/2026", help="Season string (e.g., 2025/2026)")
        parser.add_argument("--league", default="mens_league", choices=["mens_league", "womens_league"], help="League (mens_league or womens_league)")
        parser.add_argument("--gk", action="store_true", help="Generate additional goalkeeper report")

    def validate_args(self) -> bool:
        """Validate input directory exists."""
        self.input_dir = self.args.input
        
        # Override output_dir from args if provided specific to this pipeline
        if hasattr(self.args, 'output'):
            self.output_dir = self.args.output

        if not self.input_dir.exists():
            self.log(f"Input directory not found: {self.input_dir}", logging.ERROR)
            Console.error(f"Input directory not found: {self.input_dir}")
            return False
            
        # Validate matchday logic
        from src.config.league_definitions import get_league_config
        try:
            config = get_league_config(self.args.league)
            max_md = config.get("max_matchdays", 30)
            if self.args.md > max_md:
                err = f"Matchday {self.args.md} exceeds league maximum of {max_md} for {self.args.league.upper()}."
                self.log(f"LOGICAL ERROR: {err}", logging.ERROR)
                Console.error(err)
                return False
        except Exception as e:
            self.log(f"League configuration error: {e}", logging.ERROR)
            Console.error(f"League configuration error: {e}")
            return False

        return True

    def run(self) -> bool:
        """Execute the weekly report generation pipeline."""
        matchday_number = self.args.md
        league = self.args.league.lower()
        season_str = self.args.season.replace("/", "-")
        league_prefix = league.upper()
        
        Console.section(f"Weekly Report  ·  {league.upper()}  ·  MD{matchday_number}")
        self.log(f"Starting Weekly Report for MD{matchday_number}")
        
        # Initialize Rejection Log
        rejection_dir = str(Path("logs") / season_str / league.upper() / "rejected" / self.run_id)
        rlog = RejectionLog(run_id=self.run_id, output_dir=rejection_dir)

        # 1. Find and Filter Files
        csv_files = self._find_csv_files()
        
        if not csv_files:
            Console.warning("No new CSV files found to process.")
            self.log("No new CSV files found to process.", logging.WARNING)
            return False

        # 2. Process Files
        processed_data = self._process_files(csv_files, matchday_number, rlog)
        
        if not processed_data:
            Console.warning("No valid data extracted for this matchday.")
            self.log("No valid data extracted for this matchday.", logging.WARNING)
            rlog.flush()
            return False
            
        df_all_list, uploading_teams, missing_teams, files_to_rename = processed_data
        
        if not df_all_list:
             Console.warning("No data found for the target teams.")
             self.log("No DataFrames generated.", logging.WARNING)
             rlog.flush()
             return False
             
        # Combined DataFrame
        df_all = pd.concat(df_all_list, ignore_index=True)
        
        # Compute derived metrics (acc/dec totals and rates)
        df_all = compute_derived_metrics(df_all)
        
        Console.info(f"Loaded {len(df_all):,} player sessions from {len(csv_files)} files")
        self.update_metrics({"total_players_raw": len(df_all)})
        
        # 3. Apply Strict Filtering (60 min, 2 km)
        Console.section("Phase 2 · Activity Filtering")
        initial_count = len(df_all)
        
        # Track rejected rows for the audit
        fail_mask = (df_all['Duration'] < constants.MIN_SESSION_DURATION_MINUTES) | \
                    (df_all['Distance (km)'] < constants.MIN_SESSION_DISTANCE_KM)
        
        if fail_mask.any():
            rlog.record(df_all[fail_mask], "activity_filter", f"Distance < {constants.MIN_SESSION_DISTANCE_KM}km OR Duration < {constants.MIN_SESSION_DURATION_MINUTES}min")

        df_all = df_all[~fail_mask].copy()
        
        filtered_count = len(df_all)
        Console.stat("Players retained", filtered_count, initial_count)
        
        self.update_metrics({
            "players_retained": filtered_count,
            "players_filtered_out": initial_count - filtered_count,
            "uploading_teams": list(uploading_teams),
            "missing_teams": list(missing_teams)
        })

        # 4. Generate Reports
        Console.section("Phase 3 · Generating Reports")
        
        # Pass 1: Main Report (Excluding GKs)
        df_field = filter_by_position(df_all, "field")
        Console.info(f"Generating Main Weekly Report (MD{matchday_number}) ...")
        
        main_filename = f"{league_prefix}_{season_str}_Weekly_MD{matchday_number}_Report_{self.run_id}.docx"
        main_output_path = self.output_dir / main_filename
        
        try:
            builder = WeeklyGPSReportBuilder(matchday_number, season=self.args.season, league=self.args.league)
            builder.build_report(df_field, uploading_teams, missing_teams)
            builder.save(str(main_output_path))
            Console.saved("Main Report", str(main_output_path))
            self.log(f"Main Report Saved: {main_output_path}")
        except Exception as e:
            Console.error(f"Failed to generate main report: {e}")
            self.log(f"Failed to generate main report: {e}", logging.ERROR)
            rlog.flush()
            return False

        # Pass 2: GK Report (If requested)
        if self.args.gk:
            df_gk = filter_by_position(df_all, "gk")
            if not df_gk.empty:
                Console.info("Generating Goalkeeper Weekly Report ...")
                gk_filename = f"{league_prefix}_{season_str}_Weekly_GK_MD{matchday_number}_Report_{self.run_id}.docx"
                gk_output_path = self.output_dir / gk_filename
                try:
                    gk_builder = WeeklyGPSReportBuilder(matchday_number, season=self.args.season, gk_mode=True, league=self.args.league)
                    gk_builder.build_report(df_gk, uploading_teams, missing_teams)
                    gk_builder.save(str(gk_output_path))
                    Console.saved("GK Report", str(gk_output_path))
                    self.log(f"GK Report Saved: {gk_output_path}")
                except Exception as e:
                    Console.error(f"Failed to generate GK report: {e}")
                    self.log(f"Failed to generate GK report: {e}", logging.ERROR)
            else:
                Console.info("No goalkeeper data available (skipping GK report).")
                self.log("No goalkeeper data available to generate report.", logging.INFO)
            
        Console.section_end()

        # 5. Cleanup & Audit
        self._rename_files(files_to_rename)
        rlog.flush()
        
        Console.success("Weekly Pipeline Complete!")
        return True

    def _find_csv_files(self) -> List[Path]:
        """Find CSV files in input directory that haven't been processed."""
        all_files = list(self.input_dir.glob("*.csv"))
        # Exclude processed files
        csv_files = [f for f in all_files if not f.name.startswith("PROCESSED_")]
        self.log(f"Found {len(csv_files)} new CSV files.")
        return csv_files

    def _process_files(self, csv_files: List[Path], target_md: int, rlog: RejectionLog = None) -> Tuple:
        """Process list of CSV files."""
        processed_dfs = []
        files_to_rename = []
        uploading_teams = set()
        opponents = set()
        
        for csv_file in csv_files:
            try:
                # Load raw data
                df_raw = pd.read_csv(csv_file)
                if 'Session Title' not in df_raw.columns:
                    self.log(f"Skipping {csv_file.name}: 'Session Title' col missing", logging.WARNING)
                    if rlog is not None:
                        rlog.record(df_raw, "file_check", f"'Session Title' missing in {csv_file.name}")
                    continue
                
                # Track if we extracted any valid data from this file
                file_has_valid_data = False
                
                # Group by Session Title to handle multiple teams/matches in one file
                for session_title, df_session in df_raw.groupby('Session Title'):
                    
                    # 1. Check Matchday
                    md_num = parse_matchday(session_title)
                    if md_num != target_md:
                        if rlog is not None:
                            rlog.record(df_session, "matchday_filter", f"MD{md_num} != Target MD{target_md}")
                        continue
                        
                    # 2. Parse Info
                    session_info = parse_session_info(session_title)
                    if not session_info:
                        self.log(f"Skipping session '{session_title}' in {csv_file.name}: Invalid format", logging.WARNING)
                        if rlog is not None:
                            rlog.record(df_session, "parse_error", "Invalid Session Title format")
                        continue
                        
                    # 3. Extract & Clean
                    # Pass the session subset to extract metrics
                    df_clean = extract_metrics(df_session, csv_file.name, log_func=lambda m, *a: None)
                    if df_clean.empty:
                        if rlog is not None:
                            rlog.record(df_session, "extract_metrics", "Requirement check failed (missing cols or names)")
                        continue
                        
                    # 4. Aggregate Halves
                    df_agg = aggregate_halves(df_clean, log_func=lambda m, *a: None)
                    
                    if not df_agg.empty:
                        # Standardize Team Names using fuzzy matching
                        official_clubs = [c for c in league_definitions.get_league_clubs(self.args.league, self.args.season)]
                        from src.utils.text_cleaning import best_match

                        raw_t1 = session_info.get('team1', '').strip()
                        raw_t2 = session_info.get('team2', '').strip()
                        
                        t1_clean = best_match(raw_t1, official_clubs, return_original=False) if raw_t1 else None
                        t2_clean = best_match(raw_t2, official_clubs, return_original=False) if raw_t2 else None

                        # CRITICAL: If uploading team (Team 1) is invalid, discard data
                        if raw_t1 and t1_clean is None:
                            msg = f"Team '{raw_t1}' not found in official list. Skipping session."
                            self.log(f"Discrepancy: {msg}", logging.WARNING)
                            if rlog is not None:
                                rlog.record(df_agg, "club_normalization", f"Unrecognized team: {raw_t1}")
                            continue

                        # Update session info with clean names
                        if t1_clean:
                            session_info['team1'] = t1_clean
                        if t2_clean:
                            session_info['team2'] = t2_clean
                        elif raw_t2:
                            self.log(f"Discrepancy: Opponent '{raw_t2}' not found in official list.", logging.WARNING)

                        # Add metadata
                        for key, val in session_info.items():
                            df_agg[key] = val
                        
                        processed_dfs.append(df_agg)
                        file_has_valid_data = True
                        
                        if t1_clean:
                            uploading_teams.add(t1_clean.upper())
                        if t2_clean:
                            opponents.add(t2_clean.upper())
                        
                        Console.info(f"Processed '{session_title}': {len(df_agg)} players")
                
                if file_has_valid_data:
                    files_to_rename.append(csv_file)

            except Exception as e:
                self.log(f"Error processing {csv_file.name}: {e}", logging.ERROR)
                Console.error(f"Error processing {csv_file.name}: {e}")

        
        # Determine missing teams based on FULL league roster
        # Pass the season explicitly to get correct roster
        all_clubs = set(c.upper() for c in league_definitions.get_league_clubs(self.args.league, self.args.season))
        
        # Filter uploading teams to only those in the official list to ensure counts match
        valid_uploading_teams = uploading_teams.intersection(all_clubs)
        unrecognized_teams = uploading_teams - all_clubs
        
        if unrecognized_teams:
            self.log(f"Unrecognized teams found in data (excluded from compliance count): {', '.join(unrecognized_teams)}", logging.WARNING)
            
        missing_teams = all_clubs - valid_uploading_teams
        
        return processed_dfs, valid_uploading_teams, missing_teams, files_to_rename
        
    def _rename_files(self, files: List[Path]):
        """Rename processed files with PROCESSED_ prefix."""
        self.log(f"Renaming {len(files)} processed files...")
        for f in files:
            try:
                new_name = f.with_name(f"PROCESSED_{f.name}")
                f.rename(new_name)
                self.log(f"  Renamed: {f.name} -> {new_name.name}")
            except Exception as e:
                self.log(f"  Failed to rename {f.name}: {e}", logging.ERROR)
