# Scripts - Production Analysis Pipeline

This directory contains production-ready Python CLI scripts that replace the Jupyter notebook workflows. All scripts support command-line argument parsing, comprehensive logging, and error handling.

## Quick Start

### 1. Data Cleaning
```bash
python scripts/process_league_data.py \
  --league upl \
  --input UPL25_matches2.csv \
  --output cleaned_data.csv
```

### 2. Statistical Analysis
```bash
python scripts/generate_analysis.py \
  --league upl \
  --input cleaned_data.csv \
  --output analysis_results/
```

### 3. Report Generation
```bash
python scripts/generate_reports.py \
  --cleaned cleaned_data.csv \
  --analysis analysis_results/ \
  --output reports/
```

### 4. Complete Pipeline (All Steps)
```bash
python scripts/run_full_analysis.py \
  --league upl \
  --input UPL25_matches2.csv \
  --output results/
```

## Scripts Overview

### `process_league_data.py`
**Data cleaning and preprocessing script**

Purpose: Standardize raw Catapult data, normalize club names, compute derived metrics

```bash
python scripts/process_league_data.py --help

# Usage
python scripts/process_league_data.py \
  --league {upl|fwsl} \
  --input RAW_CSV_FILE \
  --output CLEANED_CSV_FILE \
  [--verbose]
```

**Output**: Single cleaned CSV file ready for analysis

---

### `generate_analysis.py`
**Statistical analysis computation script**

Purpose: Execute 13+ analytical functions on cleaned data

```bash
python scripts/generate_analysis.py --help

# Usage
python scripts/generate_analysis.py \
  --league {upl|fwsl} \
  --input CLEANED_CSV \
  --output ANALYSIS_OUTPUT_DIR \
  [--verbose]
```

**Output**: Directory containing:
- `summary_stats.csv` - Descriptive statistics
- `unique_players.csv` - Player count analysis
- `top_players.csv` - Player rankings
- `club_coverage.csv` - Data coverage metrics
- `positional_stats.csv` - Position-based analysis
- `analysis_metadata.json` - Analysis results metadata

---

### `generate_reports.py`
**DOCX report generation script**

Purpose: Create professional per-club reports

```bash
python scripts/generate_reports.py --help

# Usage
python scripts/generate_reports.py \
  --cleaned CLEANED_CSV \
  --analysis ANALYSIS_DIR \
  --output REPORTS_DIR \
  [--league {upl|fwsl}] \
  [--verbose]
```

**Output**: Directory containing one DOCX report per club

---

### `run_full_analysis.py`
**Complete end-to-end pipeline orchestration**

Purpose: Execute all phases (cleaning → analysis → reporting) in sequence

```bash
python scripts/run_full_analysis.py --help

# Usage
python scripts/run_full_analysis.py \
  --league {upl|fwsl} \
  --input RAW_CSV \
  --output RESULTS_DIR \
  [--verbose] \
  [--interactive]
```

**Output Structure**:
```
results/
├── 01_cleaned/
│   └── {league}_cleaned.csv
├── 02_analysis/
│   ├── summary_stats.csv
│   ├── unique_players.csv
│   ├── top_players.csv
│   ├── club_coverage.csv
│   ├── positional_stats.csv
│   └── analysis_metadata.json
└── 03_reports/
    ├── Club_A_Report.docx
    ├── Club_B_Report.docx
    └── [one report per club]
```

## Common Workflows

### Workflow 1: Process Single League
```bash
# Clean, analyze, and generate reports for UPL
python scripts/run_full_analysis.py \
  --league upl \
  --input UPL25_matches2.csv \
  --output upl_results/

# Reports available in: upl_results/03_reports/
```

### Workflow 2: Process Both Leagues
```bash
# UPL
python scripts/run_full_analysis.py --league upl --input UPL25_matches2.csv -o upl_results/

# FWSL
python scripts/run_full_analysis.py --league fwsl --input FWSL25_matches2.csv -o fwsl_results/
```

### Workflow 3: Interactive Mode with Confirmations
```bash
python scripts/run_full_analysis.py \
  --league upl \
  --input data.csv \
  --output results/ \
  --interactive

# Output:
# ✓ Input validation successful
# [Continue to Phase 1? (y/n)] y
# Running data cleaning...
# [Continue to Phase 2? (y/n)] y
# Running analysis...
# [Continue to Phase 3? (y/n)] y
# Generating reports...
```

### Workflow 4: Individual Phase Execution
```bash
# Clean only
python scripts/process_league_data.py --league upl --input raw.csv --output cleaned.csv

# Analyze only (after cleaning)
python scripts/generate_analysis.py --league upl --input cleaned.csv --output analysis/

# Report only (after analysis)
python scripts/generate_reports.py --cleaned cleaned.csv --analysis analysis/ --output reports/
```

### Workflow 5: Verbose Debugging
```bash
python scripts/run_full_analysis.py \
  --league upl \
  --input data.csv \
  --output results/ \
  --verbose

# Shows detailed operation logs with timestamps
```

## Features

### All Scripts Include:
- **Argument Parsing**: Full CLI support with `--help`
- **Error Handling**: Graceful failures with descriptive error messages
- **Logging**: Timestamp-prefixed progress indicators
- **Validation**: Input and output validation
- **Documentation**: Built-in usage examples

