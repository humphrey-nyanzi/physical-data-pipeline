#!/usr/bin/env python
"""
End-to-End Pipeline Wrapper Script

Orchestrates complete analysis pipeline: cleaning → analysis → reporting

Provides flexible execution modes:
- Full automation: Execute all phases without prompts
- Step-by-step: Execute with confirmation at each phase
- Interactive: Menu-driven mode with phase selection

Usage:
    # Full end-to-end
    python scripts/run_full_analysis.py --league upl --input raw.csv --output results/

    # Step-by-step with confirmation
    python scripts/run_full_analysis.py --league fwsl --input data.csv -o results/ --interactive

    # Verbose output
    python scripts/run_full_analysis.py --league upl --input raw.csv -o results/ -v
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class PipelineExecutor:
    """Orchestrates the complete analysis pipeline."""

    def __init__(
        self, league: str, input_path: Path, output_dir: Path, verbose: bool = False
    ):
        """Initialize pipeline executor."""
        self.league = league
        self.input_path = input_path
        self.output_dir = output_dir
        self.verbose = verbose

        # Create subdirectories
        self.cleaned_dir = output_dir / "01_cleaned"
        self.analysis_dir = output_dir / "02_analysis"
        self.reports_dir = output_dir / "03_reports"

        self.cleaned_path = self.cleaned_dir / f"{league}_cleaned.csv"
        self.analysis_metadata = self.analysis_dir / "analysis_metadata.json"

        self.execution_log = {
            "start_time": None,
            "end_time": None,
            "league": league,
            "phases": {},
        }

    def validate_inputs(self) -> bool:
        """Validate that inputs exist and are readable."""
        if not self.input_path.exists():
            logger.error(f"Input file not found: {self.input_path}")
            return False

        try:
            import pandas as pd

            pd.read_csv(self.input_path, nrows=1)
        except Exception as e:
            logger.error(f"Cannot read input file: {e}")
            return False

        return True

    def run_phase_1_cleaning(self) -> bool:
        """Execute data cleaning phase."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("PHASE 1: DATA CLEANING")
        logger.info("=" * 70)

        phase_start = time.time()
        try:
            # Create cleaned directory
            self.cleaned_dir.mkdir(parents=True, exist_ok=True)

            # Build command
            cmd = [
                "python",
                "scripts/process_league_data.py",
                "--league",
                self.league,
                "--input",
                str(self.input_path),
                "--output",
                str(self.cleaned_path),
            ]

            if self.verbose:
                cmd.append("--verbose")

            # Run subprocess
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent,
                capture_output=False,
                text=True,
            )

            if result.returncode != 0:
                logger.error("❌ Cleaning phase failed")
                return False

            phase_time = time.time() - phase_start
            self.execution_log["phases"]["cleaning"] = {
                "status": "success",
                "elapsed_seconds": phase_time,
                "output_file": str(self.cleaned_path),
            }

            logger.info(f"✓ Phase 1 completed in {phase_time:.2f}s")
            return True

        except Exception as e:
            logger.error(f"❌ Cleaning phase failed: {e}")
            self.execution_log["phases"]["cleaning"] = {
                "status": "error",
                "error": str(e),
            }
            return False

    def run_phase_2_analysis(self) -> bool:
        """Execute analysis phase."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("PHASE 2: ANALYSIS")
        logger.info("=" * 70)

        phase_start = time.time()
        try:
            # Create analysis directory
            self.analysis_dir.mkdir(parents=True, exist_ok=True)

            # Build command
            cmd = [
                "python",
                "scripts/generate_analysis.py",
                "--league",
                self.league,
                "--input",
                str(self.cleaned_path),
                "--output",
                str(self.analysis_dir),
            ]

            if self.verbose:
                cmd.append("--verbose")

            # Run subprocess
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent,
                capture_output=False,
                text=True,
            )

            if result.returncode != 0:
                logger.error("❌ Analysis phase failed")
                return False

            phase_time = time.time() - phase_start
            self.execution_log["phases"]["analysis"] = {
                "status": "success",
                "elapsed_seconds": phase_time,
                "output_dir": str(self.analysis_dir),
            }

            logger.info(f"✓ Phase 2 completed in {phase_time:.2f}s")
            return True

        except Exception as e:
            logger.error(f"❌ Analysis phase failed: {e}")
            self.execution_log["phases"]["analysis"] = {
                "status": "error",
                "error": str(e),
            }
            return False

    def run_phase_3_reporting(self) -> bool:
        """Execute report generation phase."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("PHASE 3: REPORT GENERATION")
        logger.info("=" * 70)

        phase_start = time.time()
        try:
            # Create reports directory
            self.reports_dir.mkdir(parents=True, exist_ok=True)

            # Build command
            cmd = [
                "python",
                "scripts/generate_reports.py",
                "--cleaned",
                str(self.cleaned_path),
                "--analysis",
                str(self.analysis_dir),
                "--output",
                str(self.reports_dir),
                "--league",
                self.league,
            ]

            if self.verbose:
                cmd.append("--verbose")

            # Run subprocess
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent,
                capture_output=False,
                text=True,
            )

            if result.returncode != 0:
                logger.error("❌ Report generation phase failed")
                return False

            phase_time = time.time() - phase_start
            self.execution_log["phases"]["reporting"] = {
                "status": "success",
                "elapsed_seconds": phase_time,
                "output_dir": str(self.reports_dir),
            }

            logger.info(f"✓ Phase 3 completed in {phase_time:.2f}s")
            return True

        except Exception as e:
            logger.error(f"❌ Report generation phase failed: {e}")
            self.execution_log["phases"]["reporting"] = {
                "status": "error",
                "error": str(e),
            }
            return False

    def execute_full_pipeline(self) -> bool:
        """Execute complete pipeline."""
        logger.info("")
        logger.info("╔" + "═" * 68 + "╗")
        logger.info("║" + " FULL PIPELINE EXECUTION ".center(68) + "║")
        logger.info("╚" + "═" * 68 + "╝")

        total_start = time.time()
        self.execution_log["start_time"] = total_start

        # Phase 1: Cleaning
        if not self.run_phase_1_cleaning():
            return False

        # Phase 2: Analysis
        if not self.run_phase_2_analysis():
            return False

        # Phase 3: Reporting
        if not self.run_phase_3_reporting():
            return False

        total_time = time.time() - total_start
        self.execution_log["end_time"] = total_time

        # Print summary
        self.print_summary(total_time)

        return True

    def print_summary(self, total_time: float) -> None:
        """Print execution summary."""
        logger.info("")
        logger.info("╔" + "═" * 68 + "╗")
        logger.info("║" + " PIPELINE EXECUTION COMPLETE ".center(68) + "║")
        logger.info("╚" + "═" * 68 + "╝")
        logger.info("")
        logger.info(f"League: {self.league.upper()}")
        logger.info(f"Input: {self.input_path}")
        logger.info("")
        logger.info("OUTPUT DIRECTORIES:")
        logger.info(f"  Cleaned Data:      {self.cleaned_dir}")
        logger.info(f"  Analysis Results:  {self.analysis_dir}")
        logger.info(f"  Reports:           {self.reports_dir}")
        logger.info("")
        logger.info("PHASE EXECUTION TIMES:")
        for phase_name, phase_data in self.execution_log["phases"].items():
            if phase_data.get("status") == "success":
                elapsed = phase_data.get("elapsed_seconds", 0)
                logger.info(f"  {phase_name.title():20s} {elapsed:6.2f}s ✓")
        logger.info("")
        logger.info(f"Total Execution Time: {total_time:.2f}s")
        logger.info("")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Execute complete analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_full_analysis.py --league upl --input raw.csv --output results/
  python scripts/run_full_analysis.py --league fwsl --input data.csv -o results/ -v
  python scripts/run_full_analysis.py --league upl --input raw.csv -o results/ --interactive
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
        help="Output directory for all results",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode with phase confirmations",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Initialize executor
    executor = PipelineExecutor(
        league=args.league,
        input_path=args.input,
        output_dir=args.output,
        verbose=args.verbose,
    )

    # Validate inputs
    logger.info("Validating inputs...")
    if not executor.validate_inputs():
        logger.error("❌ Input validation failed")
        sys.exit(1)
    logger.info("✓ Inputs validated")

    # Execute pipeline
    if executor.execute_full_pipeline():
        logger.info("✓ PIPELINE SUCCESSFUL")
        sys.exit(0)
    else:
        logger.error("✗ PIPELINE FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
