# Match Analysis Scripts

This directory contains the unified command-line interface (CLI) for the FUFA Match Analysis platform.

## Unified CLI: `match_analysis.py`

The project has been refactored to use a single entry point for all analysis pipelines. This replaces several standalone scripts and provides a consistent interface.

### Usage

```bash
python scripts/match_analysis.py <command> [options]
```

### Available Commands

#### 1. Weekly Report (`weekly`)

Generates GPS reports for a specific matchday.

```bash
python scripts/match_analysis.py weekly --md 11
```

#### 2. Season Report (`season`)

Generates full season analysis and individual club reports.

```bash
python scripts/match_analysis.py season --league upl --input data/raw/all_catapult_data_16_Jul_25.csv
```

### Options

Run any command with `--help` to see all available options:

```bash
python scripts/match_analysis.py weekly --help
python scripts/match_analysis.py season --help
```

## Legacy Scripts

Standalone scripts like `run_full_analysis.py`, `generate_reports.py`, etc., have been **deprecated and removed**. Their functionality is now fully integrated into the `match_analysis.py` tool via the `src/pipelines/` module.

---
**Organization:** FUFA-RST
**Last Updated:** January 21, 2026
