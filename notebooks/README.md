# Notebooks

This directory contains Jupyter notebooks for interactive analysis and reporting.

## Entry Point

**Start here:** `main_pipeline.ipynb`
- League selection (FWSL or UPL)
- Orchestrates entire analysis workflow
- Generates reports and visualizations

## Workflow Notebooks

1. **01_clean_data.ipynb**
   - Load raw data
   - Clean and validate
   - Save processed CSVs

2. **02_analyze_league.ipynb**
   - Load processed data
   - Compute metrics and statistics
   - Generate visualizations

3. **03_generate_reports.ipynb**
   - Create club-specific analysis reports
   - Generate Word documents
   - Export to reports/ directory

## Running the Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Open main_pipeline.ipynb in Jupyter
jupyter notebook main_pipeline.ipynb

# Or use VS Code
# Ctrl+Shift+D to open notebook
```

## Archive

Old versions are in `notebook_archive/` - do not use for active analysis.
