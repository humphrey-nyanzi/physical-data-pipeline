import pandas as pd
from src.utils.text_parsing import parse_player_details

def extract_metrics(df, csv_file, log_func=print):
    """
    Extract required metrics from dataframe.
    Uses exact Catapult column names from user's CSV.
    And parses player names.
    
    IMPORTANT: This function now keeps ALL original columns from the dataset,
    only validating that required columns exist. This ensures columns needed 
    for derived metrics (e.g., acceleration zones for total_accelerations) are preserved.
    """
    # Core columns that MUST exist
    required_cols = [
        'Player Name',
        'Duration',  # In minutes according to Catapult
        'Distance (km)',
        'Sprint Distance (m)',
        'Top Speed (km/h)',
        'Player Load'
    ]
    
    # Check all required columns exist
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        log_func(f"{csv_file}: Missing columns {missing}", "error")
        return pd.DataFrame()
    
    # KEEP ALL COLUMNS from original dataset instead of filtering
    # This preserves columns needed for derived metrics (acceleration/deceleration zones, etc.)
    df_clean = df.copy()
    
    # Remove rows without player names
    df_clean = df_clean[df_clean['Player Name'].notna()]
    
    # Parse Player Details
    # Apply parsing to create new columns
    df_clean[['Clean Name', 'Position']] = df_clean['Player Name'].apply(
        lambda x: pd.Series(parse_player_details(x))
    )
    
    # Dynamically discover all numeric columns to convert
    # Core required numeric columns
    core_numeric = ['Duration', 'Distance (km)', 'Sprint Distance (m)', 
                    'Top Speed (km/h)', 'Player Load']
    
    # Dynamically find acceleration/deceleration/speed zone columns  
    acc_zone_cols = [c for c in df_clean.columns if 'acceleration' in c.lower() and 'zone' in c.lower() and 'count' in c.lower()]
    dec_zone_cols = [c for c in df_clean.columns if 'deceleration' in c.lower() and 'zone' in c.lower() and 'count' in c.lower()]
    speed_zone_cols = [c for c in df_clean.columns if 'distance' in c.lower() and 'speed' in c.lower() and 'zone' in c.lower()]
    
    # Combine all numeric columns
    numeric_cols = core_numeric + acc_zone_cols + dec_zone_cols + speed_zone_cols
    
    # Convert known numeric columns
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
    
    # Remove rows with all NaN in core metrics only (don't drop rows if zone columns are missing)
    df_clean = df_clean.dropna(subset=core_numeric, how='all')
    
    # Add source file for tracking
    df_clean['source_csv'] = csv_file
    
    return df_clean

def aggregate_halves(df, log_func=print):
    """
    Aggregate 1st.half and 2nd.half data for each player.
    Filters out 'Full Session' or other aggregate rows to prevent double counting.
    - SUM: most metrics (Distance, Sprint Distance, Player Load, Duration)
    - MAX: metrics starting with 'Top' or 'Max' (Top Speed, Max Acceleration, etc.)
    
    Returns: Aggregated dataframe with one row per player
    """
    if df.empty:
        return df

    # CRITICAL: Filter for halves ONLY to prevent double addition (e.g. Full Session + Halves)
    from src.config import constants
    
    # Identify the split/period column
    # Common Catapult names: 'Split Name', 'Period Name'
    split_col = next((c for c in df.columns if c in ['Split Name', 'Period Name']), None)
    
    if split_col:
        valid_halves = [v.lower().strip() for v in constants.SPLIT_NAMES.values()]
        # Filter to only include rows that match the valid half names (case-insensitive)
        df_filtered = df[df[split_col].astype(str).str.lower().str.strip().isin(valid_halves)].copy()
        
        if not df_filtered.empty:
            df = df_filtered
        else:
            # If no halves found, we should pick a sensible default like 'all' or 'game'
            # to avoid summing EVERYTHING if those rows exist.
            # If we don't find halves, we take the one with 'all' or 'game' 
            # instead of letting everything sum up.
            df_fallback = df[df[split_col].astype(str).str.lower().str.strip().isin(['all', 'game', 'entire session'])].copy()
            if not df_fallback.empty:
                # If there are multiple (e.g., 'all' and 'game'), take 'all' or the first one
                df = df_fallback.groupby('Player Name', as_index=False).head(1)
            else:
                # Extreme fallback: if no known splits at all, just take the first row per player
                # logic to prevent distance inflation
                pass
    
    # Identify numeric columns to aggregate
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    # Remove source_csv from numeric if present
    if 'source_csv' in numeric_cols:
        numeric_cols.remove('source_csv')
    
    # Separate columns by aggregation method
    max_cols = [col for col in numeric_cols if col.lower().startswith('top') or col.lower().startswith('max')]
    sum_cols = [col for col in numeric_cols if col not in max_cols]
    
    # Build aggregation dictionary
    agg_dict = {}
    
    # Sum for most metrics
    for col in sum_cols:
        agg_dict[col] = 'sum'
    
    # Max for Top/Max metrics
    for col in max_cols:
        agg_dict[col] = 'max'
    
    # Keep first value for non-numeric columns (they should be identical per player)
    non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()
    for col in non_numeric_cols:
        if col not in ['Player Name', 'source_csv']:
            agg_dict[col] = 'first'
    
    # Group by Player Name and aggregate
    df_agg = df.groupby('Player Name', as_index=False).agg(agg_dict)
    
    return df_agg


def compute_derived_metrics(df):
    """
    Compute total accelerations, decelerations and their rates.
    Matches the logic in cleaning.py but works with unstandardized column names.
    """
    if df.empty:
        return df

    df = df.copy()

    # Identify zone columns
    acc_cols = [
        c
        for c in df.columns
        if "acceleration" in c.lower() and "zone" in c.lower() and "count" in c.lower()
    ]
    dec_cols = [
        c
        for c in df.columns
        if "deceleration" in c.lower() and "zone" in c.lower() and "count" in c.lower()
    ]

    # Calculate Totals
    if acc_cols:
        df["total_accelerations"] = df[acc_cols].sum(axis=1)
    else:
        df["total_accelerations"] = 0

    if dec_cols:
        df["total_decelerations"] = df[dec_cols].sum(axis=1)
    else:
        df["total_decelerations"] = 0

    # Calculate Rates
    if "Duration" in df.columns:
        # Avoid division by zero
        dur = df["Duration"].replace(0, 1)  # or NaN
        df["acc_counts_per_min"] = df["total_accelerations"] / dur
        df["dec_counts_per_min"] = df["total_decelerations"] / dur

    return df
