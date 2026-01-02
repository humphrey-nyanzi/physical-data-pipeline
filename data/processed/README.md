# Processed Data

This directory contains cleaned and processed datasets ready for analysis.

## Contents

- `FWSL25_matches_clean.csv` - Cleaned FWSL match data (Uganda women's football league)
- `UPL25_matches_clean.csv` - Cleaned UPL match data (Uganda professional league)

## Schema

| Column | Type | Description |
|--------|------|-------------|
| match_date | datetime | Date of the match |
| club | string | Club/team name (normalized) |
| league | string | League code (FWSL or UPL) |
| player_name | string | Player name (normalized) |
| position | string | Player position (raw) |
| position_category | string | Position category (GK, DEF, MID, FWD) |
| minutes_played | float | Minutes played in match |
| total_distance_km | float | Total distance covered (km) |
| high_speed_distance_km | float | Distance at high speed >6 m/s (km) |
| sprint_distance_km | float | Distance at sprint speed >7 m/s (km) |
| total_accel_events | int | Number of acceleration events |
| total_decel_events | int | Number of deceleration events |
| avg_velocity_ms | float | Average velocity (m/s) |
| max_velocity_ms | float | Maximum velocity reached (m/s) |
| player_load | float | Player load (intensity measure) |
| per_minute_distance | float | Distance per minute played (km/min) |

## Cleaning Steps

1. **Column standardization** - Lowercase, trim whitespace
2. **Session filtering** - Keep only match sessions (discard practice)
3. **Club normalization** - Fuzzy matching to standard club names
4. **Position parsing** - Categorize into GK/DEF/MID/FWD
5. **Data validation** - Check for missing, duplicates, outliers
6. **Derived metrics** - Compute per-minute and efficiency metrics

## Usage

```python
import pandas as pd

# Load FWSL data
fwsl_df = pd.read_csv('FWSL25_matches_clean.csv')

# Load UPL data
upl_df = pd.read_csv('UPL25_matches_clean.csv')
```

Or use the analysis module:

```python
from src.data.cleaning import load_processed_data

fwsl_df = load_processed_data('fwsl')
upl_df = load_processed_data('upl')
```

## Data Quality

- No missing required columns
- Outliers flagged and reviewed
- Duplicates removed
- All player names and clubs normalized
