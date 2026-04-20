# Match-Analysis: Football Performance Analytics Platform

A comprehensive data analysis and reporting platform for GPS tracking match data from professional football leagues (Women's League and Men's League). This tool automates the cleaning, analysis, and reporting of player performance metrics to generate insightful club-specific and league-wide analysis reports.

---

## 🎯 Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/Match-Analysis.git
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

---

## 🚀 Running the Pipelines

All pipelines are driven through a single unified CLI entry point:

```bash
python scripts/match_analysis.py <command> [options]
```

Available commands: `full`, `season`, `weekly`

### `full` — Complete 4-Phase Pipeline *(Recommended)*

Runs Config → Clean → Analyze → Report end-to-end for a given league.

```bash
python scripts/match_analysis.py full \
  --league upl \
  --input data/raw/raw_tracking_data.csv \
  --season 2024/25

# Options:
#   --timeframe [season|half_season]  (default: season)
#   --gk                              Include goalkeeper reports
#   --skip-club-reports               Skip individual club DOCX files
```

### `season` — Season / Half-Season Analysis

Focused season or half-season reporting with full club-level detail.

```bash
python scripts/match_analysis.py season \
  --league fwsl \
  --input data/raw/raw_tracking_data.csv \
  --season 2024/25 \
  --timeframe half_season

# Options:
#   --gk                  Generate additional goalkeeper reports
#   --skip-cleaning       Skip the data cleaning step (use pre-processed CSV)
#   --skip-club-reports   Skip individual club DOCX files
```

### `weekly` — Matchday GPS Report

Processes individual-matchday GPS CSV exports from `data/matchday_csvs/` and generates a single-matchday GPS report.

```bash
python scripts/match_analysis.py weekly \
  --md 12 \
  --league upl \
  --season 2025/2026

# Options:
#   --input   Directory of matchday CSVs (default: data/matchday_csvs/)
#   --gk      Generate an additional goalkeeper report
```

### View all options for any command

```bash
python scripts/match_analysis.py <command> --help
```

---

## 🔄 Pipeline Visualisation

> **How to read this section:**  Each tree shows the data flow for one pipeline — what goes **in**, every processing **step** and the **module responsible**, and exactly what **file** is produced and **where** it lands.  
> To improve a specific output, find it in the tree and follow the arrow back to the step / module that created it.

---

### Pipeline 1 — `full` *(Config → Clean → Analyze → Report)*

