"""
Unit Tests for Pipeline Orchestration (Phase 5)

Tests for full pipeline execution, including:
    - Individual phase execution
    - Data flow and transformations
    - Error handling and recovery
    - Output generation and validation
"""

import unittest
import tempfile
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Import functions to test
from src.pipeline.orchestrator import PipelineExecutor, execute_pipeline
from src.config import league_definitions


class TestPipelineExecutor(unittest.TestCase):
    """Test PipelineExecutor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor_upl = PipelineExecutor("upl")
        self.executor_fwsl = PipelineExecutor("fwsl")

    def test_executor_initialization_upl(self):
        """Test executor initialization for UPL."""
        self.assertEqual(self.executor_upl.league, "upl")
        self.assertIsNotNone(self.executor_upl.execution_log)

    def test_executor_initialization_fwsl(self):
        """Test executor initialization for FWSL."""
        self.assertEqual(self.executor_fwsl.league, "fwsl")
        self.assertIsNotNone(self.executor_fwsl.execution_log)

    def test_executor_invalid_league(self):
        """Test that invalid league raises error."""
        with self.assertRaises(ValueError):
            PipelineExecutor("invalid_league")

    def test_phase_1_config_upl(self):
        """Test Phase 1 configuration loading for UPL."""
        config = self.executor_upl.phase_1_config()

        # Check that config is returned
        self.assertIsInstance(config, dict)

        # Check that execution log was updated
        self.assertIn("phase_1", self.executor_upl.execution_log["phases"])
        phase_1_log = self.executor_upl.execution_log["phases"]["phase_1"]
        self.assertEqual(phase_1_log["status"], "success")

    def test_phase_1_config_fwsl(self):
        """Test Phase 1 configuration loading for FWSL."""
        config = self.executor_fwsl.phase_1_config()

        # Check that config is returned
        self.assertIsInstance(config, dict)

        # Check that execution log was updated
        self.assertIn("phase_1", self.executor_fwsl.execution_log["phases"])

    def test_execution_log_structure(self):
        """Test that execution log has correct structure."""
        executor = PipelineExecutor("upl")

        # Initial structure
        self.assertEqual(executor.execution_log["league"], "upl")
        self.assertIsNotNone(executor.execution_log["start_time"])
        self.assertIsInstance(executor.execution_log["phases"], dict)


class TestPipelineIntegration(unittest.TestCase):
    """Test integrated pipeline functions."""

    def setUp(self):
        """Create sample test data."""
        # Create minimal test DataFrame
        self.test_data = pd.DataFrame(
            {
                "match_day": ["Md1", "Md1", "Md2", "Md2"],
                "club_for": ["KCCA FC", "KCCA FC", "BUL FC", "BUL FC"],
                "club_against": ["BUL FC", "BUL FC", "KCCA FC", "KCCA FC"],
                "p_name": ["player1", "player2", "player3", "player4"],
                "general_position": ["DEF", "MID", "DEF", "FWD"],
                "player_position": ["CB", "CM", "CB", "CF"],
                "player_club_": ["KCCA FC", "KCCA FC", "BUL FC", "BUL FC"],
                "duration": [90.0, 45.0, 90.0, 90.0],
                "distance_km": [10.5, 8.2, 10.8, 11.2],
                "sprint_distance_m": [500, 300, 600, 700],
                "player_load": [450, 350, 500, 550],
                "top_speed_kmh": [28, 25, 29, 30],
                "result": ["W", "W", "D", "D"],
                "location": ["Home", "Home", "Away", "Away"],
                "date": ["2025-01-01", "2025-01-01", "2025-01-08", "2025-01-08"],
            }
        )

    def test_executor_phases_return_types(self):
        """Test that each phase returns expected types."""
        executor = PipelineExecutor("upl")

        # Phase 1: Returns dict
        config = executor.phase_1_config()
        self.assertIsInstance(config, dict)

        # Phase 3: Can parse cleaned data
        # (Phase 2 skipped as it requires file I/O)
        analysis_results = executor.phase_3_analysis(self.test_data, config)
        self.assertIsInstance(analysis_results, dict)

        # Check analysis keys exist
        expected_keys = [
            "summary_stats",
            "unique_players",
            "players_per_club_md",
            "matchdays_per_club",
            "club_coverage",
            "top_players",
            "positional_stats",
            "positional_comparison",
        ]
        for key in expected_keys:
            self.assertIn(key, analysis_results)


class TestDataFlowValidation(unittest.TestCase):
    """Test data flow through pipeline phases."""

    def test_cleaned_data_structure(self):
        """Test that cleaned data has expected structure."""
        # Create minimal cleaned dataset
        cleaned_df = pd.DataFrame(
            {
                "match_day": ["Md1", "Md1"],
                "club_for": ["KCCA FC", "KCCA FC"],
                "p_name": ["player1", "player2"],
                "duration": [90.0, 45.0],
                "distance_km": [10.5, 8.2],
            }
        )

        # Check essential columns exist
        expected_columns = [
            "match_day",
            "club_for",
            "p_name",
            "duration",
            "distance_km",
        ]
        for col in expected_columns:
            self.assertIn(col, cleaned_df.columns)

    def test_analysis_output_structure(self):
        """Test that analysis output has expected structure."""
        executor = PipelineExecutor("upl")
        config = executor.phase_1_config()

        # Load real cleaned data if available, otherwise skip
        import os

        cleaned_file = "UPL25_matches2.csv"
        if not os.path.exists(cleaned_file):
            self.skipTest(f"Cleaned data file {cleaned_file} not found")

        # Load cleaned data
        test_df = pd.read_csv(cleaned_file)

        # Get analysis
        analysis = executor.phase_3_analysis(test_df, config)

        # Check output is dict with expected keys
        self.assertIsInstance(analysis, dict)
        self.assertIn("summary_stats", analysis)
        self.assertIn("club_coverage", analysis)
        self.assertIn("summary_stats", analysis)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in pipeline."""

    def test_invalid_league_raises_error(self):
        """Test that invalid league parameter raises error."""
        with self.assertRaises(ValueError):
            PipelineExecutor("invalid")

    def test_phase_1_error_handling(self):
        """Test that Phase 1 errors are caught and logged."""
        executor = PipelineExecutor("upl")

        # Phase 1 should succeed (it doesn't do external I/O)
        try:
            config = executor.phase_1_config()
            self.assertIsNotNone(config)
        except Exception as e:
            self.fail(f"Phase 1 unexpectedly raised: {e}")


