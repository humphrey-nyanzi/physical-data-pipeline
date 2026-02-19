"""
Pipeline Module

⚠️  DEPRECATION NOTICE ⚠️
This module is DEPRECATED. Use src/pipelines/ instead.

OLD WAY (deprecated):
    from src.pipeline.orchestrator import PipelineExecutor
    executor = PipelineExecutor(league='upl')
    executor.execute_full_pipeline('data.csv')

NEW WAY (recommended):
    python scripts/match_analysis.py full --league upl --input data.csv

Submodules:
    - orchestrator: Legacy execution engine (deprecated)
"""

from .orchestrator import (
    PipelineExecutor,
    execute_pipeline,
    setup_logging,
)

__all__ = [
    "PipelineExecutor",
    "execute_pipeline",
    "setup_logging",
]