```
📥 INPUT
└── data/raw/<gps_export>.csv
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1 · Configuration                                        │
│  src/config/league_definitions.py                               │
│  • Load league clubs, session patterns, matchday limits         │
│  • Load half-season cutoff from scripts/config/analysis_config  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2 · Data Cleaning  (src/data/cleaning.py)                │
│                                                                 │
│  Step  1  load_raw_data()           — read raw CSV              │
│  Step  2  standardize_columns()     — lowercase, trim           │
│  Step  3  normalize_duration()      — seconds → minutes         │
│  Step  3½ extract_and_save_training_data()                      │
│  Step  4  filter_match_sessions()   — pattern-match MD# titles  │
│  Step  5  standardize_split_names() — '1st.half' → '1st Half'  │
│  Step  6  apply_text_cleaning()     — strip unicode/whitespace  │
│  Step  7  extract_session_info()    — parse matchday/teams/     │
│           (src/utils/text_parsing.py)   location/result        │
│  Step  8  validate_matchday_logic() — drop out-of-range MDs    │
│  Step  9  extract_player_columns()  — name, club, position      │
│  Step 10  normalize_clubs()         — fuzzy-match to official   │
│           (src/utils/text_cleaning.py)  club list              │
│  Step 11  filter_gk()              — exclude goalkeepers        │
│  Step 12  remove_duplicate_rows()                               │
│  Step 13  drop_sparse_columns()    — drop >95% zero cols        │
│  Step 14  aggregate_halves()       — merge H1+H2 per player     │
│  Step 15  filter_active_sessions() — min 60 min & 2 km         │
│  Step 16  remove_outliers()        — IQR × 1.5                 │
│  Step 17  compute_derived_metrics()— accel/dec rates, d/min    │
└────────────────────────┬────────────────────────────────────────┘
                         │
            ┌────────────┴───────────────┐
            ▼                            ▼
  📄 data/processed/                📄 Output/<Season>/<League>/Full/<Run_ID>/
     mens_league_matches_clean.csv       01_cleaned/
     womens_league_matches_clean.csv      └── {LEAGUE}_{Season}_Full_Cleaned_{run_id}.csv
     {LEAGUE}_training_data.csv        (reference copy for this run)
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3 · Analysis  (src/analysis/analysis.py)                 │
│                                                                 │
│  • compute_summary_stats()         — per-club mean/sum/std      │
│  • unique_players_per_club()                                    │
│  • players_per_club_per_matchday()                              │
│  • matchdays_per_club()                                         │
│  • top_players_by_matchdays()      — top-10 by appearances      │
│  • _compute_matchday_order()       — sort Md1…Md30 numerically  │
└────────────────────────┬────────────────────────────────────────┘
                         │  (results held in memory, no file output at this stage)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4a · Per-Club Reports  (src/reporting/)                  │
│  ClubReportBuilder → document_generation.py                     │
│                                                                 │
│  For every club in the league:                                  │
│  • Table of Contents                                            │
│  • Introduction / Methodology / Key Concepts                    │
│  • Match Day Usage table                                        │
│  • Player Usage table                                           │
│  • Club Metric Results (volume & intensity)                     │
│  • Top Players by Metric                                        │
│  • Average Metrics per Position                                 │
│  • Cumulative Position Metrics (volume)                         │
│  • Club vs Season Comparison                                    │
│  • Positional Comparison vs Season Averages                     │
│  • Physical Performance Trends chart (rolling average)          │
│  • Speed Zone Distribution chart                                │
│  • Challenges / Future Plans / Conclusion                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
  📄 Output/<Season>/<League>/Full/<Run_ID>/02_club_reports/
     └── {LEAGUE}_{Season}_Full_Club_{ClubName}_Report_{run_id}.docx
               (one file per club · e.g. ML_2024-25_Full_Club_Capital FC_Report_….docx)

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4b · League-Wide Report  (src/reporting/)                │
│  SeasonReportBuilder                                            │
│                                                                 │
│  • filter_data_by_timeframe()  — season or half-season slice    │
│  • Usage statistics & coverage grid                             │
│  • Performance stats (volume & intensity)                       │
│  • Max performers table                                         │
│  • Home/Away & Win/Draw/Loss contextual stats                   │
│  • Speed zone breakdown by position                             │
│  • Club comparison table                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
  📄 Output/<Season>/<League>/Full/<Run_ID>/03_league_report/
     └── {LEAGUE}_{Season}_League_{Timeframe}_Report_{run_id}.docx

┌─────────────────────────────────────────────────────────────────┐
│  METADATA & LOGGING  (src/pipelines/base.py)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
  📄 Output/<Season>/<League>/Full/<Run_ID>/run_metadata.json
  📄 logs/<Season>/<League>/{run_id}_full.log
  📄 logs/run_history.csv                 ← appended after every run
```

---

### Pipeline 2 — `season` *(Season / Half-Season Reports)*

Functionally equivalent to `full` but with more explicit stage control (e.g. `--skip-cleaning`).

