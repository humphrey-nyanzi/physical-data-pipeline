# Match-Analysis Coding Guidelines

## Project Overview

Match-Analysis is a Python data pipeline for processing Catapult GPS/IMU tracking data from Uganda's FUFA football leagues (FWSL/UPL). It transforms raw CSV exports into cleaned datasets, statistical analyses, and professional Word reports.

## Architecture

The pipeline follows a **4-phase modular architecture** with multiple pipeline implementations:

```
Phase 1: Configuration (src/config/) → Phase 2: Cleaning (src/data/) → Phase 3: Analysis (src/analysis/) → Phase 4: Reporting (src/reporting/)
```

### Core Modules

- **`src/config/`**: Centralized constants, thresholds, league definitions, and metric configurations
- **`src/data/`**: Data loading, cleaning pipeline, validation, and schema definitions
- **`src/analysis/`**: Statistical computations, aggregations, positional/club/player-level analysis
- **`src/reporting/`**: Word document generation via `python-docx`, styled tables, embedded charts
- **`src/utils/`**: Fuzzy text matching, name normalization, document styling utilities

### Pipeline Implementations (Active)

- **`src/pipelines/base.py`**: Abstract `AnalysisPipeline` base class for all pipelines
- **`src/pipelines/full.py`**: `FullPipeline` - Complete 4-phase workflow
- **`src/pipelines/season.py`**: `SeasonPipeline` - Season-wide analysis with league reports
- **`src/pipelines/weekly.py`**: `WeeklyPipeline` - Weekly matchday GPS reports

### Legacy Code (Deprecated - DO NOT USE)

- **`src/pipeline/orchestrator.py`**: Old monolithic `PipelineExecutor` class
  - ⚠️ **Status**: Deprecated. Use `scripts/match_analysis.py full` instead
  - Scheduled for removal after deprecation period

### Recommended Usage

Use the unified CLI (`scripts/match_analysis.py`) to access all pipelines:

```bash
python scripts/match_analysis.py full --league upl --input data.csv
python scripts/match_analysis.py season --league upl --input data.csv
python scripts/match_analysis.py weekly --md 11
```

## Jupyter Notebook Workflow

For interactive analysis, use notebooks in order:

| Step  | Notebook                    | Purpose                                             |
| ----- | --------------------------- | --------------------------------------------------- |
| Entry | `main_pipeline.ipynb`       | League selection (FWSL/UPL), orchestrates workflow  |
| 1     | `01_clean_data.ipynb`       | Load raw data, clean, validate, save processed CSVs |
| 2     | `02_analyze_league.ipynb`   | Compute metrics, generate visualizations            |
| 3     | `03_generate_reports.ipynb` | Create club-specific Word documents                 |

```bash
# Running notebooks
jupyter notebook notebooks/main_pipeline.ipynb
# Or use VS Code with Jupyter extension
```

**Note:** Old notebooks in `notebook_archive/` are deprecated—do not use for active analysis.

## Key Conventions

### Module Imports

Always use relative imports within `src/`:

```python
from ..config import constants, league_definitions
from ..utils import text_cleaning
```

### League Parameterization

Functions accept `league` parameter ('fwsl' or 'upl') to switch behavior dynamically:

```python
df = clean_pipeline(league='fwsl')
config = league_definitions.get_league_config('upl')
clubs = league_definitions.get_league_clubs('fwsl')
```

### Configuration Over Hardcoding

All thresholds, file paths, metrics, and club mappings live in `src/config/constants.py` and `src/config/league_definitions.py`. Never hardcode values—add them to these modules.

### Metric Categories

Metrics are categorized as **volume** (cumulative) or **intensity** (peaks):

- **Volume**: `distance_km`, `sprint_distance_m`, `total_accelerations`, `total_decelerations`
- **Intensity**: `player_load`, `top_speed_kmh`, `max_acceleration_mss`, `power_score_wkg`

Use `constants.VOLUME_METRICS` and `constants.INTENSITY_METRICS` for programmatic access.

## Data Schema

### Raw Catapult Data Format