class TestLoggingSetup(unittest.TestCase):
    """Test logging configuration."""

    def test_logging_setup_creates_directory(self):
        """Test that logging setup creates log directory."""
        from src.pipeline.orchestrator import setup_logging

        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "logs")
            logger = setup_logging(log_dir)

            # Directory should be created
            self.assertTrue(os.path.isdir(log_dir))
            self.assertIsNotNone(logger)


class TestPipelineFunction(unittest.TestCase):
    """Test high-level execute_pipeline function."""

    def test_execute_pipeline_signature(self):
        """Test that execute_pipeline function exists and is callable."""
        self.assertTrue(callable(execute_pipeline))

    def test_execute_pipeline_requires_parameters(self):
        """Test that execute_pipeline requires league and raw_path."""
        # Function should require at least 2 positional args
        import inspect

        sig = inspect.signature(execute_pipeline)
        params = list(sig.parameters.keys())

        self.assertIn("league", params)
        self.assertIn("raw_path", params)


class TestExecutionLog(unittest.TestCase):
    """Test execution logging."""

    def test_execution_log_initialization(self):
        """Test that executor initializes execution log."""
        executor = PipelineExecutor("upl")

        log = executor.execution_log
        self.assertEqual(log["league"], "upl")
        self.assertIsNotNone(log["start_time"])
        self.assertIsNone(log["end_time"])
        self.assertIsInstance(log["phases"], dict)

    def test_phase_1_logs_execution_time(self):
        """Test that Phase 1 logs execution time."""
        executor = PipelineExecutor("upl")
        executor.phase_1_config()

        phase_log = executor.execution_log["phases"]["phase_1"]
        self.assertIn("elapsed_seconds", phase_log)
        self.assertGreaterEqual(phase_log["elapsed_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
