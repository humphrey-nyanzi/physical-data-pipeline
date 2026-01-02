# Raw Data

This directory contains raw, unprocessed data from Catapult exports.

## Contents

- `all_catapult_data_16_Jul_25.csv` - Raw Catapult match data export for FWSL and UPL leagues

## Data Source

**Frequency:** Updated as new matches are completed  
**Format:** CSV (Comma-separated values)  
**Updated:** Periodically as new match data becomes available

## Usage

Use `src.data.cleaning.load_raw_data()` to load this data. Do not modify files in this directory directly.

See [processed/README.md](../processed/README.md) for cleaned data.
