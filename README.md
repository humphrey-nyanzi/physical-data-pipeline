# Match-Analysis: Uganda Football Data Analytics Platform

A comprehensive data analysis and reporting platform for Catapult match data from Uganda's football leagues (FWSL and UPL). This tool automates the cleaning, analysis, and reporting of player performance metrics to generate insightful club-specific analysis reports.

## 🎯 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Jupyter Notebook or VS Code with Jupyter extension

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/fufa-rst/Match-Analysis.git
   cd Match-Analysis
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Running the Pipeline

**Option 1: Interactive Notebook (Recommended for new users)**
```bash
jupyter notebook main_pipeline.ipynb
```
This opens an interactive notebook where you can:
- Select league (FWSL or UPL)
- Run analysis step-by-step
- View outputs and visualizations immediately

**Option 2: Python Script**
```bash
python scripts/run_pipeline.py
```

---

## 📊 Project Overview

### What This Project Does

Match-Analysis processes raw Catapult sports tracking data and transforms it into:

1. **Cleaned Datasets** - Standardized, validated data ready for analysis
2. **Performance Metrics** - Derived metrics like distance per minute, high-speed running efficiency, etc.
3. **Statistical Summaries** - Team and player-level performance statistics
4. **Professional Reports** - Word documents with visualizations and insights for each club

### Supported Leagues

| League | Full Name | Teams | Season |
|--------|-----------|-------|--------|
| **FWSL** | Uganda Women's Football Super League | 12 | 2024-2025 |
| **UPL** | Uganda Premier League (Men) | 16 | 2024-2025 |

---

## 📁 Project Structure

### Key Directories

```
Match-Analysis/
│
├── src/                          # Core application code
│   ├── config/                   # Configuration & definitions
│   │   ├── constants.py          # Global settings & thresholds
│   │   ├── league_definitions.py # Team names, positions per league
│   │   └── metrics.py            # Metric definitions & categories
│   │
│   ├── data/                     # Data processing
│   │   ├── cleaning.py           # Main cleaning pipeline
│   │   ├── schemas.py            # Column definitions & validation rules
│   │   └── validators.py         # Data quality checks
│   │
│   ├── analysis/                 # Analysis & computation
│   │   ├── analysis.py           # Metric computation & aggregation
│   │   └── visualizations.py     # Chart generation
│   │
│   ├── reporting/                # Report generation
│   │   ├── report_builder.py     # Aggregate metrics, build sections
│   │   ├── document_generator.py # Create Word documents
│   │   └── formatters.py         # Styling & formatting
│   │
│   └── utils/                    # Utility functions
│       ├── text_cleaning.py      # Name normalization, fuzzy matching
│       ├── styling.py            # Word document styling
│       └── normalization.py      # Club/position mapping
│
├── notebooks/                    # Interactive analysis workflows
│   ├── main_pipeline.ipynb       # Entry point (league selection)
│   ├── 01_clean_data.ipynb       # Data cleaning workflow
│   ├── 02_analyze_league.ipynb   # Analysis & statistics
│   └── 03_generate_reports.ipynb # Report generation
│
├── data/                         # Data storage
│   ├── raw/                      # Raw Catapult CSV exports (read-only)
│   │   └── all_catapult_data_16_Jul_25.csv
│   ├── processed/                # Cleaned & processed data
│   │   ├── FWSL25_matches_clean.csv
│   │   └── UPL25_matches_clean.csv
│   └── external/                 # Reference data, notes
│
├── reports/                      # Generated analysis reports
│   ├── FWSL/                     # Women's league club reports
│   ├── UPL/                      # Men's league club reports
│   └── README.md                 # Report guide
│
├── scripts/                      # Standalone utility scripts
│   ├── run_pipeline.py           # Full pipeline automation
│   ├── validate_data.py          # Data quality checks
│   └── generate_reports.py       # Batch report generation
│
├── tests/                        # Automated tests
│   ├── conftest.py               # Pytest fixtures & configuration
│   ├── test_cleaning.py          # Data cleaning tests
│   ├── test_analysis.py          # Analysis function tests
│   └── fixtures/                 # Test data
│
├── experiments/                  # Exploratory & experimental code
│   ├── ash_workflow.ipynb        # Workflow exploration
│   ├── create_infographic.ipynb  # Visual experiments
│   └── Uganda_data.R             # R-based analysis
│
├── logs/                         # Pipeline execution logs
├── outputs/                      # Generated outputs (charts, etc.)
├── docs/                         # Additional documentation
│
└── Configuration Files
    ├── requirements.txt          # Python dependencies
    ├── .gitignore               # Git exclusions
    ├── .env.example             # Environment template
    └── README.md                # This file
```

