# Notebooks Archive

**Status**: ⚠️ ARCHIVED - Use Python scripts instead

---

## Overview

This directory contains the original Jupyter notebooks used during project development. These notebooks have been **successfully migrated** to production Python CLI scripts.

### ⚠️ Important Notes

✋ **Do not use these notebooks for production analysis**

**Instead use**:
- `scripts/process_league_data.py` - for data cleaning
- `scripts/generate_analysis.py` - for statistical analysis
- `scripts/generate_reports.py` - for report generation
- `scripts/run_full_analysis.py` - for complete pipeline

---

## Archive Contents

### Cleaning Notebooks
- `cleaning_FWSL_2025.ipynb` - FWSL data cleaning (Archived)
- `cleaning_UPL_2025.ipynb` - UPL data cleaning (Archived)
  
**Replaced by**: `scripts/process_league_data.py`

### Analysis Notebooks
- `analysis_FWSL_2025.ipynb` - FWSL statistical analysis (Archived)
- `analysis_UPL_2025.ipynb` - UPL statistical analysis (Archived)

**Replaced by**: `scripts/generate_analysis.py`

### Reporting Notebooks
- `individual_club_reports.ipynb` - Per-club DOCX reports (Archived)

**Replaced by**: `scripts/generate_reports.py`

### Other Notebooks
- Other exploration/demo notebooks may be present for reference

---

## When to Reference Archived Notebooks

✅ **Appropriate uses**:
1. Understanding the original logic and methodology
2. Reviewing historical analysis approaches
3. Cell-by-cell debugging during development
4. Exploring data interactively (for EDA only)

❌ **Not appropriate for**:
1. Production analysis workflows
2. Scheduled batch processing
3. Integration with automation/CI-CD
4. Current data analysis

---

## Migration Path

If you're migrating analysis from a notebook:

### Step 1: Identify Equivalent Script
Find the script that replaces your notebook:

| Notebook | Script |
|----------|--------|
| `cleaning_*.ipynb` | `scripts/process_league_data.py` |
| `analysis_*.ipynb` | `scripts/generate_analysis.py` |
| `individual_club_reports.ipynb` | `scripts/generate_reports.py` |

### Step 2: Extract Custom Logic
If you added custom logic to a notebook:

```python
# In notebook: Extract your analysis function
def my_custom_analysis(df):
    # Your logic here
    return result
```

### Step 3: Apply to Script
1. Copy the function to the appropriate script
2. Update `analysis_config.yaml` if parameterization needed
3. Integrate with script's main function
4. Test with `scripts/validate_data.py`

### Step 4: Use the Script

```bash
# Instead of opening notebook and running cells
python scripts/process_league_data.py --league upl --input data.csv -o output.csv
```

---

## Archive Maintenance

### What Changed
- Scripts replaced notebooks for production use
- Configuration moved to YAML files
- Error handling made robust
- Logging added throughout
- Multiple export formats supported

### What Stayed the Same
- Core analysis logic is identical
- Data transformations unchanged
- Results are equivalent
- Configuration parameters same

### If You Find a Bug

If notebook and script give different results:

1. **Check the data**: Run `scripts/validate_data.py`
2. **Compare parameters**: Check `scripts/config/analysis_config.yaml`
3. **Debug**: Use script with `-v` (verbose) flag
4. **Report**: Create issue with specific findings

---

## Usage Examples

### For Reference Only
```python
# Open notebook to understand logic
import nbformat
with open('cleaning_FWSL_2025.ipynb') as f:
    nb = nbformat.read(f, as_version=4)
    # Review cells for documentation
```

### For Interactive Exploration
```bash
# If you need to explore data interactively
jupyter notebook

# But for production: use scripts instead
python scripts/run_full_analysis.py --league upl --input data.csv -o results/
```

---

## Migration Status

| Notebook | Status | Replacement |
|----------|--------|-------------|
| cleaning_FWSL_2025.ipynb | ✅ Archived | scripts/process_league_data.py |
| cleaning_UPL_2025.ipynb | ✅ Archived | scripts/process_league_data.py |
| analysis_FWSL_2025.ipynb | ✅ Archived | scripts/generate_analysis.py |
| analysis_UPL_2025.ipynb | ✅ Archived | scripts/generate_analysis.py |
| individual_club_reports.ipynb | ✅ Archived | scripts/generate_reports.py |

**All production analysis should use scripts** ✅

---

## Resources

### Script Documentation
- User guide: [../scripts/README.md](../scripts/README.md)
- Migration guide: [../MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md)
- Quick reference: [../PHASE_1_QUICK_REFERENCE.md](../PHASE_1_QUICK_REFERENCE.md)

### Getting Help
```bash
# View help for any script
python scripts/run_full_analysis.py --help

# Launch interactive CLI
python scripts/analysis_cli.py

# Validate data
python scripts/validate_data.py --input your_data.csv
```

---

## Deprecation Notice

⚠️ **These notebooks are no longer maintained**

- No updates for new features
- No bug fixes applied
- No support provided
- **Use Python scripts instead**

Future analysis should use:
- `scripts/` for analysis workflows
- `scripts/analysis_cli.py` for interactive use
- `scripts/config/analysis_config.yaml` for parameters

---

## Archive Contents Preservation

This archive is kept for:
1. Historical reference
2. Understanding project evolution
3. Validation of logic migration
4. Educational purposes

**But not for production use.**

---

**Last Updated**: January 2, 2026  
**Status**: ✅ Migration Complete  
**Recommendation**: Use Python scripts for all analysis