```
📥 INPUT
└── data/raw/<gps_export>.csv   (or pre-processed CSV with --skip-cleaning)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1 · Data Cleaning  (same 17-step pipeline as `full`)     │
│  src/data/cleaning.py  →  clean_pipeline()                      │
│                                                                 │
│  ⚙️  --skip-cleaning flag: bypasses cleaning and loads the      │
│     input CSV directly (must be an already-processed file).      │
│     Still runs validate_matchday_logic() as a safety check.     │
└────────────────────────┬────────────────────────────────────────┘
                         │
            ┌────────────┴──────────────┐
            ▼                           ▼
  📄 data/processed/              📄 Output/<Season>/<League>/Season/<Run_ID>/
     mens_league_matches_clean.csv      01_cleaned/
     {LEAGUE}_training_data.csv       └── {LEAGUE}_{Season}_Season_Cleaned_{run_id}.csv
            │
            ▼
  Position split (in-memory, no file):
  df_field  → defender / midfielder / forward
  df_gk     → goalkeeper  (only when --gk is set)
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2 · League-Wide Report  (src/reporting/)                 │
│  SeasonReportBuilder                                            │
│  + season_analysis.filter_data_by_timeframe()                   │
│                                                                 │
│  One of:                                                        │
│  • timeframe = "season"       → all matchdays                   │
│  • timeframe = "half_season"  → MDs ≤ half_season_matchday cfg  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
  📄 Output/<Season>/<League>/Season/<Run_ID>/03_league_report/
     ├── {LEAGUE}_{Season}_League_{Timeframe}_Report_{run_id}.docx
     └── {LEAGUE}_{Season}_League_{Timeframe}_Report_{run_id}_GK.docx  (if --gk)

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3 · Per-Club Reports  (src/reporting/)                   │
│  Uses legacy document_generation.py + report_builder.py         │
│                                                                 │
│  Per club:                                                      │
│  • Table of Contents                                            │
│  • Introduction / Methodology / Key Concepts                    │
│  • Match Day Usage table      (get_matchday_stats)              │
│  • Player Usage table         (get_players_monitored_stats)     │
│  • Club Metric Results        (get_metric_summary)              │
│  • Top Players by Metric      (get_top_players_by_metric)       │
│  • Average Metrics/Position   (get_average_metrics_by_position) │
│  • Cumulative Position Volume (get_total_metrics_by_position)   │
│  • Club vs Season Comparison  (club_vs_season_comparison)       │
│  • Positional vs Season Avg   (positional_comparison_vs_season) │
│  • Rolling trend charts       (visualizations.py)               │
│  • Speed Zone Distribution    (get_speed_zone_breakdown)        │
│  • Challenges / Future Plans / Conclusion                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
  📄 Output/<Season>/<League>/Season/<Run_ID>/02_club_reports/
     ├── {LEAGUE}_{Season}_Season_Club_{ClubName}_Report_{run_id}.docx
     └── {LEAGUE}_{Season}_Season_Club_{ClubName}_Report_{run_id}_GK.docx  (if --gk)

  📄 Output/<Season>/<League>/Season/<Run_ID>/run_metadata.json
  📄 logs/<Season>/<League>/{run_id}_season.log
  📄 logs/run_history.csv
```

---

### Pipeline 3 — `weekly` *(Matchday GPS Report)*

Processes one matchday at a time from individual club-uploaded CSV files.

```
📥 INPUT
└── data/matchday_csvs/*.csv     (raw per-club GPS exports, not prefixed PROCESSED_)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  FILE DISCOVERY  (_find_csv_files)                              │
│  • Glob *.csv in --input directory                              │
│  • Skip files already prefixed PROCESSED_                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PER-FILE PROCESSING  (_process_files)                          │
│  src/utils/text_parsing.py                                      │
│  src/processing/gps_aggregation.py                              │
│                                                                 │
│  For each CSV file / session group:                             │
│  1. parse_matchday()        — extract MD number from title      │
│  2. parse_session_info()    — parse team names, location etc.   │
│  3. extract_metrics()       — select relevant GPS columns       │
│  4. aggregate_halves()      — combine H1 + H2 per player        │
│  5. best_match() fuzzy      — normalise team names to official  │
│     (src/utils/text_cleaning.py)  roster                       │
│  6. Track uploading_teams / missing_teams vs official roster    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
  Combined DataFrame (all teams for target matchday)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  FILTERING                                                      │
│  • compute_derived_metrics() — accel/dec totals & rates         │
│  • Keep rows:  duration ≥ 60 min  AND  distance ≥ 2 km          │
│  • Split:  df_field (no GKs)  /  df_gk (GKs only, if --gk)     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  REPORT GENERATION  (src/reporting/weekly_gps_report.py)        │
│  WeeklyGPSReportBuilder                                         │
│                                                                 │
│  • Matchday summary header (uploading / missing clubs)          │
│  • Per-player GPS metrics table                                 │
│  • Position-group averages                                      │
│  • Speed zone breakdown                                         │
│  • (GK variant generated separately when --gk is set)          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
  📄 Output/<Season>/<League>/Weekly/<Run_ID>/
     ├── {LEAGUE}_{Season}_Weekly_MD{N}_Report_{run_id}.docx
     └── {LEAGUE}_{Season}_Weekly_GK_MD{N}_Report_{run_id}.docx   (if --gk)

  📄 data/matchday_csvs/PROCESSED_<original_filename>.csv   ← renamed on success
  📄 logs/<Season>/<League>/{run_id}_weekly.log
  📄 logs/run_history.csv
```

---

## 📁 Project Structure

