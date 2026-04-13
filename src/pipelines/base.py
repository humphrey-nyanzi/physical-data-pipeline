import argparse
import logging
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    from src.utils.console import Console
except ImportError:
    Console = None  # Graceful fallback

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
        
        # Unique Run ID
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Base Output Directory (default)
        self.base_output_dir = Path(getattr(args, 'output', './Output'))
        self.output_dir = self.base_output_dir
        
        # Metadata storage
        self.metadata: Dict[str, Any] = {
            "run_id": self.run_id,
            "pipeline": self.name,
            "start_time": datetime.now().isoformat(),
            "args": vars(args),
            "status": "started",
            "metrics": {}
        }

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

    def setup_run_context(self):
        """
        Setup hierarchical output directory and logging context.
        Hierarchy: Output / {Season} / {League} / {Command} / {Run_ID}
        """
        season = getattr(self.args, 'season', 'unknown_season').replace('/', '-')
        league = getattr(self.args, 'league', 'unknown_league').upper()
        
        # Build hierarchical path
        self.output_dir = self.base_output_dir / season / league / self.name.capitalize() / self.run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup file logging for this specific run
        log_dir = Path("logs") / season / league
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{self.run_id}_{self.name}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logging.getLogger().addHandler(file_handler)
        
        self.log("Run context initialized.")
        self.log(f"Output directory: {self.output_dir}")
        self.log(f"Log file: {log_file}")
        if Console:
            Console.divider()
            Console.stat("Run ID",        self.run_id)
            Console.stat("Output dir",    str(self.output_dir))
            Console.stat("Log file",       str(log_file))
            Console.divider()

    def save_metadata(self, status: str = "completed"):
        """Save run metadata to JSON file and update global history."""
        self.metadata["status"] = status
        self.metadata["end_time"] = datetime.now().isoformat()
        
        # Save local metadata JSON
        metadata_file = self.output_dir / "run_metadata.json"
        try:
            def stringify_paths(obj):
                if isinstance(obj, dict):
                    return {k: stringify_paths(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [stringify_paths(i) for i in obj]
                elif isinstance(obj, Path):
                    return str(obj)
                return obj

            serializable_metadata = stringify_paths(self.metadata)
            
            with open(metadata_file, 'w') as f:
                json.dump(serializable_metadata, f, indent=4)
            self.log(f"Metadata saved to {metadata_file}")
            if Console:
                Console.saved("Run metadata", str(metadata_file))
            
            self._update_run_history_csv()
            
        except Exception as e:
            self.log(f"Failed to save metadata: {e}", logging.ERROR)
            if Console:
                Console.error(f"Failed to save metadata: {e}")

    def _update_run_history_csv(self):
        """Append this run to the global run_history.csv file."""
        import csv
        history_file = Path("logs/run_history.csv")
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_exists = history_file.exists()
        
        fieldnames = [
            'run_id', 'timestamp', 'pipeline', 'league', 'season', 
            'status', 'input_file', 'output_dir'
        ]
        
        row = {
            'run_id': self.run_id,
            'timestamp': self.metadata['start_time'],
            'pipeline': self.name,
            'league': getattr(self.args, 'league', 'N/A').upper(),
            'season': getattr(self.args, 'season', 'N/A'),
            'status': self.metadata['status'],
            'input_file': str(getattr(self.args, 'input', 'N/A')),
            'output_dir': str(self.output_dir)
        }
        
        try:
            with open(history_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
            self.log(f"Run history updated: {history_file}")
        except Exception as e:
            self.log(f"Failed to update run history: {e}", logging.ERROR)

    def log(self, message: str, level: int = logging.INFO):
        """Helper for logging."""
        logger.log(level, f"[{self.name.upper()}] {message}")

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update run metrics for metadata."""
        self.metadata["metrics"].update(metrics)
