"""
Configuration management for Match-Analysis pipeline.

Handles YAML configuration loading, validation, and runtime access.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages application configuration from YAML files."""

    _instance = None
    _config = None

    def __new__(cls):
        """Singleton pattern for config manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration manager."""
        if self._config is None:
            self.reload_config()

    @staticmethod
    def get_config_path() -> Path:
        """Get path to configuration file."""
        config_path = Path(__file__).parent / "analysis_config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return config_path

    def reload_config(self) -> None:
        """Load/reload configuration from YAML file."""
        config_path = self.get_config_path()
        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Examples:
            config.get('leagues.mens_league.clubs')  # Returns 16
            config.get('analysis.min_distance_km')  # Returns 2.0
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_league_config(self, league: str) -> Dict[str, Any]:
        """Get complete configuration for a league.

        Args:
            league: League identifier ('mens_league' or 'womens_league')

        Returns:
            Dictionary with league configuration
        """
        league_lower = league.lower()
        config = self.get(f"leagues.{league_lower}")

        if not config:
            raise ValueError(f"League '{league}' not found in configuration")

        return config

    def get_analysis_config(self) -> Dict[str, Any]:
        """Get analysis parameters."""
        return self.get("analysis", {})

    def get_reporting_config(self) -> Dict[str, Any]:
        """Get reporting parameters."""
        return self.get("reporting", {})

    def get_validation_config(self) -> Dict[str, Any]:
        """Get data validation parameters."""
        return self.get("validation", {})

    def get_export_config(self) -> Dict[str, Any]:
        """Get export format parameters."""
        return self.get("export", {})

    def get_batch_config(self) -> Dict[str, Any]:
        """Get batch processing parameters."""
        return self.get("batch", {})

    def validate_league(self, league: str) -> bool:
        """Check if league is valid.

        Args:
            league: League identifier

        Returns:
            True if league is valid
        """
        valid_leagues = list(self.get("leagues", {}).keys())
        return league.lower() in valid_leagues

    def get_valid_leagues(self) -> list:
        """Get list of valid league identifiers."""
        return list(self.get("leagues", {}).keys())


# Global config instance
config = ConfigManager()
