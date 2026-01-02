"""
Pipeline Module

Orchestration layer coordinating all phases of the Match-Analysis pipeline.

Submodules:
    - orchestrator: Main execution engine
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