```
Match-Analysis/
│
├── data/
│   ├── raw/                    # Raw GPS tracking CSV exports (input)
│   ├── matchday_csvs/          # Per-matchday club uploads (weekly pipeline)
│   ├── processed/              # Cleaned CSVs (output of cleaning step)
│   │   ├── mens_league_matches_clean.csv
│   │   ├── womens_league_matches_clean.csv
│   │   └── {LEAGUE}_training_data.csv
│   └── external/               # External reference data
│
├── Output/                     # All pipeline run outputs
│   └── <Season>/
│       └── <LEAGUE>/
│           ├── Full/<Run_ID>/
│           │   ├── 01_cleaned/
│           │   ├── 02_club_reports/
│           │   ├── 03_league_report/
│           │   └── run_metadata.json
│           ├── Season/<Run_ID>/
│           │   └── (same structure)
│           └── Weekly/<Run_ID>/
│               └── {LEAGUE}_{Season}_Weekly_MD{N}_Report_{run_id}.docx
│
├── logs/
│   ├── run_history.csv         # Global log of all pipeline runs
│   └── <Season>/<LEAGUE>/
│       └── {run_id}_{pipeline}.log
│
├── scripts/
│   ├── match_analysis.py       # Unified CLI entry point
│   └── config/
│       └── analysis_config.yaml  # Half-season matchday cutoffs
│
├── src/
│   ├── pipelines/
│   │   ├── base.py             # Abstract pipeline (output dirs, logging, metadata)
│   │   ├── full.py             # FullPipeline  (4-phase end-to-end)
│   │   ├── season.py           # SeasonPipeline (season/half-season)
│   │   └── weekly.py           # WeeklyPipeline (matchday GPS)
│   │
│   ├── data/
│   │   ├── cleaning.py         # 17-step clean_pipeline() + all helper functions
│   │   ├── schemas.py          # Expected column definitions
│   │   └── validators.py       # Data integrity checks
│   │
│   ├── analysis/
│   │   ├── analysis.py         # Summary stats, player rankings, matchday counts
│   │   ├── season_analysis.py  # Timeframe filtering, club comparisons, speed zones
│   │   └── visualizations.py   # Matplotlib charts (trends, speed zones, etc.)
│   │
│   ├── reporting/
│   │   ├── club_report_builder.py    # Premium club report orchestrator (full pipeline)
│   │   ├── season_report_builder.py  # League-wide season/half-season report builder
│   │   ├── weekly_gps_report.py      # Weekly matchday GPS report builder
│   │   ├── report_builder.py         # Shared data-prep helpers (metrics, tables)
│   │   └── document_generation.py   # Low-level python-docx helpers
│   │
│   ├── config/
│   │   ├── constants.py          # Thresholds, metrics, file paths, corrections
│   │   ├── league_definitions.py # Club rosters, session patterns, max matchdays
│   │   ├── analysis_config.yaml  # Half-season cutoff configuration
│   │   ├── metrics.py            # Additional metric helpers
│   │   ├── speed_zones.py        # Speed zone definitions
│   │   └── styles.py             # Word document brand styles
│   │
│   ├── processing/
│   │   └── gps_aggregation.py    # Weekly pipeline: extract_metrics, aggregate_halves
│   │
│   └── utils/
│       ├── text_cleaning.py      # Club fuzzy-matching, position normalisation
│       ├── text_parsing.py       # Session title parsing (matchday, teams, result)
│       └── styling.py            # Document styling helpers
│
├── experiments/                  # Exploratory / prototyping code
├── notebook_archive/             # Legacy Jupyter notebooks
├── requirements.txt
└── .env                          # Environment overrides (optional)
```

---

## 📊 Output Reference

