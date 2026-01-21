import os
import argparse
import logging
from pathlib import Path
from typing import List, Tuple
import pandas as pd

from src.pipelines.base import AnalysisPipeline
from src.utils.text_parsing import parse_matchday, parse_session_info
from src.processing.gps_aggregation import aggregate_halves, extract_metrics
from src.reporting.weekly_gps_report import WeeklyGPSReportBuilder

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

    def validate_args(self) -> bool:
        """Validate input directory exists."""
        self.input_dir = self.args.input
        
        # Override output_dir from args if provided specific to this pipeline
        if hasattr(self.args, 'output'):
            self.output_dir = self.args.output

        if not self.input_dir.exists():
            self.log(f"Input directory not found: {self.input_dir}", logging.ERROR)
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
        self.log(f"TOTAL PLAYERS: {len(df_all)}")
        
        # 3. Generate Report
        output_path = self.output_dir / f"UPL 2025-26 MD{matchday_number} Catapult Data Report.docx"
        
        try:
            builder = WeeklyGPSReportBuilder(matchday_number)
            builder.build_report(df_all, uploading_teams, missing_teams)
            builder.save(str(output_path))
            self.log(f"Report Saved Successfully: {output_path}")
        except Exception as e:
            self.log(f"Failed to generate report: {e}", logging.ERROR)
            return False
            
        # 4. Cleanup (Rename processed files)
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
        
        # Assuming we know all teams to find missing ones
        # For now, let's keep it simple as per original script logic
        # Ideally, this should come from config
        ALL_UPL_TEAMS = {
            "KCCA FC", "Vipers SC", "SC Villa", "Kitara FC", "NEC FC", "BUL FC", 
            "Police FC", "Express FC", "URA FC", "Wakiso Giants FC", "Maroons FC", 
            "Bright Stars FC", "UPDF FC", "Lugazi FC", "Mbale Heroes FC", "Mbarara City FC"
        }
        
        # Initialize team tracking with empty sets for now or pre-fill if we assume all play
        # The original script inferred matchday and teams dynamically
        
        for csv_file in csv_files:
            try:
                # Load raw data to check matchday
                df_raw = pd.read_csv(csv_file)
                if 'Session Title' not in df_raw.columns:
                    self.log(f"Skipping {csv_file.name}: 'Session Title' col missing", logging.WARNING)
                    continue
                    
                first_session = df_raw['Session Title'].iloc[0]
                md_num = parse_matchday(first_session)
                
                if md_num != target_md:
                    self.log(f"Skipping {csv_file.name}: MD{md_num} != MD{target_md}", logging.INFO)
                    continue
                    
                # Parse session info
                session_info = parse_session_info(first_session)
                if not session_info:
                    self.log(f"Skipping {csv_file.name}: Could not parse session info", logging.WARNING)
                    continue
                    
                home_team = session_info.get('team1')
                away_team = session_info.get('team2')
                
                # Clean and extract
                df_clean = extract_metrics(df_raw, csv_file.name, log_func=lambda m: None) # m: None to suppress noisy logs
                if df_clean.empty:
                    continue
                    
                # Aggregate halves
                df_agg = aggregate_halves(df_clean, log_func=lambda m: None)
                
                if not df_agg.empty:
                    # Add all session info (team1, team2, etc.)
                    for key, val in session_info.items():
                        df_agg[key] = val
                    
                    processed_dfs.append(df_agg)
                    files_to_rename.append(csv_file)
                    
                    # Track teams
                    # team1 is usually the 'Home' or 'Uploading' team in the session title convention "Us vs Them"
                    t1 = session_info.get('team1', '').strip().upper()
                    t2 = session_info.get('team2', '').strip().upper()
                    
                    if t1: uploading_teams.add(t1)
                    if t2: opponents.add(t2)
                    
                    self.log(f"Processed {csv_file.name}: {len(df_agg)} players")

            except Exception as e:
                self.log(f"Error processing {csv_file.name}: {e}", logging.ERROR)

        missing_teams = opponents - uploading_teams
        return processed_dfs, uploading_teams, missing_teams, files_to_rename

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