**Source file pattern:** `all_catapult_data_<date>.csv` in `data/raw/`

Key raw columns from Catapult export:
| Column | Type | Description |
|--------|------|-------------|
| `session_title` | str | Match identifier (e.g., "Wmd1 Club A vs Club B") |
| `player_name` | str | Format: "Name - Club - Position" |
| `duration` | float | Session duration in minutes |
| `distance_km` | float | Total distance covered |
| `player_load` | float | Catapult intensity metric |
| `accelerations_zone_count:_*` | int | Acceleration counts by zone |

Session title patterns by league:

- **FWSL**: `Wmd<N>` (e.g., "Wmd1", "Wmd22")
- **UPL**: `Md<N>` (e.g., "Md1", "Md30")

### Processed Data Schema

Output files: `FWSL25_matches_clean.csv`, `UPL25_matches_clean.csv` in `data/processed/`

| Column                | Type     | Description                                                     |
| --------------------- | -------- | --------------------------------------------------------------- |
| `match_date`          | datetime | Date of the match                                               |
| `club_for`            | str      | Club name (normalized)                                          |
| `club_against`        | str      | Opponent club name                                              |
| `league`              | str      | League code (FWSL or UPL)                                       |
| `match_day`           | str      | Normalized match day (MD1, MD2, ...)                            |
| `p_name`              | str      | Player name (extracted)                                         |
| `player_club_`        | str      | Player's club affiliation                                       |
| `player_position`     | str      | Raw position code (CB, CM, FW, etc.)                            |
| `general_position`    | str      | Normalized position (goalkeeper, defender, midfielder, forward) |
| `duration`            | float    | Minutes played                                                  |
| `distance_km`         | float    | Total distance (km)                                             |
| `sprint_distance_m`   | float    | Sprint distance (m)                                             |
| `player_load`         | float    | Catapult player load                                            |
| `top_speed_kmh`       | float    | Maximum speed (km/h)                                            |
| `total_accelerations` | int      | Sum of all acceleration zones                                   |
| `total_decelerations` | int      | Sum of all deceleration zones                                   |
| `acc_counts_per_min`  | float    | Accelerations per minute (derived)                              |
| `dec_counts_per_min`  | float    | Decelerations per minute (derived)                              |

## Report Generation

Reports use `python-docx` for Word document creation.

### Report Structure

Each club report contains standardized sections:

1. Introduction (FUFA mission, Catapult investment)
2. Methodology (data collection, cleaning)
3. Key Concepts (metric definitions)
4. Season Results (matchday stats, player usage)
5. Club Metric Results (summary statistics)
6. Top Players by Metric
7. Positional Analysis
8. Club vs Season Comparison
9. Challenges & Future Plans
10. Conclusion

### Adding a New Report Section

1. Create aggregation function in `src/reporting/report_builder.py`:

```python
def get_new_analysis(club_df: pd.DataFrame, ...) -> pd.DataFrame:
    """Compute new analysis for report section."""
    # Aggregate data
    return result_df
```

2. Add document section in `src/reporting/document_generation.py`:

```python
def add_new_section(doc: Document, data: pd.DataFrame):
    """Add new analysis section to report."""
    doc.add_heading("New Section Title", level=1)
    add_dataframe_as_table(doc, data)
```

3. Export in `src/reporting/__init__.py`

4. Call in `src/pipelines/full.py` `_phase_4_reporting()` method (or `src/pipelines/season.py` for season-specific logic)

### Key Reporting Functions

| Function                                   | Purpose                             |
| ------------------------------------------ | ----------------------------------- |
| `create_report_document(club_name)`        | Create new doc with title page      |
| `add_dataframe_as_table(doc, df)`          | Insert DataFrame as formatted table |
| `embed_matplotlib_figure(doc, fig)`        | Embed chart as image                |
| `save_document(doc, output_dir, filename)` | Save and return path                |

### Document Styling

Styling utilities in `src/utils/styling.py` provide consistent formatting. Use existing functions rather than inline styling.

## Testing

Run tests with pytest from project root:

