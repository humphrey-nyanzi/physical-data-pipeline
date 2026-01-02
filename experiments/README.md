# Experiments

This directory contains experimental and exploratory notebooks that are **not part of the main pipeline**.

⚠️ **Warning:** Code here is not guaranteed to work or follow best practices.

## Contents

- `ash_workflow.ipynb` - Exploratory workflow analysis
- `create_infographic.ipynb` - Visual infographic experiments
- `Uganda_data.R` - R-based exploratory analysis

## Usage

These are for research and exploration only. For production analysis, use notebooks in `notebooks/` directory.

If you find useful code here, migrate it to the main pipeline:
1. Create a proper function in `src/`
2. Add tests in `tests/`
3. Document in main notebooks
4. Remove from experiments
