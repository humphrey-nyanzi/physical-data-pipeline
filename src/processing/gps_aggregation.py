import pandas as pd
from src.utils.text_parsing import parse_player_details

def extract_metrics(df, csv_file, log_func=print):
    """
    Extract required metrics from dataframe.
    Uses exact Catapult column names from user's CSV.
    And parses player names.
    """
    # Exact column names from Catapult export
    required_cols = [
        'Player Name',
        'Duration',  # In minutes according to Catapult
        'Distance (km)',
        'Sprint Distance (m)',
        'Top Speed (km/h)',
        'Player Load'
    ]
    
    # Check all columns exist
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        log_func(f"{csv_file}: Missing columns {missing}", "error")
        return pd.DataFrame()
    
    # Extract required columns
    df_clean = df[required_cols].copy()
    
    # Remove rows without player names
    df_clean = df_clean[df_clean['Player Name'].notna()]
    
    # Parse Player Details
    # Apply parsing to create new columns
    df_clean[['Clean Name', 'Position']] = df_clean['Player Name'].apply(
        lambda x: pd.Series(parse_player_details(x))
    )
    
    # Convert numeric columns
    numeric_cols = ['Duration', 'Distance (km)', 'Sprint Distance (m)', 
                   'Top Speed (km/h)', 'Player Load']
    
    for col in numeric_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Remove rows with all NaN metrics
    df_clean = df_clean.dropna(subset=numeric_cols, how='all')
    
    # Add source file for tracking
    df_clean['source_csv'] = csv_file
    
    return df_clean

def aggregate_halves(df, log_func=print):
    """
    Aggregate 1st.half and 2nd.half data for each player.
    - SUM: most metrics (Distance, Sprint Distance, Player Load, Duration)
    - MAX: metrics starting with 'Top' or 'Max' (Top Speed, Max Acceleration, etc.)
    
    Returns: Aggregated dataframe with one row per player
    """
    if df.empty:
        return df
    
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
    
    # Log handled by caller usually, but added support if needed
    # log_func(f"      Aggregated {len(df)} half records → {len(df_agg)} full match records")
    
    return df_agg