### Advanced Features:
- **Batch Processing**: Process multiple datasets sequentially
- **Flexible Input/Output**: Specify custom paths via CLI arguments
- **Interactive Mode**: Confirm execution before each phase
- **Metadata Tracking**: JSON metadata for all analysis outputs
- **Resume Capability**: Re-run individual phases if needed

## Common Issues & Solutions

### Issue: "file not found" error
**Solution**: Ensure file paths are correct and files exist
```bash
# Test with ls or dir first
ls UPL25_matches2.csv  # On Linux/Mac
dir UPL25_matches2.csv # On Windows

# Use absolute paths if relative paths fail
python scripts/process_league_data.py \
  --league upl \
  --input "/full/path/to/UPL25_matches2.csv" \
  --output "/full/path/to/cleaned.csv"
```

### Issue: Module import errors
**Solution**: Scripts handle path management automatically, but ensure you're in the project root
```bash
cd /path/to/Match-Analysis
python scripts/process_league_data.py --help
```

### Issue: "League not found" error
**Solution**: Only 'upl' and 'fwsl' are supported
```bash
python scripts/generate_analysis.py --league upl --input data.csv -o out/
#                                           ↑
#                                    Only 'upl' or 'fwsl'
```

### Issue: Verbose logging isn't showing
**Solution**: Use `-v` flag (must be uppercase V variant works too)
```bash
python scripts/process_league_data.py \
  --league upl \
  --input raw.csv \
  --output clean.csv \
  --verbose  # or -v

# or

python scripts/run_full_analysis.py \
  --league upl \
  --input raw.csv \
  -o results/ \
  -v
```

## Performance & Resource Requirements

| Operation | Typical Time | Memory | CPU |
|-----------|-------------|--------|-----|
| Data Cleaning | 5-15 seconds | 50-100 MB | Low |
| Analysis (13 functions) | 10-30 seconds | 100-200 MB | Medium |
| Report Generation (20 clubs) | 5-20 seconds | 50-100 MB | Low |
| **Complete Pipeline** | **20-60 seconds** | **150-300 MB** | **Low-Medium** |

## Integration Examples

### Python Script Integration
```python
import subprocess
import json

# Run pipeline
result = subprocess.run([
    'python', 'scripts/run_full_analysis.py',
    '--league', 'upl',
    '--input', 'raw.csv',
    '--output', 'results/'
], capture_output=True, text=True)

if result.returncode == 0:
    print("Pipeline completed successfully")
    with open('results/02_analysis/analysis_metadata.json') as f:
        metadata = json.load(f)
        print(f"Analysis included {metadata.get('total_analyses')} analyses")
else:
    print(f"Error: {result.stderr}")
```

### Shell Script Integration
```bash
#!/bin/bash

for league in upl fwsl; do
    echo "Processing $league..."
    python scripts/run_full_analysis.py \
        --league $league \
        --input "${league}_matches.csv" \
        --output "${league}_results/" \
        -v
    
    if [ $? -eq 0 ]; then
        echo "✓ $league completed"
    else
        echo "✗ $league failed"
    fi
done
```

### Scheduled Execution (Cron)
```bash
# Daily analysis at 2 AM
0 2 * * * cd /path/to/Match-Analysis && python scripts/run_full_analysis.py --league upl --input data.csv -o results/ >> logs/analysis.log 2>&1
```

## Testing Scripts

Each script supports `--help` for usage information:
```bash
python scripts/process_league_data.py --help
python scripts/generate_analysis.py --help
python scripts/generate_reports.py --help
python scripts/run_full_analysis.py --help
```

## Requirements

- Python 3.8+
- pandas
- python-docx
- All dependencies in `requirements.txt`

Install dependencies:
```bash
pip install -r requirements.txt
```

## Migration from Notebooks

If migrating from the Jupyter notebook workflow:

1. **Replace cleaning notebooks**:
   - Use `scripts/process_league_data.py` instead of `cleaning_FWSL_2025.ipynb` and `cleaning_UPL_2025.ipynb`

2. **Replace analysis notebooks**:
   - Use `scripts/generate_analysis.py` instead of `analysis_FWSL_2025.ipynb` and `analysis_UPL_2025.ipynb`

3. **Replace report notebooks**:
   - Use `scripts/generate_reports.py` instead of `individual_club_reports.ipynb`

4. **For complete pipeline**:
   - Use `scripts/run_full_analysis.py` as single replacement for all three notebooks

## Support & Documentation

- See [PHASE_1_IMPLEMENTATION_SUMMARY.md](../PHASE_1_IMPLEMENTATION_SUMMARY.md) for detailed documentation
- Each script includes built-in help: `python scripts/SCRIPT.py --help`
- Check script source code for detailed documentation strings

## Version History

**Phase 1 Release** (Jan 2, 2026)
- Created 4 production scripts
- Implemented comprehensive logging
- Added error handling and validation
- Included interactive mode
- Full CLI argument support

**Next: Phase 2** (Planned)
- Configuration system (YAML)
- Advanced CLI tool with menus
- Batch processing
- Additional export formats
- Notebook deprecation guide