| Output File | Produced By | Location |
|---|---|---|
| `mens_league_matches_clean.csv` | `clean_pipeline()` | `data/processed/` |
| `womens_league_matches_clean.csv` | `clean_pipeline()` | `data/processed/` |
| `{LEAGUE}_training_data.csv` | `extract_and_save_training_data()` | `data/processed/` |
| `{LEAGUE}_…_Full_Cleaned_….csv` | `FullPipeline._phase_2_cleaning()` | `Output/…/Full/<Run>/01_cleaned/` |
| `{LEAGUE}_…_Full_Club_{Club}_Report_….docx` | `ClubReportBuilder.build()` | `Output/…/Full/<Run>/02_club_reports/` |
| `{LEAGUE}_…_League_{Timeframe}_Report_….docx` | `SeasonReportBuilder.build_report()` | `Output/…/Full/<Run>/03_league_report/` |
| `{LEAGUE}_…_Season_Cleaned_….csv` | `SeasonPipeline.run()` | `Output/…/Season/<Run>/01_cleaned/` |
| `{LEAGUE}_…_Season_Club_{Club}_Report_….docx` | `SeasonPipeline._generate_club_reports()` | `Output/…/Season/<Run>/02_club_reports/` |
| `{LEAGUE}_…_Weekly_MD{N}_Report_….docx` | `WeeklyGPSReportBuilder.build_report()` | `Output/…/Weekly/<Run>/` |
| `PROCESSED_<original>.csv` | `WeeklyPipeline._rename_files()` | `data/matchday_csvs/` |
| `run_metadata.json` | `AnalysisPipeline.save_metadata()` | `Output/…/<Pipeline>/<Run>/` |
| `{run_id}_{pipeline}.log` | `AnalysisPipeline.setup_run_context()` | `logs/<Season>/<League>/` |
| `run_history.csv` | `AnalysisPipeline._update_run_history_csv()` | `logs/` |

---

## 📈 Data Schema

### Cleaned Data Columns (`data/processed/*.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `p_name` | string | Player name |
| `club_for` | string | Player's club (normalised) |
| `club_against` | string | Opponent club |
| `match_day` | string | Matchday label (e.g. `Md12`) |
| `general_position` | string | Standardised position (`goalkeeper`, `defender`, `midfielder`, `forward`) |
| `player_position` | string | Raw position code (e.g. `CB`, `CAM`) |
| `location` | string | `Home` or `Away` |
| `result` | string | `Win`, `Loss`, or `Draw` |
| `duration` | float | Minutes played |
| `distance_km` | float | Total distance (km) |
| `sprint_distance_m` | float | Sprint distance (m) |
| `player_load` | float | Player Load score |
| `top_speed_kmh` | float | Peak speed (km/h) |
| `total_accelerations` | int | Summed acceleration zone counts |
| `total_decelerations` | int | Summed deceleration zone counts |
| `total_actions` | int | `total_accelerations + total_decelerations` |
| `acc_counts_per_min` | float | Acceleration rate (/min) |
| `dec_counts_per_min` | float | Deceleration rate (/min) |
| `distance_per_min_mmin` | float | Distance rate (m/min) |
| `energy_kcal` | float | Energy expenditure (kcal) |
| `power_plays` | int | Power play count |
| `work_ratio` | float | Work ratio (from 'All' split) |
| `distance_in_speed_zone_N_km` | float | Distance in speed zone 1–5 (km) |

---

## ⚙️ Configuration

### Key Tuning Points

