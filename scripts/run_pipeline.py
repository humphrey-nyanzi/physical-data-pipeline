#!/usr/bin/env python3
"""
Pipeline Command-Line Interface

Execute the full Match-Analysis pipeline from the command line.

Usage:
    python scripts/run_pipeline.py --league upl --input ./all_catapult_data_16_Jul_25.csv --output ./reports
    python scripts/run_pipeline.py --league fwsl --input ./raw_data.csv

Options:
    --league/-l     League identifier: 'fwsl' or 'upl' (required)
    --input/-i      Path to raw CSV input file (required)
    --output/-o     Output directory base (default: ./output)
    --verbose/-v    Enable verbose logging (default: False)
    --help/-h       Show help message
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../"))

from src.pipeline.orchestrator import execute_pipeline


def main():
    """Main CLI entry point."""

    parser = argparse.ArgumentParser(
        description="Execute Match-Analysis pipeline for Catapult GPS data processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process UPL data
  python run_pipeline.py -l upl -i ./all_catapult_data_16_Jul_25.csv -o ./output
  
  # Process FWSL data with verbose output
  python run_pipeline.py -l fwsl -i ./raw_data.csv -v
  
  # Use default output directory
  python run_pipeline.py -l upl -i ./data.csv
        """,
    )

    parser.add_argument(
        "-l",
        "--league",
        required=True,
        choices=["upl", "fwsl"],
        help="League identifier (required): upl or fwsl",
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=str,
        help="Path to raw CSV input file (required)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="./output",
        type=str,
        help="Output directory base (default: ./output)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Validate inputs
    if not os.path.isfile(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    print("\n" + "=" * 70)
    print("MATCH-ANALYSIS PIPELINE")
    print("=" * 70)
    print(f"League:        {args.league.upper()}")
    print(f"Input:         {args.input}")
    print(f"Output:        {args.output}")
    print(f"Verbose:       {args.verbose}")
    print("=" * 70 + "\n")

    try:
        # Execute pipeline
        result = execute_pipeline(
            league=args.league, raw_path=args.input, output_dir=args.output
        )

        # Print results
        print("\n" + "=" * 70)

        if result["status"] == "success":
            print("✓ PIPELINE EXECUTION SUCCESSFUL")
            print("=" * 70)
            print(
                f"Total Time:           {result['total_elapsed_seconds']:.2f} seconds"
            )
            print(f"Clubs Processed:      {result['analysis_summary']['unique_clubs']}")
            print(
                f"Rows Processed:       {result['analysis_summary']['total_rows_processed']}"
            )
            print(f"Cleaned Data:         {result['cleaned_data_path']}")
            print(f"Reports Generated:    {len(result['report_paths'])}")
            print(
                f"Reports Location:     {os.path.dirname(list(result['report_paths'].values())[0]) if result['report_paths'] else 'N/A'}"
            )
            print("=" * 70)

            # Save execution summary
            summary_file = os.path.join(
                args.output, f"pipeline_summary_{args.league}.json"
            )
            with open(summary_file, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\nExecution summary saved to: {summary_file}\n")

            return 0
        else:
            print("✗ PIPELINE EXECUTION FAILED")
            print("=" * 70)
            print(f"Error: {result.get('error', 'Unknown error')}")
            print("=" * 70 + "\n")
            return 1

    except KeyboardInterrupt:
        print("\n\nPipeline execution interrupted by user.")
        return 130
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
