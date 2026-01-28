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
from src.data.cleaning import filter_by_position

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
        parser.add_argument("--input", type=Path, default=Path("data/matchday_csvs"), 
                           help="Input directory containing Catapult CSVs")
        parser.add_argument("--output", type=Path, default=Path("Output/Weekly"), 
                           help="Output directory for reports")
        parser.add_argument("--season", default="2025/2026", help="Season string (e.g., 2025/2026)")
        parser.add_argument("--league", default="upl", choices=["upl", "fwsl"], help="League (upl or fwsl)")
        parser.add_argument("--gk", action="store_true", help="Generate additional goalkeeper report")

    def validate_args(self) -> bool:
        """Validate input directory exists."""
        self.input_dir = self.args.input
        
        # Override output_dir from args if provided specific to this pipeline
        if hasattr(self.args, 'output'):
            self.output_dir = self.args.output

        if not self.input_dir.exists():
            self.log(f"Input directory not found: {self.input_dir}", logging.ERROR)
            return False
            
        # Validate matchday logic
        from src.config.league_definitions import get_league_config
        try:
            config = get_league_config(self.args.league)
            max_md = config.get("max_matchdays", 30)
            if self.args.md > max_md:
                self.log(
                    f"LOGICAL ERROR: Matchday {self.args.md} exceeds league maximum of {max_md} for {self.args.league.upper()}.",
                    logging.ERROR
                )
                return False
        except Exception as e:
            self.log(f"League configuration error: {e}", logging.ERROR)
            return False

        return True

    def run(self) -> bool:
        """Execute the weekly report generation pipeline."""
        self.setup_output_dir()
        matchday_number = self.args.md
        
        self.log(f"Starting Weekly Report for MD{matchday_number}")
        
        # 1. Find and Filter Files
        csv_files = self._find_csv_files()
        
        if not csv_files:
            self.log("No new CSV files found to process.", logging.WARNING)
            return False

        # 2. Process Files
        processed_data = self._process_files(csv_files, matchday_number)
        
        if not processed_data:
            self.log("No valid data extracted for this matchday.", logging.WARNING)
            return False
            
        df_all_list, uploading_teams, missing_teams, files_to_rename = processed_data
        
        if not df_all_list:
             self.log("No DataFrames generated.", logging.WARNING)
             return False
             
        # Combined DataFrame
        df_all = pd.concat(df_all_list, ignore_index=True)
        
        # Compute derived metrics (acc/dec totals and rates)
        df_all = compute_derived_metrics(df_all)
        
        self.log(f"TOTAL PLAYERS: {len(df_all)}")
        
        # 3. Apply Strict Filtering (60 min, 2 km)
        initial_count = len(df_all)
        df_all = df_all[
            (df_all['Duration'] >= constants.MIN_SESSION_DURATION_MINUTES) &
            (df_all['Distance (km)'] >= constants.MIN_SESSION_DISTANCE_KM)
        ].copy()
        
        filtered_count = len(df_all)
        self.log(f"Filtered players: {filtered_count} retained (from {initial_count} initial)")

        # 4. Generate Reports
        filename_season = self.args.season.replace("/", "-")
        league_prefix = self.args.league.upper()
        
        # Pass 1: Main Report (Excluding GKs)
        df_field = filter_by_position(df_all, "field")
        main_output_path = self.output_dir / f"{league_prefix} {filename_season} MD{matchday_number} Catapult Data Report.docx"
        
        try:
            builder = WeeklyGPSReportBuilder(matchday_number, season=self.args.season, league=self.args.league)
            builder.build_report(df_field, uploading_teams, missing_teams)
            builder.save(str(main_output_path))
            self.log(f"Main Report Saved: {main_output_path}")
        except Exception as e:
            self.log(f"Failed to generate main report: {e}", logging.ERROR)
            return False

        # Pass 2: GK Report (If requested)
        if self.args.gk:
            df_gk = filter_by_position(df_all, "gk")
            if not df_gk.empty:
                gk_output_path = self.output_dir / f"{league_prefix} {filename_season} MD{matchday_number} Goalkeeper Data Report.docx"
                try:
                    # We can use the same builder or a slightly modified one for GK
                    gk_builder = WeeklyGPSReportBuilder(matchday_number, season=self.args.season, gk_mode=True, league=self.args.league)
                    # We might want to customize build_report for GK later, but for now just pass filtered data
                    gk_builder.build_report(df_gk, uploading_teams, missing_teams)
                    gk_builder.save(str(gk_output_path))
                    self.log(f"GK Report Saved: {gk_output_path}")
                except Exception as e:
                    self.log(f"Failed to generate GK report: {e}", logging.ERROR)
            else:
                self.log("No goalkeeper data available to generate report.", logging.INFO)
            
        # 5. Cleanup (Rename processed files)
        self._rename_files(files_to_rename)
        
        return True

    def _find_csv_files(self) -> List[Path]:
        """Find CSV files in input directory that haven't been processed."""
        all_files = list(self.input_dir.glob("*.csv"))
        # Exclude processed files
        csv_files = [f for f in all_files if not f.name.startswith("PROCESSED_")]
        self.log(f"Found {len(csv_files)} new CSV files.")
        return csv_files

    def _process_files(self, csv_files: List[Path], target_md: int) -> Tuple:
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
                    continue
                
                # Track if we extracted any valid data from this file
                file_has_valid_data = False
                
                # Group by Session Title to handle multiple teams/matches in one file
                for session_title, df_session in df_raw.groupby('Session Title'):
                    
                    # 1. Check Matchday
                    md_num = parse_matchday(session_title)
                    if md_num != target_md:
                        continue
                        
                    # 2. Parse Info
                    session_info = parse_session_info(session_title)
                    if not session_info:
                        self.log(f"Skipping session '{session_title}' in {csv_file.name}: Invalid format", logging.WARNING)
                        continue
                        
                    # 3. Extract & Clean
                    # Pass the session subset to extract metrics
                    df_clean = extract_metrics(df_session, csv_file.name, log_func=lambda m: None)
                    if df_clean.empty:
                        continue
                        
                    # 4. Aggregate Halves
                    df_agg = aggregate_halves(df_clean, log_func=lambda m: None)
                    
                    if not df_agg.empty:
                        # Standardize Team Names using fuzzy matching
                        # We use the OFFICIAL roster for this season to find the best match
                        official_clubs = [c for c in league_definitions.get_league_clubs(self.args.league, self.args.season)]
                        from src.utils.text_cleaning import best_match

                        raw_t1 = session_info.get('team1', '').strip()
                        raw_t2 = session_info.get('team2', '').strip()
                        
                        # Apply fuzzy matching
                        # Return None if no good match found (e.g. "Juventus")
                        t1_clean = best_match(raw_t1, official_clubs, return_original=False) if raw_t1 else None
                        t2_clean = best_match(raw_t2, official_clubs, return_original=False) if raw_t2 else None

                        # CRITICAL: If uploading team (Team 1) is invalid, discard data
                        if raw_t1 and t1_clean is None:
                            self.log(f"Discrepancy: Team '{raw_t1}' not found in official list. Skipping session '{session_title}'.", logging.WARNING)
                            continue

                        # Update session info with clean names
                        if t1_clean:
                            session_info['team1'] = t1_clean
                        
                        if t2_clean:
                            session_info['team2'] = t2_clean
                        elif raw_t2:
                            # Log warning for opponent but keep raw name (don't discard session)
                            self.log(f"Discrepancy: Opponent '{raw_t2}' not found in official list.", logging.WARNING)

                        # Add metadata (Team, Matchday, etc.)
                        for key, val in session_info.items():
                            df_agg[key] = val
                        
                        processed_dfs.append(df_agg)
                        file_has_valid_data = True
                        
                        # Track Teams (using the cleaned names)
                        if t1_clean:
                            uploading_teams.add(t1_clean.upper())
                        if t2_clean:
                            opponents.add(t2_clean.upper())
                        
                        # Note: Validation against official_clubs is now implicit due to best_match logic
                        
                        self.log(f"Processed Session '{session_title}': {len(df_agg)} players")
                
                # Only rename if we successfully processed at least one session
                if file_has_valid_data:
                    files_to_rename.append(csv_file)

            except Exception as e:
                self.log(f"Error processing {csv_file.name}: {e}", logging.ERROR)

        
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