| What to change | File | Variable/Key |
|---|---|---|
| Minimum match duration | `src/config/constants.py` | `MIN_SESSION_DURATION_MINUTES` |
| Minimum match distance | `src/config/constants.py` | `MIN_SESSION_DISTANCE_KM` |
| Outlier detection sensitivity | `src/config/constants.py` | `OUTLIER_IQR_MULTIPLIER` |
| Sparse column threshold | `src/config/constants.py` | `SPARSE_COLUMN_THRESHOLD` |
| Club name corrections (Women's) | `src/config/constants.py` | `CLUB_CORRECTIONS_WOMENS` |
| Club name corrections (Men's) | `src/config/constants.py` | `CLUB_CORRECTIONS_MENS` |
| Half-season cutoff matchday | `scripts/config/analysis_config.yaml` | `season_report.half_season_matchday` |
| Official club roster | `src/config/league_definitions.py` | `LEAGUE_CONFIG[league]['clubs']` |
| Position mapping | `src/config/league_definitions.py` | `POSITION_MAPPING`, `POSITION_ALIASES` |
| Session title regex pattern | `src/config/league_definitions.py` | `get_league_session_pattern()` |
| Volume / intensity metrics | `src/config/constants.py` | `VOLUME_METRICS`, `INTENSITY_METRICS` |
| Report brand styles | `src/config/styles.py` | `ReportStyles` |

### Environment Variables (`.env`)

```bash
LOG_LEVEL=INFO

DATA_DIR=./data/
RAW_DATA_DIR=./data/raw/
PROCESSED_DATA_DIR=./data/processed/
OUTPUT_DIR=./Output/
```

---

## 🛠️ Key Modules

### `src.data.cleaning` — `clean_pipeline()`

The entire 17-step cleaning sequence in a single call:

```python
from src.data.cleaning import clean_pipeline

cleaned_df, output_path = clean_pipeline(
    raw_path="data/raw/my_export.csv",
    league="upl",
    season="2024/25"
)
```

Individual steps are also importable if you need to replay just one stage:

```python
from src.data.cleaning import (
    load_raw_data, standardize_columns, filter_match_sessions,
    aggregate_halves, compute_derived_metrics, save_processed
)
```

### `src.analysis.season_analysis` — Timeframe Filtering

```python
from src.analysis.season_analysis import filter_data_by_timeframe

df_half = filter_data_by_timeframe(
    df, timeframe="half_season", league="upl", half_season_md=15
)
```

### `src.utils.text_cleaning` — Club Fuzzy Matching

```python
from src.utils.text_cleaning import best_match

canonical = best_match("Brite Stars", official_clubs, min_score=0.5)
# → "Shining Stars FC"
```

---

## 📚 League Information

### Women's League

**Season:** 2024-2025 · **Teams (12):**

College WFC · Crescent LFC · Phoenix FC · Lady Hawks FC · University WFC · Academy HS WFC · Sterling SS WFC · Corporate FC · Valkyrie FC · Heritage WFC · Hillside WFC

Session title format: `WMd<N> - <TeamA> - <TeamB> - <Location> - League - <Result>`

### Men's League

**Season:** 2024-2025 · **Teams (16):**

Forge FC · Capital FC · Metro SC · Cobras SC · Rapid FC · Shield FC · Industrial FC · Garrison FC · Mountain Heroes FC · Western City FC · Central FC · Army FC · Shining Stars FC · Revenue FC · Eastern FC · Lakeside Giants FC

Session title format: `Md<N> - <TeamA> - <TeamB> - <Location> - League - <Result>`

---

## 🐛 Troubleshooting

### Zero output rows after cleaning

The most common cause is the session-title filter. Check that your raw CSV session titles match the expected format:

```
# Women's League: WMd01 - Phoenix FC - Crescent LFC - Home - League - Win
# Men's League:  Md12 - Capital FC - Forge FC - Away - League - Draw
```

Adjust the pattern in `src/config/league_definitions.py → get_league_session_pattern()` if needed.

### Club names not matching

Add a manual correction in `src/config/constants.py`:

```python
CLUB_CORRECTIONS_MENS = {
    "Typo Name": "Correct Canonical Name",
}
```

Or lower the fuzzy-match threshold in `normalize_clubs()` (`min_score=0.5`).

### "Module not found" errors

Ensure the project root is on the Python path:

```bash
# Windows PowerShell
$env:PYTHONPATH = "$(pwd)"

# bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Slow processing

```python
# Process one league at a time
cleaned_df, _ = clean_pipeline(raw_path="...", league="fwsl", season="2024/25")

# Filter by date range after cleaning
df_recent = cleaned_df[cleaned_df["match_day"].str.extract(r"(\d+)")[0].astype(int) >= 10]
```

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and add tests in `tests/`
3. Run tests: `pytest`
4. Commit with a clear message
5. Open a Pull Request

**Code style:** PEP 8, type hints, docstrings on all public functions.

**Adding a new pipeline:** Subclass `AnalysisPipeline` in `src/pipelines/`, implement `name`, `register_arguments`, and `run`, then register it in `scripts/match_analysis.py`.

**Adding a new metric:** Define it in `src/config/constants.py` (`VOLUME_METRICS` or `INTENSITY_METRICS`), implement computation in `src/data/cleaning.py → compute_derived_metrics()`, and add a display name to `METRIC_DISPLAY_NAMES`.

---

## 🗺️ Roadmap

- [ ] Interactive web dashboard for data exploration
- [ ] Player benchmarking across leagues
- [ ] Injury risk prediction models
- [ ] Tactical analysis (positioning, heat maps)
- [ ] PDF / HTML export variants

---

## 📝 License & Attribution

**Data Source:** GPS tracking data  
**Leagues:** Women's League, Men's League  
**Author:** Performance Analytics Team

---

**Last Updated:** March 2026  
**Version:** 2.0
