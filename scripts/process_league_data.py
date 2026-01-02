#!/usr/bin/env python
"""
Data Cleaning Pipeline Script

Replaces: cleaning_FWSL_2025.ipynb and cleaning_UPL_2025.ipynb

This script handles complete data cleaning workflow for match analysis data,
including standardization, filtering, outlier removal, and aggregation.

Usage:
    python scripts/process_league_data.py --league upl --input raw_data.csv --output cleaned.csv
    python scripts/process_league_data.py --league fwsl --input data.csv --output cleaned.csv --verbose
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Tuple

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.league_definitions import LEAGUE_CONFIG
from src.data.cleaning import clean_pipeline


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def validate_inputs(league: str, input_path: Path, output_path: Path) -> bool:
    """Validate input arguments."""
    # Check league
    if league not in LEAGUE_CONFIG:
        logger.error(f"Invalid league: {league}. Must be 'fwsl' or 'upl'")
        return False

    # Check input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return False

    # Check input is readable
    try:
        pd.read_csv(input_path, nrows=1)
    except Exception as e:
        logger.error(f"Cannot read input file: {e}")
        return False

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    return True


def get_data_preview(df: pd.DataFrame, n_rows: int = 3) -> str:
    """Generate a preview of the data."""
    preview = f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n"
    preview += f"Columns: {', '.join(df.columns[:5])}...\n"
    preview += f"Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB"
    return preview


def calculate_cleaning_stats(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> dict:
    """Calculate statistics about the cleaning process."""
    return {
        "rows_raw": len(raw_df),
        "rows_cleaned": len(clean_df),
        "rows_removed": len(raw_df) - len(clean_df),
        "removal_percentage": (len(raw_df) - len(clean_df)) / len(raw_df) * 100,
        "columns_raw": raw_df.shape[1],
        "columns_cleaned": clean_df.shape[1],
        "columns_removed": raw_df.shape[1] - clean_df.shape[1],
    }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Clean league match analysis data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/process_league_data.py --league upl --input raw.csv --output cleaned.csv
  python scripts/process_league_data.py --league fwsl --input data.csv -o result.csv -v
        """,
    )

    parser.add_argument(
        "--league",
        required=True,
        choices=["upl", "fwsl"],
        help="League identifier (upl or fwsl)",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to raw input CSV file",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Path to output cleaned CSV file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Print header
    logger.info("=" * 70)
    logger.info("DATA CLEANING PIPELINE")
    logger.info("=" * 70)
    logger.info(f"League: {args.league.upper()}")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info("")

    # Validate inputs
    logger.info("Validating inputs...")
    if not validate_inputs(args.league, args.input, args.output):
        logger.error("❌ Input validation failed")
        sys.exit(1)
    logger.info("✓ Inputs validated")
    logger.info("")

    # Load raw data
    logger.info(f"Loading raw data from {args.input}...")
    start_time = time.time()
    try:
        raw_df = pd.read_csv(args.input)
        load_time = time.time() - start_time
        logger.info(f"✓ Loaded {len(raw_df)} rows in {load_time:.2f}s")
        if args.verbose:
            logger.debug(get_data_preview(raw_df))
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        sys.exit(1)
    logger.info("")

    # Run cleaning pipeline
    logger.info("Running cleaning pipeline...")
    logger.info("  - Standardizing columns...")
    logger.info("  - Filtering sessions...")
    logger.info("  - Normalizing clubs...")
    logger.info("  - Computing derived metrics...")
    logger.info("  - Removing outliers...")
    logger.info("  - Aggregating halves...")
    start_time = time.time()
    try:
        cleaned_df = clean_pipeline(str(args.input), args.league)
        clean_time = time.time() - start_time
        logger.info(f"✓ Cleaning completed in {clean_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ Cleaning failed: {e}")
        if args.verbose:
            import traceback

            logger.debug(traceback.format_exc())
        sys.exit(1)
    logger.info("")

    # Calculate statistics
    logger.info("Cleaning Statistics:")
    stats = calculate_cleaning_stats(raw_df, cleaned_df)
    logger.info(f"  Raw rows: {stats['rows_raw']:,}")
    logger.info(f"  Cleaned rows: {stats['rows_cleaned']:,}")
    logger.info(
        f"  Rows removed: {stats['rows_removed']:,} ({stats['removal_percentage']:.1f}%)"
    )
    logger.info(f"  Raw columns: {stats['columns_raw']}")
    logger.info(f"  Cleaned columns: {stats['columns_cleaned']}")
    logger.info(f"  Columns removed: {stats['columns_removed']}")
    if args.verbose:
        logger.debug(get_data_preview(cleaned_df))
    logger.info("")

    # Save cleaned data
    logger.info(f"Saving cleaned data to {args.output}...")
    start_time = time.time()
    try:
        cleaned_df.to_csv(args.output, index=False)
        save_time = time.time() - start_time
        file_size = args.output.stat().st_size / 1024 / 1024
        logger.info(f"✓ Saved {file_size:.1f} MB in {save_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ Failed to save data: {e}")
        sys.exit(1)
    logger.info("")

    # Summary
    logger.info("=" * 70)
    logger.info("✓ CLEANING COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Input:  {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Total time: {load_time + clean_time + save_time:.2f}s")


if __name__ == "__main__":
    main()