---

## 🔄 Data Pipeline

### Workflow Overview

```
Raw Data (CSVs)
       ↓
[1. CLEANING] → Standardize columns, filter matches, normalize names
       ↓
Processed Data (CSVs)
       ↓
[2. ANALYSIS] → Compute metrics, aggregate by player/club, calculate stats
       ↓
Metrics & Statistics
       ↓
[3. REPORTING] → Generate Word documents with tables, charts, insights
       ↓
Club Reports (DOCX)
```

### Step 1: Data Cleaning

**Input:** Raw Catapult CSV exports  
**Output:** Cleaned, validated CSVs

```python
from src.data.cleaning import clean_matches

# Clean FWSL data
df = clean_matches(league='fwsl')
df.to_csv('data/processed/FWSL25_matches_clean.csv', index=False)
```

**What happens:**
- Column standardization (lowercase, trim whitespace)
- Filter to match sessions only (exclude practice)
- Club name normalization (fuzzy matching to standard names)
- Position categorization (GK → Goalkeeper, DEF → Defender, etc.)
- Data validation (check missing data, detect outliers)
- Derived metrics (per-minute distance, efficiency scores)

### Step 2: Analysis

**Input:** Cleaned CSVs  
**Output:** Performance metrics and statistics

```python
from src.analysis.analysis import load_processed_data, compute_match_metrics

df = load_processed_data('fwsl')
metrics = compute_match_metrics(df)
summary = compute_summary_statistics(df, by_position=True)
```

**Key Metrics:**
- **Volume:** Total distance, sprints, accelerations
- **Intensity:** Player load, max speed, top acceleration
- **Efficiency:** Distance per minute, actions per minute

### Step 3: Reporting

**Input:** Aggregated metrics  
**Output:** Professional Word documents

```python
from src.reporting.document_generator import create_club_report

create_club_report(
    club='Amus College WFC',
    league='fwsl',
    output_path='reports/FWSL/Amus_College_WFC_report.docx'
)
```

**Report Contents:**
- Team summary & key statistics
- Player profiles & rankings
- Performance charts & visualizations
- Trends over the season
- Benchmarking against league averages

---

## 📈 Data Schema

### Processed Data Columns

| Column | Type | Description |
|--------|------|-------------|
| **match_date** | datetime | Date of the match |
| **club** | string | Club/team name (normalized) |
| **league** | string | 'FWSL' or 'UPL' |
| **player_name** | string | Player name |
| **position** | string | Raw position (e.g., "CB", "CAM") |
| **position_category** | string | Standardized category (GK/DEF/MID/FWD) |
| **minutes_played** | float | Minutes in match |
| **total_distance_km** | float | Total distance covered (km) |
| **high_speed_distance_km** | float | Distance at >6 m/s (km) |
| **sprint_distance_km** | float | Distance at >7 m/s (km) |
| **total_accel_events** | int | Acceleration events |
| **total_decel_events** | int | Deceleration events |
| **avg_velocity_ms** | float | Average velocity (m/s) |
| **max_velocity_ms** | float | Peak velocity (m/s) |
| **player_load** | float | Intensity score |
| **per_minute_distance** | float | Distance per minute (km/min) |

See [data/processed/README.md](data/processed/README.md) for full schema.

---

## 🛠️ Key Modules

### `src.config.constants`
Global configuration, thresholds, and settings.

```python
from src.config import constants

# Validation thresholds
MIN_SESSION_DURATION_MINUTES = 60
OUTLIER_IQR_MULTIPLIER = 1.5
SPARSE_COLUMN_THRESHOLD = 0.95

# File paths
RAW_DATA_FILE = './data/raw/all_catapult_data_16_Jul_25.csv'
FWSL_PROCESSED_OUTPUT = 'FWSL25_matches_clean.csv'
```

### `src.data.cleaning`
Main data cleaning functions.

```python
from src.data.cleaning import (
    load_raw_data,
    standardize_columns,
    filter_match_sessions,
    clean_matches
)

# Quick start
df = clean_matches(league='fwsl')
```

### `src.analysis.analysis`
Metric computation and aggregation.

```python
from src.analysis.analysis import (
    load_processed_data,
    compute_match_metrics,
    compute_summary_statistics,
    aggregate_by_position
)

df = load_processed_data('upl')
team_stats = compute_summary_statistics(df, by_position=True)
```

