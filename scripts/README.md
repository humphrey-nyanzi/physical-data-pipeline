# Match Analysis Scripts

This directory contains the unified command-line interface (CLI) for the Match Analysis platform.

## Unified CLI: `match_analysis.py`

The project has been refactored to use a single entry point for all analysis pipelines. This replaces several standalone scripts and provides a consistent interface.

### Usage

```bash
python scripts/match_analysis.py <command> [options]
```

### Available Commands

#### 1. Full Pipeline (`full`) - **RECOMMENDED**

Executes the complete 4-phase workflow: Configuration → Data Cleaning → Analysis → Report Generation

```bash
python scripts/match_analysis.py full --league mens_league --input data/raw/raw_tracking_data.csv --output Output/
```

This is the primary way to process raw GPS tracking data end-to-end and generate club reports.

#### 2. Season Report (`season`)

Generates full season analysis and individual club reports.

```bash
python scripts/match_analysis.py season --league mens_league --input data/raw/raw_tracking_data.csv
```

#### 3. Weekly Report (`weekly`)

Generates GPS reports for a specific matchday.

```bash
python scripts/match_analysis.py weekly --md 11
```

### Options

Run any command with `--help` to see all available options:

```bash
python scripts/match_analysis.py full --help
python scripts/match_analysis.py season --help
python scripts/match_analysis.py weekly --help
```

## Deprecated Code

**Legacy Pattern (DO NOT USE):**
```python
# Old way - DEPRECATED
from src.pipeline.orchestrator import PipelineExecutor
executor = PipelineExecutor(league='mens_league')
executor.execute_full_pipeline('data.csv', 'output/')
```

Use the CLI instead:
```bash
python scripts/match_analysis.py full --league mens_league --input data.csv
```

## Legacy Scripts

Standalone scripts like `run_full_analysis.py`, `generate_reports.py`, etc., have been **deprecated and removed**. Their functionality is now fully integrated into the `match_analysis.py` tool via the `src/pipelines/` module.

---
**Last Updated:** February 19, 2026
**Migration Status:** Legacy orchestrator scheduled for removal after CLI deprecation period
