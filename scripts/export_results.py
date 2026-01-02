"""
Export analysis results to various formats.

Converts analysis outputs to Excel, CSV, JSON, and HTML formats.
"""

import sys
from pathlib import Path
import argparse
import json
import logging
from typing import Dict, List
import pandas as pd
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class ResultsExporter:
    """Export analysis results to various formats."""

    def __init__(self, analysis_dir: Path, output_dir: Path, verbose: bool = False):
        """Initialize exporter.

        Args:
            analysis_dir: Directory containing analysis CSV files
            output_dir: Output directory for exported files
            verbose: Enable verbose logging
        """
        self.analysis_dir = Path(analysis_dir)
        self.output_dir = Path(output_dir)
        self.verbose = verbose

        self.output_dir.mkdir(parents=True, exist_ok=True)

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        logger.info(f"Results Exporter initialized")
        logger.info(f"  Analysis directory: {analysis_dir}")
        logger.info(f"  Output directory: {output_dir}")

    def find_analysis_files(self) -> Dict[str, Path]:
        """Find all analysis CSV files.

        Returns:
            Dictionary mapping file type to path
        """
        files = {}

        for csv_file in self.analysis_dir.glob("*.csv"):
            file_type = csv_file.stem.replace("_", " ").title()
            files[file_type] = csv_file
            logger.debug(f"Found: {csv_file.name}")

        logger.info(f"Found {len(files)} CSV files")
        return files

    def load_all_csv_files(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files as DataFrames.

        Returns:
            Dictionary mapping file type to DataFrame
        """
        logger.info("Loading CSV files...")

        dfs = {}
        csv_files = self.find_analysis_files()

        for file_type, path in csv_files.items():
            try:
                df = pd.read_csv(path)
                dfs[file_type] = df
                logger.debug(f"  Loaded {path.name}: {len(df)} rows")
            except Exception as e:
                logger.warning(f"  Failed to load {path.name}: {e}")

        logger.info(f"Successfully loaded {len(dfs)} files")
        return dfs

    def export_to_excel(self, dfs: Dict[str, pd.DataFrame]) -> Path:
        """Export all DataFrames to Excel with multiple sheets.

        Args:
            dfs: Dictionary of DataFrames

        Returns:
            Path to exported file
        """
        logger.info("\nExporting to Excel...")

        output_file = self.output_dir / "analysis_results.xlsx"

        try:
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                # Write summary sheet
                summary_df = self._create_summary_sheet(dfs)
                summary_df.to_excel(writer, sheet_name="Summary", index=False)
                logger.debug(f"  Added Summary sheet")

                # Write each DataFrame as a sheet
                for sheet_name, df in dfs.items():
                    # Limit sheet name length (Excel limit: 31 chars)
                    sheet_name_short = sheet_name[:31]
                    df.to_excel(writer, sheet_name=sheet_name_short, index=False)
                    logger.debug(f"  Added {sheet_name} sheet")

                # Auto-format columns
                for sheet in writer.sheets.values():
                    for column in sheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        sheet.column_dimensions[column_letter].width = adjusted_width

            logger.info(f"  ✓ Exported to: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"  ✗ Excel export failed: {e}")
            raise

    def export_to_csv(self, dfs: Dict[str, pd.DataFrame]) -> List[Path]:
        """Export each DataFrame to CSV.

        Args:
            dfs: Dictionary of DataFrames

        Returns:
            List of exported file paths
        """
        logger.info("\nExporting to CSV...")

        csv_dir = self.output_dir / "csv_files"
        csv_dir.mkdir(parents=True, exist_ok=True)

        files = []
        for file_name, df in dfs.items():
            output_file = csv_dir / f"{file_name.lower().replace(' ', '_')}.csv"
            try:
                df.to_csv(output_file, index=False)
                logger.debug(f"  Exported: {output_file.name}")
                files.append(output_file)
            except Exception as e:
                logger.warning(f"  Failed to export {file_name}: {e}")

        logger.info(f"  ✓ Exported {len(files)} CSV files to: {csv_dir}")
        return files

    def export_to_json(self, dfs: Dict[str, pd.DataFrame]) -> List[Path]:
        """Export each DataFrame to JSON.

        Args:
            dfs: Dictionary of DataFrames

        Returns:
            List of exported file paths
        """
        logger.info("\nExporting to JSON...")

        json_dir = self.output_dir / "json_files"
        json_dir.mkdir(parents=True, exist_ok=True)

        files = []
        for file_name, df in dfs.items():
            output_file = json_dir / f"{file_name.lower().replace(' ', '_')}.json"
            try:
                # Convert to JSON with metadata
                data = {
                    "metadata": {
                        "source": str(self.analysis_dir),
                        "export_date": datetime.now().isoformat(),
                        "rows": len(df),
                        "columns": len(df.columns),
                    },
                    "data": df.to_dict(orient="records"),
                }

                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2, default=str)

                logger.debug(f"  Exported: {output_file.name}")
                files.append(output_file)
            except Exception as e:
                logger.warning(f"  Failed to export {file_name}: {e}")

        logger.info(f"  ✓ Exported {len(files)} JSON files to: {json_dir}")
        return files

    def export_to_html(self, dfs: Dict[str, pd.DataFrame]) -> Path:
        """Export summary statistics as HTML.

        Args:
            dfs: Dictionary of DataFrames

        Returns:
            Path to exported file
        """
        logger.info("\nExporting to HTML...")

        output_file = self.output_dir / "analysis_summary.html"

        try:
            html_parts = []

            # Header
            html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Analysis Results Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; background-color: white; }
        th { background-color: #007bff; color: white; padding: 10px; text-align: left; }
        td { border: 1px solid #ddd; padding: 8px; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .metadata { background-color: #e8f4f8; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
            """)

            # Title and metadata
            html_parts.append(f"""
<h1>Analysis Results Summary</h1>
<div class="metadata">
    <p><strong>Export Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p><strong>Analysis Directory:</strong> {self.analysis_dir}</p>
    <p><strong>Total Files:</strong> {len(dfs)}</p>
</div>
            """)

            # Add summary for each DataFrame
            for file_name, df in dfs.items():
                html_parts.append(f"<h2>{file_name}</h2>")
                html_parts.append(f"<p>Rows: {len(df)}, Columns: {len(df.columns)}</p>")

                # Display first few rows
                html_parts.append(df.head(10).to_html(index=False, border=0))

                # Add statistics
                if len(df) > 0:
                    html_parts.append("<h3>Statistics</h3>")
                    html_parts.append(df.describe().to_html())

            # Footer
            html_parts.append("""
</body>
</html>
            """)

            # Write file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(html_parts))

            logger.info(f"  ✓ Exported to: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"  ✗ HTML export failed: {e}")
            raise

    def _create_summary_sheet(self, dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create summary sheet for Excel export.

        Args:
            dfs: Dictionary of DataFrames

        Returns:
            Summary DataFrame
        """
        summary_data = []

        for file_name, df in dfs.items():
            summary_data.append(
                {
                    "File Name": file_name,
                    "Rows": len(df),
                    "Columns": len(df.columns),
                    "Memory (MB)": df.memory_usage(deep=True).sum() / 1024**2,
                }
            )

        summary_df = pd.DataFrame(summary_data)
        return summary_df

    def export(self, format: str = "excel") -> Dict:
        """Export analysis results in specified format.

        Args:
            format: Export format ('excel', 'csv', 'json', 'html', or 'all')

        Returns:
            Dictionary with export results
        """
        logger.info(f"{'=' * 70}")
        logger.info("RESULTS EXPORT")
        logger.info(f"{'=' * 70}\n")

        # Load data
        dfs = self.load_all_csv_files()

        if not dfs:
            logger.error("No CSV files found to export")
            return {"success": False}

        results = {"success": True, "format": format, "files": {}}

        # Export based on format
        if format in ["excel", "all"]:
            try:
                file_path = self.export_to_excel(dfs)
                results["files"]["excel"] = str(file_path)
            except Exception as e:
                logger.error(f"Excel export failed: {e}")
                results["success"] = False

        if format in ["csv", "all"]:
            try:
                file_paths = self.export_to_csv(dfs)
                results["files"]["csv"] = [str(f) for f in file_paths]
            except Exception as e:
                logger.error(f"CSV export failed: {e}")
                results["success"] = False

        if format in ["json", "all"]:
            try:
                file_paths = self.export_to_json(dfs)
                results["files"]["json"] = [str(f) for f in file_paths]
            except Exception as e:
                logger.error(f"JSON export failed: {e}")
                results["success"] = False

        if format in ["html", "all"]:
            try:
                file_path = self.export_to_html(dfs)
                results["files"]["html"] = str(file_path)
            except Exception as e:
                logger.error(f"HTML export failed: {e}")
                results["success"] = False

        logger.info(f"\n{'=' * 70}")
        logger.info("EXPORT SUMMARY")
        logger.info(f"{'=' * 70}")
        logger.info(f"Status: {'✓ Success' if results['success'] else '✗ Failed'}")
        logger.info(f"Format: {format}")
        logger.info(f"Output Directory: {self.output_dir}")

        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export analysis results to various formats",
        epilog="""
Examples:
  python scripts/export_results.py --analysis results/ --output-dir exports/ --format excel
  python scripts/export_results.py --analysis results/ --output-dir exports/ --format all
  python scripts/export_results.py --analysis results/ --output-dir exports/ --format csv
        """,
    )

    parser.add_argument(
        "--analysis", required=True, help="Path to analysis results directory"
    )
    parser.add_argument(
        "--output-dir", required=True, help="Output directory for exported files"
    )
    parser.add_argument(
        "--format",
        choices=["excel", "csv", "json", "html", "all"],
        default="excel",
        help="Export format (default: excel)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Validate directories
    analysis_dir = Path(args.analysis)
    if not analysis_dir.exists():
        logger.error(f"Analysis directory not found: {analysis_dir}")
        sys.exit(1)

    output_dir = Path(args.output_dir)

    # Export results
    exporter = ResultsExporter(analysis_dir, output_dir, verbose=args.verbose)
    results = exporter.export(format=args.format)

    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
