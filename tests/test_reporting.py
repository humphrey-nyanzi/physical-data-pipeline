"""
Unit Tests for Reporting Module (Phase 4)

Tests for report_builder and document_generation modules.
Validates data aggregation, comparison calculations, and document utilities.

Test Coverage:
    - Matchday statistics aggregation
    - Player monitoring statistics
    - Metric summary calculations
    - Top player identification
    - Positional analysis
    - Season comparisons
    - Speed zone breakdown
    - Coverage summary
    - Document generation utilities
"""

import unittest
import pandas as pd
import numpy as np
from io import BytesIO

# Import functions to test
from src.reporting.report_builder import (
    get_matchday_stats,
    get_players_monitored_stats,
    get_metric_summary,
    get_top_players_by_metric,
    get_average_metrics_by_position,
    get_average_metrics_per_matchday,
    club_vs_season_comparison,
    positional_comparison_vs_season,
    get_speed_zone_breakdown,
    compute_coverage_summary,
)

from src.reporting.document_generation import (
    fmt_cell_value,
    add_dataframe_as_table,
    create_report_document,
    save_document,
)


class TestReportBuilderBasics(unittest.TestCase):
    """Test basic report builder functions with sample data."""

    def setUp(self):
        """Create sample data for testing."""
        # Sample club data
        self.club_df = pd.DataFrame(
            {
                "match_day": ["Md1", "Md1", "Md2", "Md2", "Md3"],
                "club_against": ["Team A", "Team A", "Team B", "Team B", "Team C"],
                "p_name": ["alice", "bob", "alice", "charlie", "alice"],
                "general_position": ["DEF", "MID", "DEF", "FWD", "DEF"],
                "duration": [90, 45, 90, 90, 85],
                "result": ["W", "W", "D", "D", "L"],
                "location": ["Home", "Home", "Away", "Away", "Home"],
                "distance_km": [10.5, 8.2, 10.8, 11.2, 9.5],
                "sprint_distance_m": [500, 300, 600, 700, 450],
                "player_load": [450, 350, 500, 550, 400],
                "top_speed_kmh": [28, 25, 29, 30, 27],
            }
        )

        self.matchday_order = ["Md1", "Md2", "Md3", "Md4"]
        self.volume_metrics = ["distance_km", "sprint_distance_m"]
        self.intensity_metrics = ["player_load", "top_speed_kmh"]
        self.metric_names = {
            "distance_km": "Distance",
            "sprint_distance_m": "Sprint Distance",
            "player_load": "Player Load",
            "top_speed_kmh": "Top Speed",
        }

    def test_matchday_stats_shape(self):
        """Test that matchday stats returns correct shape."""
        result = get_matchday_stats(self.club_df, self.matchday_order)

        # Should have all matchdays
        self.assertEqual(len(result), len(self.matchday_order))

        # Should have correct columns
        expected_cols = {
            "Match Day",
            "Opponent Club",
            "Number of Players Monitored",
            "Average Session Duration (min)",
            "Match Result",
            "Match Location",
        }
        self.assertTrue(expected_cols.issubset(set(result.columns)))

    def test_players_monitored_stats(self):
        """Test player monitoring statistics."""
        result = get_players_monitored_stats(self.club_df)

        # Should have 3 unique players
        self.assertEqual(len(result), 3)

        # Should have correct columns
        expected_cols = {"Player Name", "Position", "Match Days Analysed"}
        self.assertTrue(expected_cols.issubset(set(result.columns)))

        # Check alice appears 3 times
        alice_row = result[result["Player Name"] == "Alice"]
        self.assertEqual(alice_row.iloc[0]["Match Days Analysed"], 3)

    def test_metric_summary_calculation(self):
        """Test metric summary aggregation."""
        result = get_metric_summary(
            self.club_df, self.volume_metrics, self.intensity_metrics, self.metric_names
        )

        # Should have 4 rows (one per metric)
        self.assertEqual(len(result), 4)

        # Should have correct columns
        expected_cols = {"Metric", "Total", "Max", "Min", "Mean", "Std Dev", "Range"}
        self.assertTrue(expected_cols.issubset(set(result.columns)))

        # Check Distance total is sum of distance_km
        distance_row = result[result["Metric"] == "Distance"]
        expected_total = self.club_df["distance_km"].sum()
        self.assertAlmostEqual(distance_row.iloc[0]["Total"], expected_total, places=1)

    def test_top_players_by_metric(self):
        """Test top player identification."""
        all_metrics = self.volume_metrics + self.intensity_metrics
        result = get_top_players_by_metric(self.club_df, all_metrics, self.metric_names)

        # Should have metrics as columns (one per metric)
        self.assertGreater(len(result.columns), 0)

    def test_positional_averages(self):
        """Test positional metric averaging."""
        result = get_average_metrics_by_position(
            self.club_df, self.volume_metrics, self.intensity_metrics, self.metric_names
        )

        # Should have position in index
        self.assertIn("Position", result.iloc[:, 0].values)

    def test_matchday_trends(self):
        """Test matchday trend calculation."""
        display_df, plot_df = get_average_metrics_per_matchday(
            self.club_df,
            self.matchday_order,
            self.volume_metrics,
            self.intensity_metrics,
            self.metric_names,
        )

        # Should have matchdays with data
        self.assertGreater(len(display_df), 0)
        self.assertEqual(len(plot_df), len(display_df))


