from abc import ABC, abstractmethod
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AnalysisPipeline(ABC):
    """
    Abstract base class for all match analysis pipelines.
    
    Subclasses must implement:
    - name: Property returning pipeline name
    - register_arguments: Add argparse arguments
    - run: Execute the pipeline logic
    """

    def __init__(self, args: argparse.Namespace):
        """Initialize pipeline with parsed arguments."""
        self.args = args
        self.config: Dict[str, Any] = {}
        self.output_dir = Path(getattr(args, 'output', './Output'))
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the pipeline (e.g., 'weekly', 'season')."""
        pass

    @property
    def description(self) -> str:
        """Description for CLI help."""
        return f"Execute {self.name} analysis"

    @classmethod
    @abstractmethod
    def register_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """Register pipeline-specific arguments to the parser."""
        pass

    def validate_args(self) -> bool:
        """
        Validate provided arguments. 
        Override in subclasses for specific validation.
        """
        return True

    @abstractmethod
    def run(self) -> bool:
        """
        Execute the pipeline logic.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    def setup_output_dir(self):
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ready: {self.output_dir}")

    def log(self, message: str, level: int = logging.INFO):
        """Helper for logging."""
        logger.log(level, f"[{self.name.upper()}] {message}")
