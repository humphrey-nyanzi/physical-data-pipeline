#!/usr/bin/env python3
"""
Match Analysis Unified CLI

The single entry point for all analysis pipelines.
Usage:
    python scripts/match_analysis.py <command> [options]

Commands:
    weekly    Generate weekly GPS reports
    season    Generate season/half-season reports
"""

import sys
import os
import argparse
import logging
from typing import Dict, Type

# Add project root to path BEFORE other local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipelines.base import AnalysisPipeline
from src.pipelines.full import FullPipeline
from src.pipelines.weekly import WeeklyPipeline
from src.pipelines.season import SeasonPipeline

# Registry of available pipelines
# We will populate this as we migrate pipelines
PIPELINE_REGISTRY: Dict[str, Type[AnalysisPipeline]] = {}

def register_pipeline(pipeline_cls: Type[AnalysisPipeline]):
    """Register a pipeline class."""
    PIPELINE_REGISTRY[pipeline_cls(argparse.Namespace()).name] = pipeline_cls

register_pipeline(FullPipeline)
register_pipeline(WeeklyPipeline)
register_pipeline(SeasonPipeline)

def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

def main():
    parser = argparse.ArgumentParser(
        description="FUFA Match Analysis CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global arguments
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    subparsers = parser.add_subparsers(dest="command", help="Analysis pipeline to run")
    subparsers.required = True

    # Register subcommands for each pipeline
    for name, pipeline_cls in PIPELINE_REGISTRY.items():
        # Create a dummy instance to get description (optional, but cleaner)
        # We can also make description a classmethod if preferred
        # For now, we rely on the class structure
        
        pipeline_parser = subparsers.add_parser(
            name, 
            help=f"Run {name} analysis"
        )
        pipeline_cls.register_arguments(pipeline_parser)

    # Initial parsing to handle empty args or just help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Execute selected pipeline
    if args.command in PIPELINE_REGISTRY:
        pipeline_cls = PIPELINE_REGISTRY[args.command]
        pipeline = pipeline_cls(args)
        
        logging.info(f"Starting {args.command} pipeline...")
        
        if not pipeline.validate_args():
            logging.error("Argument validation failed.")
            sys.exit(1)
            
        try:
            # Initialize hierarchical output and file logging
            pipeline.setup_run_context()
            
            success = pipeline.run()
            if success:
                logging.info(f"{args.command.title()} pipeline completed successfully.")
                pipeline.save_metadata(status="completed")
                sys.exit(0)
            else:
                logging.error(f"{args.command.title()} pipeline failed.")
                pipeline.save_metadata(status="failed")
                sys.exit(1)
        except Exception as e:
            logging.exception(f"Unhandled exception in pipeline: {e}")
            pipeline.save_metadata(status="error")
            sys.exit(1)
    else:
        logging.error(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
