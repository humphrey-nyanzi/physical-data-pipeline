#!/usr/bin/env python
"""
Season Report Generation Script

Generates league-wide season or half-season reports in DOCX format.
"""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd
import yaml

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.analysis import season_analysis
from src.reporting.season_report_builder import SeasonReportBuilder
from src.config import league_definitions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def load_config():
    config_path = Path(__file__).parent / "config" / "analysis_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Generate Season/Half-Season Reports")
    parser.add_argument("--league", required=True, choices=['upl', 'fwsl'], help="League identifier")
    parser.add_argument("--input", required=True, type=Path, help="Path to cleaned CSV data")
    parser.add_argument("--output", required=True, type=Path, help="Output directory")
    parser.add_argument("--timeframe", default="season", choices=['season', 'half_season'], help="Timeframe (season matchdays)")
    
    args = parser.parse_args()
    
    # Load Data
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
        
    logger.info(f"Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    
    # Load Config for Half Season limits
    config = load_config()
    half_season_limit = config['season_report']['half_season_matchday'][args.league]
    
    # Filter Data
    filtered_df = season_analysis.filter_data_by_timeframe(
        df, 
        args.timeframe, 
        args.league, 
        half_season_limit
    )
    
    if filtered_df.empty:
        logger.error("No data found after filtering!")
        sys.exit(1)
        
    # Build Report
    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    builder = SeasonReportBuilder(
        filtered_df, 
        args.league, 
        args.timeframe, 
        output_dir,
        half_season_limit
    )
    
    output_path = builder.build_report()
    logger.info(f"Report generation complete: {output_path}")

if __name__ == "__main__":
    main()
