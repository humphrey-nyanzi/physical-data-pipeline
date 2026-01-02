"""
FUFA Match Analysis - Football Performance Analytics Pipeline

A comprehensive data pipeline for analyzing Catapult GPS/IMU tracking data
from Uganda Football Federation (FUFA) league matches.

Modules:
    config: League definitions, constants, and configuration management
    utils: Text cleaning, normalization, and styling utilities
    data: Data loading, cleaning, and validation
    analysis: Statistical analysis and aggregation
    reporting: Report generation and visualization
"""

__version__ = "0.1.0"
__author__ = "FUFA Research & Statistics Team"

from . import config
from . import utils

__all__ = [
    "config",
    "utils",
]
