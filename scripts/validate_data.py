"""
Data validation and quality check script for Match-Analysis.

Performs comprehensive data validation before analysis.
"""

import sys
from pathlib import Path
import argparse
import json
import logging
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class DataValidator:
    """Validate data quality and schema."""

    REQUIRED_COLUMNS = [
        "p_name",
        "club_for",
        "club_against",
        "match_day",
        "general_position",
        "player_position",
        "duration",
    ]

    NUMERIC_COLUMNS = [
        "distance_km",
        "duration",
        "power_plays",
        "energy_kcal",
        "impacts",
        "sprint_distance_m",
    ]

    def __init__(self, input_file: Path, verbose: bool = False):
        """Initialize validator.

        Args:
            input_file: Path to CSV file to validate
            verbose: Enable verbose logging
        """
        self.input_file = Path(input_file)
        self.verbose = verbose
        self.df = None
        self.results = {}

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        logger.info(f"Data Validator initialized")
        logger.info(f"  File: {input_file}")

    def load_data(self) -> bool:
        """Load data from file.

        Returns:
            True if successful
        """
        try:
            logger.info("Loading data...")
            self.df = pd.read_csv(self.input_file)
            logger.info(f"  ✓ Loaded {len(self.df)} rows")
            logger.info(f"  ✓ {len(self.df.columns)} columns")
            return True
        except Exception as e:
            logger.error(f"  ✗ Failed to load file: {e}")
            return False

    def check_required_columns(self) -> Dict:
        """Check if required columns exist.

        Returns:
            Results dictionary
        """
        logger.info("\nValidating required columns...")

        missing = [c for c in self.REQUIRED_COLUMNS if c not in self.df.columns]
        present = [c for c in self.REQUIRED_COLUMNS if c in self.df.columns]

        result = {
            "check": "required_columns",
            "required": len(self.REQUIRED_COLUMNS),
            "present": len(present),
            "missing": missing,
            "status": "pass" if not missing else "fail",
        }

        logger.info(f"  Required columns: {result['present']}/{result['required']}")
        if missing:
            logger.warning(f"  Missing: {missing}")

        self.results["required_columns"] = result
        return result

    def check_data_types(self) -> Dict:
        """Check data types are appropriate.

        Returns:
            Results dictionary
        """
        logger.info("\nValidating data types...")

        issues = []
        for col in self.NUMERIC_COLUMNS:
            if col in self.df.columns:
                if not pd.api.types.is_numeric_dtype(self.df[col]):
                    issues.append(f"{col} is not numeric")

        result = {
            "check": "data_types",
            "total_columns": len(self.df.columns),
            "numeric_columns": len(
                [c for c in self.NUMERIC_COLUMNS if c in self.df.columns]
            ),
            "issues": issues,
            "status": "pass" if not issues else "warn",
        }

        logger.info(f"  Numeric columns: {result['numeric_columns']}")
        if issues:
            for issue in issues:
                logger.warning(f"    {issue}")

        self.results["data_types"] = result
        return result

    def check_missing_values(self) -> Dict:
        """Check for missing values.

        Returns:
            Results dictionary
        """
        logger.info("\nChecking missing values...")

        missing_counts = self.df.isnull().sum()
        missing_percentages = (missing_counts / len(self.df) * 100).round(2)

        critical_missing = []
        for col in self.REQUIRED_COLUMNS:
            if col in self.df.columns and missing_percentages[col] > 5:
                critical_missing.append(
                    {
                        "column": col,
                        "count": int(missing_counts[col]),
                        "percentage": float(missing_percentages[col]),
                    }
                )

        overall_missing_pct = (
            self.df.isnull().sum().sum() / (len(self.df) * len(self.df.columns)) * 100
        )

        result = {
            "check": "missing_values",
            "total_missing": int(self.df.isnull().sum().sum()),
            "missing_percentage": round(overall_missing_pct, 2),
            "critical_columns": critical_missing,
            "status": "pass" if overall_missing_pct < 10 else "fail",
        }

        logger.info(
            f"  Total missing: {result['total_missing']} ({result['missing_percentage']}%)"
        )
        if critical_missing:
            logger.warning(f"  Critical missing data:")
            for item in critical_missing:
                logger.warning(f"    {item['column']}: {item['percentage']}%")

        self.results["missing_values"] = result
        return result

    def check_duplicate_records(self) -> Dict:
        """Check for duplicate records.

        Returns:
            Results dictionary
        """
        logger.info("\nChecking for duplicates...")

        all_duplicates = self.df.duplicated().sum()

        # Check for player-match duplicates (should be unique)
        if "p_name" in self.df.columns and "match_day" in self.df.columns:
            player_match_dups = self.df.duplicated(subset=["p_name", "match_day"]).sum()
        else:
            player_match_dups = 0

        result = {
            "check": "duplicate_records",
            "total_duplicates": int(all_duplicates),
            "player_match_duplicates": int(player_match_dups),
            "duplicate_percentage": round(all_duplicates / len(self.df) * 100, 2),
            "status": "pass" if all_duplicates == 0 else "warn",
        }

        logger.info(f"  Total duplicates: {result['total_duplicates']}")
        if player_match_dups > 0:
            logger.warning(f"  Player-match duplicates: {player_match_dups}")

        self.results["duplicates"] = result
        return result

    def check_value_ranges(self) -> Dict:
        """Check for outliers and invalid ranges.

        Returns:
            Results dictionary
        """
        logger.info("\nChecking value ranges...")

        issues = []

        # Check distance
        if "distance_km" in self.df.columns:
            distance_max = self.df["distance_km"].max()
            distance_min = self.df["distance_km"].min()
            if distance_max > 50 or distance_min < 0:
                issues.append(
                    f"Unusual distance range: {distance_min}km to {distance_max}km"
                )

        # Check duration
        if "duration" in self.df.columns:
            duration_max = self.df["duration"].max()
            duration_min = self.df["duration"].min()
            if duration_max > 120 or duration_min < 0:
                issues.append(
                    f"Unusual duration range: {duration_min}min to {duration_max}min"
                )

        # Check energy
        if "energy_kcal" in self.df.columns:
            energy_max = self.df["energy_kcal"].max()
            if energy_max > 500:
                issues.append(f"Unusual maximum energy: {energy_max}kcal")

        result = {
            "check": "value_ranges",
            "numeric_columns_checked": len(
                [c for c in self.NUMERIC_COLUMNS if c in self.df.columns]
            ),
            "issues": issues,
            "status": "pass" if not issues else "warn",
        }

        logger.info(f"  Columns checked: {result['numeric_columns_checked']}")
        if issues:
            for issue in issues:
                logger.warning(f"    {issue}")

        self.results["value_ranges"] = result
        return result

    def calculate_quality_score(self) -> float:
        """Calculate overall data quality score (0-100).

        Returns:
            Quality score
        """
        checks = {
            "required_columns": 25,
            "data_types": 15,
            "missing_values": 25,
            "duplicates": 15,
            "value_ranges": 20,
        }

        score = 0
        for check, weight in checks.items():
            result = self.results.get(check, {})
            status = result.get("status", "fail")

            if status == "pass":
                score += weight
            elif status == "warn":
                score += weight * 0.5
            # 'fail' contributes 0

        return round(score, 1)

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results.

        Returns:
            List of recommendations
        """
        recommendations = []

        # Based on missing values
        missing = self.results.get("missing_values", {})
        if missing.get("missing_percentage", 0) > 5:
            recommendations.append(
                "High missing data percentage. Consider data imputation or exclusion."
            )

        # Based on duplicates
        dups = self.results.get("duplicates", {})
        if dups.get("total_duplicates", 0) > 0:
            recommendations.append(
                "Duplicate records found. Review and remove if appropriate."
            )

        # Based on value ranges
        ranges = self.results.get("value_ranges", {})
        if ranges.get("issues"):
            recommendations.append(
                "Unusual value ranges detected. Review outliers before analysis."
            )

        # Based on required columns
        required = self.results.get("required_columns", {})
        if required.get("missing"):
            recommendations.append(
                f"Missing required columns: {required['missing']}. Data may be incomplete."
            )

        if not recommendations:
            recommendations.append("Data quality appears good. Ready for analysis.")

        return recommendations

    def validate(self) -> Tuple[bool, Dict]:
        """Run full validation.

        Returns:
            Tuple of (success, results)
        """
        # Load data
        if not self.load_data():
            return False, {}

        # Run all checks
        self.check_required_columns()
        self.check_data_types()
        self.check_missing_values()
        self.check_duplicate_records()
        self.check_value_ranges()

        # Calculate quality score
        quality_score = self.calculate_quality_score()

        # Generate recommendations
        recommendations = self.generate_recommendations()

        # Compile full report
        report = {
            "file": str(self.input_file),
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "quality_score": quality_score,
            "checks": self.results,
            "recommendations": recommendations,
            "ready_for_analysis": quality_score >= 70,
        }

        return True, report

    def print_report(self, report: Dict) -> None:
        """Print validation report.

        Args:
            report: Report dictionary
        """
        print(f"\n{'=' * 70}")
        print("DATA VALIDATION REPORT")
        print(f"{'=' * 70}")

        print(f"\nFile: {report['file']}")
        print(f"Rows: {report['rows']:,}")
        print(f"Columns: {report['columns']}")

        print(f"\n{'=' * 70}")
        print(f"QUALITY SCORE: {report['quality_score']}/100")
        if report["quality_score"] >= 80:
            print("✓ Excellent data quality")
        elif report["quality_score"] >= 70:
            print("✓ Good data quality (ready for analysis)")
        elif report["quality_score"] >= 60:
            print("⚠ Fair data quality (review recommendations)")
        else:
            print("✗ Poor data quality (significant issues)")
        print(f"{'=' * 70}")

        print("\nValidation Results:")
        for check_name, result in report["checks"].items():
            status_symbol = (
                "✓"
                if result["status"] == "pass"
                else "⚠"
                if result["status"] == "warn"
                else "✗"
            )
            print(f"  {status_symbol} {check_name}: {result['status'].upper()}")

        print("\nRecommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")

        print(f"\n{'=' * 70}")
        if report["ready_for_analysis"]:
            print("✓ Data is ready for analysis")
        else:
            print("✗ Address issues before proceeding with analysis")
        print(f"{'=' * 70}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate data quality before analysis",
        epilog="""
Examples:
  python scripts/validate_data.py --input data.csv
  python scripts/validate_data.py --input data.csv -v
        """,
    )

    parser.add_argument("--input", required=True, help="Path to CSV file to validate")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Validate file exists
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"File not found: {input_file}")
        sys.exit(1)

    # Run validation
    validator = DataValidator(input_file, verbose=args.verbose)
    success, report = validator.validate()

    if success:
        validator.print_report(report)

        # Save report
        report_file = input_file.parent / f"{input_file.stem}_validation_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to: {report_file}")

        sys.exit(0 if report["ready_for_analysis"] else 1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