### `src.reporting.document_generator`
Generate Word documents.

```python
from src.reporting.document_generator import create_club_report

create_club_report(
    club='BUL FC',
    league='upl',
    output_path='reports/UPL/BUL_FC_report.docx'
)
```

---

## 📚 League Information

### FWSL (Uganda Women's Football Super League)

**Teams (12):**
- Amus College WFC
- Kawempe Muslim LFC
- Kampala Queens FC
- Lady Doves FC
- Makerere University WFC
- Olila HS WFC
- Rines SS WFC
- She Corporates FC
- She Maroons FC
- Uganda Martyrs Lubaga WFC
- Wakiso Hill WFC
- (More teams may be added)

**Season:** 2024-2025

### UPL (Uganda Premier League)

**Teams (16):**
- BUL FC
- KCCA FC
- SC Villa
- Vipers SC
- Express FC
- Kitara FC
- Lugazi FC
- Maroons FC
- Mbale Heroes FC
- Mbarara City FC
- NEC FC
- Police FC
- Soltilo Bright Stars FC
- UPDF FC
- URA FC
- Wakiso Giants FC

**Season:** 2024-2025

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_cleaning.py

# Run with coverage
pytest --cov=src tests/
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_cleaning.py         # Data cleaning tests
├── test_analysis.py         # Analysis function tests
├── test_metrics.py          # Metric computation tests
├── test_validators.py       # Validation function tests
└── fixtures/
    ├── sample_raw_data.csv
    └── sample_cleaned_data.csv
```

### Example Test

```python
def test_clean_matches_fwsl(sample_raw_data):
    """Test FWSL data cleaning."""
    result = clean_matches('fwsl', test_data=sample_raw_data)
    
    assert 'club' in result.columns
    assert 'league' in result.columns
    assert all(result['league'] == 'FWSL')
```

---

## 🔧 Common Tasks

### Task 1: Add a New Team

1. Update [src/config/league_definitions.py](src/config/league_definitions.py)
2. Add club name to appropriate league dictionary
3. Update [src/config/constants.py](src/config/constants.py) if special name mappings needed
4. Rerun cleaning and reporting

### Task 2: Add a New Metric

1. Define in [src/config/metrics.py](src/config/metrics.py)
2. Implement computation in [src/analysis/analysis.py](src/analysis/analysis.py)
3. Add to report templates in [src/reporting/](src/reporting/)
4. Add tests in [tests/test_metrics.py](tests/test_metrics.py)

### Task 3: Update Raw Data

1. Place new CSV in `data/raw/`
2. Update `RAW_DATA_FILE` in [src/config/constants.py](src/config/constants.py) if filename changed
3. Run cleaning: `notebooks/01_clean_data.ipynb`
4. Run analysis: `notebooks/02_analyze_league.ipynb`
5. Generate reports: `notebooks/03_generate_reports.ipynb`

### Task 4: Generate Reports for a Single Club

```python
from src.reporting.document_generator import create_club_report

create_club_report(
    club='KCCA FC',
    league='upl',
    output_path='reports/UPL/KCCA_FC_report.docx'
)
```

---

## 📊 Output Examples

### Generated Reports

**Location:** `reports/FWSL/` and `reports/UPL/`

Each report includes:
- **Executive Summary** - Season overview, key statistics
- **Player Profiles** - Individual performance tables
- **Performance Metrics** - Distance, sprints, accelerations
- **Visualizations** - Charts and trend lines
- **Benchmarking** - Comparison to league averages

### Data Outputs

**Location:** `data/processed/`

- `FWSL25_matches_clean.csv` - All FWSL matches and player performances
- `UPL25_matches_clean.csv` - All UPL matches and player performances

### Logs

**Location:** `logs/`

Pipeline execution logs for debugging and monitoring.

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# Logging
LOG_LEVEL=INFO

# Paths
DATA_DIR=./data/
RAW_DATA_DIR=./data/raw/
PROCESSED_DATA_DIR=./data/processed/
OUTPUT_DIR=./outputs/
REPORT_DIR=./reports/

# Thresholds
MIN_SESSION_DURATION_MINUTES=60
OUTLIER_IQR_MULTIPLIER=1.5
```

### Constants

Edit [src/config/constants.py](src/config/constants.py) for:
- Minimum session duration
- Outlier detection thresholds
- Column name mappings
- Club name corrections
- Report styling

---

## 🚀 Advanced Usage

### Custom Analysis

