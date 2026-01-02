#!/usr/bin/env python
"""
Report Generation Script

Replaces: individual_club_reports.ipynb

Generates comprehensive DOCX reports for all clubs including:
- Club performance summary
- Player statistics and matchday breakdown
- Positional analysis
- Competitive comparisons
- Coverage and trend analysis

Usage:
    python scripts/generate_reports.py --cleaned data.csv --analysis analysis.json --output reports/
    python scripts/generate_reports.py --cleaned data.csv --analysis meta.json -o results/ -v
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
from src.reporting import document_generation, report_builder


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def validate_inputs(cleaned_path: Path, analysis_path: Path, output_dir: Path) -> bool:
    """Validate input arguments."""
    # Check cleaned data exists
    if not cleaned_path.exists():
        logger.error(f"Cleaned data file not found: {cleaned_path}")
        return False

    # Check analysis metadata exists
    if not analysis_path.exists():
        logger.error(f"Analysis metadata file not found: {analysis_path}")
        return False

    # Try loading both files
    try:
        pd.read_csv(cleaned_path, nrows=1)
    except Exception as e:
        logger.error(f"Cannot read cleaned data: {e}")
        return False

    try:
        with open(analysis_path) as f:
            json.load(f)
    except Exception as e:
        logger.error(f"Cannot read analysis metadata: {e}")
        return False

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    return True


def load_analysis_results(analysis_dir: Path) -> Dict[str, Any]:
    """Load analysis results from output directory."""
    results = {}

    # Load CSV files
    for csv_file in analysis_dir.glob("*.csv"):
        if csv_file.name.endswith(".csv"):
            key = csv_file.stem
            try:
                results[key] = pd.read_csv(csv_file, index_col=0)
            except Exception:
                results[key] = pd.read_csv(csv_file)

    return results


def generate_club_reports(
    cleaned_df: pd.DataFrame,
    analysis_results: Dict[str, Any],
    league: str,
    output_dir: Path,
) -> Dict[str, Any]:
    """Generate DOCX reports for each club."""
    logger.info("Generating club reports...")

    report_stats = {
        "total_clubs": 0,
        "reports_generated": 0,
        "reports_failed": 0,
        "clubs": [],
    }

    # Get unique clubs
    clubs = sorted(cleaned_df["club_for"].unique())
    report_stats["total_clubs"] = len(clubs)

    for i, club in enumerate(clubs, 1):
        try:
            # Extract club data
            club_data = cleaned_df[cleaned_df["club_for"] == club]

            # Prepare report data
            report_dict = report_builder.prepare_club_report(
                club_data, cleaned_df, analysis_results, league
            )

            # Generate DOCX
            doc = document_generation.create_club_report_document(
                club, report_dict, league
            )

            # Save report
            report_path = output_dir / f"{club}_Report.docx"
            doc.save(report_path)

            logger.info(f"  [{i}/{len(clubs)}] ✓ {club}")
            report_stats["reports_generated"] += 1
            report_stats["clubs"].append(
                {
                    "name": club,
                    "rows": len(club_data),
                    "report_path": str(report_path),
                }
            )

        except Exception as e:
            logger.warning(f"  [{i}/{len(clubs)}] ✗ {club}: {str(e)[:50]}")
            report_stats["reports_failed"] += 1

    return report_stats


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Generate DOCX reports for all clubs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_reports.py --cleaned data.csv --analysis results/ --output reports/
  python scripts/generate_reports.py --cleaned data.csv --analysis meta.json -o docx/ -v
        """,
    )

    parser.add_argument(
        "--cleaned",
        required=True,
        type=Path,
        help="Path to cleaned data CSV file",
    )
    parser.add_argument(
        "--analysis",
        required=True,
        type=Path,
        help="Path to analysis results directory or metadata JSON",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output directory for DOCX reports",
    )
    parser.add_argument(
        "--league",
        type=str,
        help="League identifier (auto-detect if not specified)",
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
    logger.info("REPORT GENERATION")
    logger.info("=" * 70)
    logger.info(f"Cleaned data: {args.cleaned}")
    logger.info(f"Analysis results: {args.analysis}")
    logger.info(f"Output directory: {args.output}")
    logger.info("")

    # Validate inputs
    logger.info("Validating inputs...")
    if not validate_inputs(args.cleaned, args.analysis, args.output):
        logger.error("❌ Input validation failed")
        sys.exit(1)
    logger.info("✓ Inputs validated")
    logger.info("")

    # Load cleaned data
    logger.info(f"Loading cleaned data from {args.cleaned}...")
    start_time = time.time()
    try:
        cleaned_df = pd.read_csv(args.cleaned)
        load_time = time.time() - start_time
        logger.info(f"✓ Loaded {len(cleaned_df)} rows in {load_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        sys.exit(1)

    # Auto-detect league if not specified
    if not args.league:
        if (
            "Wmd"
            in cleaned_df.get("match_day", pd.Series()).astype(str).str[:3].unique()[0]
        ):
            args.league = "fwsl"
        else:
            args.league = "upl"
        logger.info(f"  Auto-detected league: {args.league.upper()}")
    logger.info("")

    # Load analysis results
    logger.info(f"Loading analysis results from {args.analysis}...")
    try:
        if args.analysis.is_dir():
            analysis_results = load_analysis_results(args.analysis)
            logger.info(f"✓ Loaded {len(analysis_results)} analysis datasets")
        else:
            # Load metadata to find analysis directory
            with open(args.analysis) as f:
                metadata = json.load(f)
            analysis_dir = args.analysis.parent
            analysis_results = load_analysis_results(analysis_dir)
            logger.info(f"✓ Loaded {len(analysis_results)} analysis datasets")
    except Exception as e:
        logger.error(f"❌ Failed to load analysis results: {e}")
        sys.exit(1)
    logger.info("")

    # Generate reports
    logger.info("Generating club reports...")
    start_time = time.time()
    try:
        report_stats = generate_club_reports(
            cleaned_df, analysis_results, args.league, args.output
        )
        generation_time = time.time() - start_time
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        if args.verbose:
            import traceback

            logger.debug(traceback.format_exc())
        sys.exit(1)
    logger.info("")

    # Summary
    logger.info("=" * 70)
    logger.info("✓ REPORT GENERATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total clubs: {report_stats['total_clubs']}")
    logger.info(f"Reports generated: {report_stats['reports_generated']}")
    if report_stats["reports_failed"] > 0:
        logger.warning(f"Reports failed: {report_stats['reports_failed']}")
    logger.info(
        f"Success rate: {report_stats['reports_generated'] / report_stats['total_clubs'] * 100:.1f}%"
    )
    logger.info(f"Total time: {generation_time:.2f}s")
    logger.info(f"Output directory: {args.output}")


if __name__ == "__main__":
    main()