class TestComparisonFunctions(unittest.TestCase):
    """Test comparison functions."""

    def setUp(self):
        """Create sample data for testing."""
        # Club data (subset)
        self.club_df = pd.DataFrame(
            {
                "p_name": ["p1", "p2", "p3"],
                "general_position": ["DEF", "MID", "FWD"],
                "distance_km": [10.0, 8.0, 9.0],
                "player_load": [400, 350, 380],
            }
        )

        # Season data (larger, with different averages)
        self.season_df = pd.DataFrame(
            {
                "p_name": ["p1", "p2", "p3", "p4", "p5"],
                "general_position": ["DEF", "MID", "FWD", "DEF", "MID"],
                "distance_km": [9.0, 8.5, 8.5, 9.5, 8.0],
                "player_load": [380, 370, 370, 390, 360],
            }
        )

        self.volume_metrics = ["distance_km"]
        self.intensity_metrics = ["player_load"]
        self.metric_names = {
            "distance_km": "Distance",
            "player_load": "Player Load",
        }

    def test_club_vs_season_comparison(self):
        """Test season comparison calculation."""
        result = club_vs_season_comparison(
            self.club_df,
            self.season_df,
            self.volume_metrics,
            self.intensity_metrics,
            self.metric_names,
        )

        # Should have 2 rows (one per metric)
        self.assertEqual(len(result), 2)

        # Should have comparison columns
        expected_cols = {"Club Average", "Season Average", "% Difference"}
        self.assertTrue(expected_cols.issubset(set(result.columns)))

    def test_positional_comparison(self):
        """Test positional comparison."""
        result = positional_comparison_vs_season(
            self.club_df,
            self.season_df,
            self.volume_metrics,
            self.intensity_metrics,
            self.metric_names,
        )

        # Should have multiple rows for metrics x positions
        self.assertGreater(len(result), 2)


class TestSpeedZones(unittest.TestCase):
    """Test speed zone breakdown."""

    def setUp(self):
        """Create sample data with speed zones."""
        self.club_df = pd.DataFrame(
            {
                "general_position": ["DEF", "MID", "FWD"],
                "distance_in_speed_zone_1_km": [2.0, 1.5, 1.2],
                "distance_in_speed_zone_2_km": [3.0, 3.5, 2.8],
                "distance_in_speed_zone_3_km": [2.5, 2.0, 2.5],
                "distance_in_speed_zone_4_km": [1.5, 1.2, 1.8],
                "distance_in_speed_zone_5_km": [1.0, 0.8, 1.2],
            }
        )

    def test_speed_zone_breakdown(self):
        """Test speed zone aggregation."""
        distances, percentages = get_speed_zone_breakdown(self.club_df)

        # Should have zones as columns
        expected_zones = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
        for zone in expected_zones:
            self.assertIn(zone, distances.columns)

        # Percentages should sum to ~100 per position
        for pos in percentages.index:
            total = percentages.loc[pos].sum()
            self.assertAlmostEqual(total, 100.0, places=1)


class TestCoverageSummary(unittest.TestCase):
    """Test coverage summary calculation."""

    def setUp(self):
        """Create sample data."""
        self.club_df = pd.DataFrame(
            {
                "match_day": ["Md1", "Md1", "Md2", "Md3"],
                "p_name": ["p1", "p2", "p1", "p2"],
            }
        )
        self.matchday_order = ["Md1", "Md2", "Md3", "Md4", "Md5"]

    def test_coverage_summary(self):
        """Test coverage summary calculation."""
        result = compute_coverage_summary(self.club_df, self.matchday_order)

        # Check expected keys
        expected_keys = {
            "total_matchdays_available",
            "matchdays_with_data",
            "unique_players",
            "total_sessions",
        }
        self.assertTrue(expected_keys.issubset(set(result.keys())))

        # Verify values
        self.assertEqual(result["total_matchdays_available"], 5)
        self.assertEqual(result["matchdays_with_data"], 3)
        self.assertEqual(result["unique_players"], 2)


class TestDocumentGeneration(unittest.TestCase):
    """Test document generation utilities."""

    def test_fmt_cell_value_float(self):
        """Test cell value formatting for floats."""
        result = fmt_cell_value(3.14159)
        self.assertEqual(result, "3.14")

    def test_fmt_cell_value_int(self):
        """Test cell value formatting for integers."""
        result = fmt_cell_value(42)
        self.assertEqual(result, "42")

    def test_fmt_cell_value_nan(self):
        """Test cell value formatting for NaN."""
        result = fmt_cell_value(np.nan)
        self.assertEqual(result, "")

    def test_fmt_cell_value_none(self):
        """Test cell value formatting for None."""
        result = fmt_cell_value(None)
        self.assertEqual(result, "")

    def test_create_report_document(self):
        """Test report document creation."""
        doc = create_report_document("Test Club")

        # Document should have content
        self.assertGreater(len(doc.paragraphs), 0)

    def test_add_dataframe_as_table(self):
        """Test adding DataFrame as table to document."""
        doc = create_report_document("Test")
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

        add_dataframe_as_table(doc, df)

        # Should have added a table
        self.assertEqual(len(doc.tables), 1)

        # Table should have correct dimensions
        self.assertEqual(len(doc.tables[0].rows), 3)  # 1 header + 2 data
        self.assertEqual(len(doc.tables[0].columns), 2)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_club_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pd.DataFrame(
            {
                "match_day": [],
                "club_against": [],
                "p_name": [],
                "general_position": [],
                "duration": [],
                "result": [],
                "location": [],
                "distance_km": [],
            }
        )

        matchday_order = ["Md1", "Md2"]

        # Should handle empty data gracefully
        result = get_matchday_stats(empty_df, matchday_order)
        self.assertEqual(len(result), len(matchday_order))

    def test_single_player(self):
        """Test with single player data."""
        single_df = pd.DataFrame(
            {
                "p_name": ["alice"],
                "general_position": ["DEF"],
                "match_day": ["Md1"],
            }
        )

        result = get_players_monitored_stats(single_df)
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
