#!/usr/bin/env python3
"""
Match Analysis Unified CLI
==========================
Single entry point for all analysis pipelines.

Usage:
    python scripts/match_analysis.py <command> [options]

Commands:
    weekly    Generate weekly GPS reports
    season    Generate season / half-season reports
"""

import sys
import os
import argparse
import logging
from typing import Dict, Type

try:
    from dotenv import load_dotenv
    # Load .env file automatically
    load_dotenv()
except ImportError:
    pass

# Add project root to path BEFORE other local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipelines.base import AnalysisPipeline
from src.pipelines.full import FullPipeline
from src.pipelines.weekly import WeeklyPipeline
from src.pipelines.season import SeasonPipeline
from src.utils.console import Console, setup_console_logging

# ──────────────────────────────────────────────────────────────────────────────
# Pipeline registry
# ──────────────────────────────────────────────────────────────────────────────

PIPELINE_REGISTRY: Dict[str, Type[AnalysisPipeline]] = {}


def register_pipeline(pipeline_cls: Type[AnalysisPipeline]):
    """Register a pipeline class by its .name property."""
    PIPELINE_REGISTRY[pipeline_cls(argparse.Namespace()).name] = pipeline_cls


register_pipeline(FullPipeline)
register_pipeline(WeeklyPipeline)
register_pipeline(SeasonPipeline)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Match Analysis CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global arguments
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Analysis pipeline to run")
    subparsers.required = True

    # Register sub-commands for each pipeline
    for name, pipeline_cls in PIPELINE_REGISTRY.items():
        pipeline_parser = subparsers.add_parser(name, help=f"Run {name} analysis")
        pipeline_cls.register_arguments(pipeline_parser)

    # Print help when called with no args
    if len(sys.argv) == 1:
        Console.banner(
            "Match Analysis",
            "Unified pipeline entry-point  ·  python scripts/match_analysis.py <command>",
        )
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # ── Pretty logging setup ──────────────────────────────────────────────────
    setup_console_logging(verbose=args.verbose)
    logger = logging.getLogger("cli")

    # ── Startup banner ────────────────────────────────────────────────────────
    league  = getattr(args, "league", "").upper()
    season  = getattr(args, "season", "")
    subtitle = f"Pipeline: {args.command.upper()}"
    if league:
        subtitle += f"  ·  League: {league}"
    if season:
        subtitle += f"  ·  Season: {season}"

    Console.banner("Match Analysis", subtitle)

    # ── Execute pipeline ──────────────────────────────────────────────────────
    if args.command not in PIPELINE_REGISTRY:
        Console.error(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)

    pipeline_cls = PIPELINE_REGISTRY[args.command]
    pipeline = pipeline_cls(args)

    # ── Arg validation ────────────────────────────────────────────────────────
    Console.section("Argument Validation")
    if not pipeline.validate_args():
        Console.error("Argument validation failed – aborting.")
        Console.section_end()
        sys.exit(1)
    Console.success("Arguments validated successfully.")
    Console.section_end()

    # ── Run ───────────────────────────────────────────────────────────────────
    try:
        Console.section("Initialising Run Context")
        pipeline.setup_run_context()
        Console.section_end()

        Console.section(f"Running  {args.command.title()} Pipeline")
        success = pipeline.run()
        Console.section_end()

        if success:
            rows = pipeline.metadata.get("metrics", {}).get("total_rows_cleaned") or \
                   pipeline.metadata.get("metrics", {}).get("players_retained", 0)
            Console.pipeline_complete(args.command, rows)
            pipeline.save_metadata(status="completed")
            sys.exit(0)
        else:
            Console.pipeline_failed(args.command, "Pipeline returned failure status.")
            pipeline.save_metadata(status="failed")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Unhandled exception in pipeline: {e}")
        Console.pipeline_failed(args.command, str(e))
        pipeline.save_metadata(status="error")
        sys.exit(1)


if __name__ == "__main__":
    main()