```python
import pandas as pd
from src.data.cleaning import clean_matches
from src.analysis.analysis import compute_summary_statistics

# Load cleaned data
df = clean_matches(league='fwsl')

# Filter to specific team
team_data = df[df['club'] == 'Amus College WFC']

# Compute custom statistics
stats = team_data.groupby('position_category').agg({
    'total_distance_km': 'mean',
    'player_load': 'max',
    'minutes_played': 'sum'
})

print(stats)
```

### Batch Processing

```python
from src.reporting.document_generator import create_club_report
from src.config.league_definitions import get_league_clubs

# Generate reports for all FWSL teams
for club in get_league_clubs('fwsl'):
    create_club_report(
        club=club,
        league='fwsl',
        output_path=f'reports/FWSL/{club}_report.docx'
    )
```

### Data Export

```python
import pandas as pd
from src.data.cleaning import clean_matches

df = clean_matches(league='upl')

# Export to Excel
df.to_excel('outputs/UPL_analysis.xlsx', index=False)

# Export to JSON
df.to_json('outputs/UPL_analysis.json', orient='records')

# Export filtered data
forwards = df[df['position_category'] == 'FWD']
forwards.to_csv('outputs/forwards_analysis.csv', index=False)
```

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors

**Solution:** Ensure Python path includes project root
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

Or in Python:
```python
import sys
sys.path.insert(0, '/path/to/Match-Analysis')
```

### Issue: Raw data file not found

**Solution:** Check file path in [src/config/constants.py](src/config/constants.py)
```python
RAW_DATA_FILE = "./data/raw/all_catapult_data_16_Jul_25.csv"
```

### Issue: Club names not matching

**Solution:** Add mapping to `CLUB_CORRECTIONS_*` in [src/config/constants.py](src/config/constants.py)
```python
CLUB_CORRECTIONS_FWSL = {
    "Typo Name": "Correct Name",
}
```

### Issue: Slow data processing

**Solution:** Check data size, filter by league/date before analysis
```python
df = clean_matches(league='fwsl')  # Process one league at a time
df_recent = df[df['match_date'] >= '2025-01-01']  # Filter by date
```

---

## 📖 Documentation Structure

- **[README.md](README.md)** - This file (project overview)
- **[data/raw/README.md](data/raw/README.md)** - Raw data source info
- **[data/processed/README.md](data/processed/README.md)** - Processed data schema
- **[reports/README.md](reports/README.md)** - Report format & contents
- **[notebooks/README.md](notebooks/README.md)** - Notebook workflow guide
- **[experiments/README.md](experiments/README.md)** - Experimental code notes
- **[src/config/constants.py](src/config/constants.py)** - Inline configuration docs

---

## 🤝 Contributing

### Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and write tests
3. Run tests: `pytest`
4. Commit: `git commit -m "Add my feature"`
5. Push: `git push origin feature/my-feature`
6. Create Pull Request

### Code Style

- Follow PEP 8
- Use type hints where possible
- Document functions with docstrings
- Write tests for new features

### Adding New Features

1. Add function to appropriate `src/` module
2. Add tests in `tests/`
3. Update documentation
4. Update notebooks if user-facing

---

## 📝 License & Attribution

**Data Source:** Catapult Sports tracking data  
**Leagues:** FWSL (Uganda Women's Football Super League), UPL (Uganda Premier League)  
**Organization:** FUFA-RST (Federation of Uganda Football Associations - Research & Statistics Team)

---

## 📧 Contact & Support

For questions, issues, or suggestions:

- **Repository:** https://github.com/fufa-rst/Match-Analysis
- **Issues:** GitHub Issues tracker
- **Documentation:** See `/docs` folder

---

## 🗺️ Project Roadmap

- [ ] Interactive web dashboard for data exploration
- [ ] Real-time data ingestion from Catapult API
- [ ] Player benchmarking across leagues
- [ ] Injury risk prediction models
- [ ] Tactical analysis (positioning, heat maps)
- [ ] Export to additional formats (PDF, HTML)

---

## 📚 Additional Resources

- **Catapult Documentation:** [Catapult Sports](https://www.catapultsports.com/)
- **Pandas Guide:** [pandas.pydata.org](https://pandas.pydata.org/)
- **Python-docx Guide:** [python-docx.readthedocs.io](https://python-docx.readthedocs.io/)
- **Jupyter Notebooks:** [jupyter.org](https://jupyter.org/)

---

**Last Updated:** January 2, 2026  
**Version:** 1.0