```bash
pytest                           # Run all tests
pytest tests/test_cleaning.py    # Run specific test file
pytest --cov=src tests/          # With coverage report
pytest -v                        # Verbose output
```

### Test Patterns

- Use fixtures from `tests/conftest.py`:
  - `sample_raw_data` - Mock raw Catapult data
  - `sample_cleaned_data` - Mock processed data
  - `temp_data_dir` - Temporary directory structure
  - `sample_csv_files` - Writes sample CSVs to temp dir

- Test individual functions, not full pipeline (requires large CSV):

```python
def test_normalize_clubs():
    df = pd.DataFrame({'club_for': ['Kampala Queens', 'Kcca Fc']})
    out = cleaning.normalize_clubs(df, 'fwsl')
    assert 'Kampala Queens FC' in out['club_for'].values

def test_compute_positional_stats():
    df = pd.DataFrame({
        'general_position': ['defender', 'forward'],
        'distance_km': [10.0, 12.0]
    })
    result = analysis.compute_positional_stats(df, 'distance_km')
    assert 'defender' in result.index
```

- Note in tests: `# Full pipeline test requires large raw CSV; avoid in CI`

## Common Development Tasks

### Adding a New Team

1. Add to `FWSL_CLUBS` or `UPL_CLUBS` in `src/config/league_definitions.py`
2. Add name corrections to `constants.CLUB_CORRECTIONS_FWSL` or `CLUB_CORRECTIONS_UPL`
3. Add uploaded matches count to `FWSL_UPLOADED_MATCHES` or `UPL_UPLOADED_MATCHES`

### Adding a New Metric

1. Define in `CORE_METRICS` or `COMPUTED_METRICS` in `src/config/constants.py`
2. Add display name to `METRIC_DISPLAY_NAMES`
3. Categorize in `VOLUME_METRICS` or `INTENSITY_METRICS`
4. Implement computation in `src/data/cleaning.py` (derived) or `src/analysis/analysis.py`
5. Add tests in `tests/test_analysis.py`

### Adding a Missing Player Position

For players without position in raw data, add to `UPL_MISSING_POSITIONS` or create similar for FWSL in `src/config/league_definitions.py`:

```python
UPL_MISSING_POSITIONS = {
    "Player Name": "CM",  # Manual position assignment
}
```

### Running the Pipeline

```bash
# Full pipeline via script
python scripts/run_pipeline.py -l upl -i ./data/raw/all_catapult_data.csv -o ./output

# Options
#   -l/--league: 'fwsl' or 'upl' (required)
#   -i/--input: Path to raw CSV (required)
#   -o/--output: Output directory (default: ./output)
#   -v/--verbose: Enable verbose logging
```

### Updating Raw Data

1. Place new CSV in `data/raw/`
2. Update `RAW_DATA_FILE` path in `src/config/constants.py` if filename changed
3. Run cleaning → analysis → reporting pipeline

## Code Style

- Follow PEP 8
- Use type hints for function signatures
- Docstrings use Google format with Args/Returns sections
- Functions in analysis modules return pandas DataFrames
- Error handling logs via `logging` module (see `src/pipelines/full.py` for patterns)
- Use `logger.info()` for progress, `logger.warning()` for non-fatal issues, `logger.error()` for failures

## Key Files Reference

| Purpose                  | Location                               |
| ------------------------ | -------------------------------------- |
| Constants & thresholds   | `src/config/constants.py`              |
| League/club definitions  | `src/config/league_definitions.py`     |
| Data schemas             | `src/data/schemas.py`                  |
| Cleaning pipeline        | `src/data/cleaning.py`                 |
| Analysis functions       | `src/analysis/analysis.py`             |
| Report data aggregation  | `src/reporting/report_builder.py`      |
| Document generation      | `src/reporting/document_generation.py` |
| Full pipeline (active)   | `src/pipelines/full.py`                |
| Season pipeline (active) | `src/pipelines/season.py`              |
| CLI entry point          | `scripts/match_analysis.py`            |
| Test fixtures            | `tests/conftest.py`                    |
