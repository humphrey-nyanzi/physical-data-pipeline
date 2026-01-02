#!/usr/bin/env python
"""
Analysis Generation Script

Replaces: analysis_FWSL_2025.ipynb and analysis_UPL_2025.ipynb

Computes comprehensive statistical analysis on cleaned league data including:
- Summary statistics and player counts
- Club-level coverage analysis
- Positional breakdowns
- Matchday trends
- Competitive comparisons

Usage:
    python scripts/generate_analysis.py --league upl --input cleaned.csv --output analysis/
    python scripts/generate_analysis.py --league fwsl --input data.csv -o results/ -v
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.league_definitions import LEAGUE_CONFIG
from src.analysis import analysis as analysis_module


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def validate_inputs(league: str, input_path: Path, output_dir: Path) -> bool:
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
        df = pd.read_csv(input_path, nrows=1)
    except Exception as e:
        logger.error(f"Cannot read input file: {e}")
        return False

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    return True


def run_all_analyses(cleaned_df: pd.DataFrame, league: str) -> Dict[str, Any]:
    """Execute all analysis functions."""
    results = {}

    logger.info("Running analyses...")

    # Summary statistics
    logger.info("  - Summary statistics...")
    results["summary_stats"] = analysis_module.compute_summary_stats(cleaned_df)

    # Player counts
    logger.info("  - Player analysis...")
    results["unique_players"] = analysis_module.unique_players_per_club(cleaned_df)
    results["players_per_club_md"] = analysis_module.players_per_club_per_matchday(
        cleaned_df
    )
    results["top_players"] = analysis_module.top_players_by_matchdays(
        cleaned_df, top_n=20
    )

    # Club analysis
    logger.info("  - Club coverage...")
    results["matchdays_per_club"] = analysis_module.matchdays_per_club(cleaned_df)
    results["club_coverage"] = analysis_module.club_coverage_analysis(
        cleaned_df, league
    )

    # Positional analysis
    logger.info("  - Positional analysis...")
    results["positional_stats"] = analysis_module.compute_positional_stats(
        cleaned_df, "distance"
    )
    results["positional_comparison"] = (
        analysis_module.positional_comparison_all_metrics(cleaned_df)
    )

    # Trends
    logger.info("  - Matchday trends...")
    results["players_per_md"] = analysis_module.total_players_per_matchday(cleaned_df)
    results["clubs_per_md"] = analysis_module.clubs_per_matchday(cleaned_df)
    results["trend_metrics"] = analysis_module.matchday_trend_metrics(
        cleaned_df, "distance"
    )

    # Coverage grid
    logger.info("  - Coverage grid...")
    results["coverage_grid"] = analysis_module.matchday_club_coverage_grid(cleaned_df)
    results["coverage_summary"] = analysis_module.coverage_summary(cleaned_df)

    # Comparisons
    logger.info("  - Competitive analysis...")
    results["club_vs_league"] = analysis_module.club_vs_league_comparison(
        cleaned_df, "distance"
    )

    return results


def export_summary_stats(results: Dict[str, Any], output_dir: Path) -> None:
    """Export key summary statistics as CSV files."""
    logger.info("Exporting summary statistics...")

    # Summary stats table
    if isinstance(results.get("summary_stats"), pd.DataFrame):
        results["summary_stats"].to_csv(output_dir / "summary_stats.csv")
        logger.info(
            f"  ✓ Saved summary_stats.csv ({len(results['summary_stats'])} rows)"
        )

    # Unique players
    if isinstance(results.get("unique_players"), pd.DataFrame):
        results["unique_players"].to_csv(output_dir / "unique_players.csv")
        logger.info(
            f"  ✓ Saved unique_players.csv ({len(results['unique_players'])} rows)"
        )

    # Top players
    if isinstance(results.get("top_players"), pd.DataFrame):
        results["top_players"].to_csv(output_dir / "top_players.csv", index=False)
        logger.info(f"  ✓ Saved top_players.csv ({len(results['top_players'])} rows)")

    # Club coverage
    if isinstance(results.get("club_coverage"), pd.DataFrame):
        results["club_coverage"].to_csv(output_dir / "club_coverage.csv")
        logger.info(
            f"  ✓ Saved club_coverage.csv ({len(results['club_coverage'])} rows)"
        )

    # Matchdays per club
    if isinstance(results.get("matchdays_per_club"), pd.DataFrame):
        results["matchdays_per_club"].to_csv(output_dir / "matchdays_per_club.csv")
        logger.info(
            f"  ✓ Saved matchdays_per_club.csv ({len(results['matchdays_per_club'])} rows)"
        )

    # Coverage grid
    if isinstance(results.get("coverage_grid"), pd.DataFrame):
        results["coverage_grid"].to_csv(output_dir / "coverage_grid.csv")
        logger.info(
            f"  ✓ Saved coverage_grid.csv ({len(results['coverage_grid'])} rows)"
        )


def save_analysis_results(results: Dict[str, Any], output_dir: Path) -> None:
    """Save analysis results to JSON format for consumption by other scripts."""
    logger.info("Serializing analysis results...")

    # Convert DataFrames to serializable format
    serializable = {}
    for key, value in results.items():
        if isinstance(value, pd.DataFrame):
            serializable[key] = {
                "type": "dataframe",
                "shape": value.shape,
                "columns": list(value.columns),
                "file": f"{key}.csv",
            }
        elif isinstance(value, dict):
            serializable[key] = {
                "type": "dict",
                "keys": list(value.keys()),
                "file": f"{key}.json",
            }
        else:
            serializable[key] = str(type(value).__name__)

    # Save metadata
    metadata = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "results": serializable,
        "total_analyses": len(results),
    }

    with open(output_dir / "analysis_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("✓ Saved analysis_metadata.json")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Generate statistical analysis from cleaned league data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_analysis.py --league upl --input cleaned.csv --output results/
  python scripts/generate_analysis.py --league fwsl --input data.csv -o analysis/ -v
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
        help="Path to cleaned input CSV file",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output directory for analysis results",
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
    logger.info("ANALYSIS GENERATION")
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

    # Load data
    logger.info(f"Loading cleaned data from {args.input}...")
    start_time = time.time()
    try:
        cleaned_df = pd.read_csv(args.input)
        load_time = time.time() - start_time
        logger.info(f"✓ Loaded {len(cleaned_df)} rows in {load_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        sys.exit(1)
    logger.info("")

    # Run analyses
    logger.info("Performing analysis computations...")
    start_time = time.time()
    try:
        results = run_all_analyses(cleaned_df, args.league)
        analysis_time = time.time() - start_time
        logger.info(f"✓ Analysis completed in {analysis_time:.2f}s")
        logger.info(f"  Computed {len(results)} analysis datasets")
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback

            logger.debug(traceback.format_exc())
        sys.exit(1)
    logger.info("")

    # Export results
    logger.info("Exporting results...")
    export_summary_stats(results, args.output)
    save_analysis_results(results, args.output)
    logger.info("")

    # Summary
    logger.info("=" * 70)
    logger.info("✓ ANALYSIS COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Analysis datasets: {len(results)}")
    logger.info(f"Total time: {analysis_time:.2f}s")
    logger.info("")
    logger.info("Output files:")
    for csv_file in sorted(args.output.glob("*.csv")):
        logger.info(f"  - {csv_file.name}")
    logger.info(f"  - analysis_metadata.json")


if __name__ == "__main__":
    main()
