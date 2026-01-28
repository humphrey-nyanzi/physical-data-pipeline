"""
Season Analysis Module

Provides specialized analysis functions for season and half-season reports.
Handles time-based filtering (season, half-season, date range) and 
league-wide aggregations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Metric Definitions
# ============================================================================

VOLUME_METRICS = [
    'distance_km', 'sprint_distance_m', 'power_plays', 'energy_kcal', 'impacts',
    'total_accelerations', 'total_decelerations'
]

INTENSITY_METRICS = [
    'player_load', 'top_speed_kmh', 'distance_per_min_mmin', 'power_score_wkg', 
    'work_ratio', 'max_acceleration_mss', 'max_deceleration_mss', 
    'acc_counts_per_min', 'dec_counts_per_min'
]

SPEED_ZONE_DIST_COLS = [
    'distance_in_speed_zone_1_km', 'distance_in_speed_zone_2_km', 
    'distance_in_speed_zone_3_km', 'distance_in_speed_zone_4_km', 
    'distance_in_speed_zone_5_km'
]

SPEED_ZONE_TIME_COLS = [
    'time_in_speed_zone_1_secs', 'time_in_speed_zone_2_secs', 
    'time_in_speed_zone_3_secs', 'time_in_speed_zone_4_secs', 
    'time_in_speed_zone_5_secs'
]

# ============================================================================
# Core Filtering
# ============================================================================

def filter_data_by_timeframe(
    df: pd.DataFrame,
    timeframe: str,
    league: str,
    half_season_md: int,
    date_range: Optional[Tuple[str, str]] = None
) -> pd.DataFrame:
    """
    Filter data based on the requested timeframe.
    """
    logger.info(f"Filtering data for timeframe: {timeframe}")
    
    # Calculate derived metrics if missing
    if 'total_accelerations' not in df.columns:
        acc_cols = [c for c in df.columns if 'accelerations_zone_count' in c]
        if acc_cols:
            df['total_accelerations'] = df[acc_cols].sum(axis=1)
    
    if 'total_decelerations' not in df.columns:
        dec_cols = [c for c in df.columns if 'deceleration_zone_count' in c]
        if dec_cols:
            df['total_decelerations'] = df[dec_cols].sum(axis=1)
            
    if 'acc_counts_per_min' not in df.columns and 'duration' in df.columns:
        df['acc_counts_per_min'] = df['total_accelerations'] / df['duration']
        
    if 'dec_counts_per_min' not in df.columns and 'duration' in df.columns:
        df['dec_counts_per_min'] = df['total_decelerations'] / df['duration']

    if timeframe == 'season':
        return df.copy()
    
    # Extract matchday number
    def extract_md_num(s):
        import re
        match = re.search(r'\d+', str(s))
        return int(match.group()) if match else 0

    if 'match_day' in df.columns:
        df['md_num'] = df['match_day'].apply(extract_md_num)
        
        if timeframe == 'half_season':
            filtered_df = df[df['md_num'] <= half_season_md].copy()
            return filtered_df.drop(columns=['md_num'])
            
    if timeframe == 'date_range' and date_range:
        if 'date' in df.columns:
            start_date = pd.to_datetime(date_range[0])
            end_date = pd.to_datetime(date_range[1])
            df['dt'] = pd.to_datetime(df['date'], errors='coerce')
            filtered_df = df[(df['dt'] >= start_date) & (df['dt'] <= end_date)].copy()
            return filtered_df.drop(columns=['md_num', 'dt'] if 'md_num' in df.columns else ['dt'])

    return df

# ============================================================================
# Usage Analysis
# ============================================================================

def get_usage_stats(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Compute comprehensive usage statistics.
    """
    stats = {}
    
    # 1. Unique players per club
    stats['unique_players_per_club'] = df.groupby('club_for')['p_name'].nunique().reset_index(name='unique_players').sort_values('unique_players', ascending=False)
    
    # 2. Matchdays uploaded per club
    stats['matchdays_per_club'] = df.groupby('club_for')['match_day'].nunique().reset_index(name='matchdays_uploaded').sort_values('matchdays_uploaded', ascending=False)
    
    # 3. Avg Players per matchday
    daily_club_counts = df.groupby(['match_day', 'club_for'])['p_name'].nunique().reset_index()
    stats['avg_players_per_md'] = daily_club_counts.groupby('club_for')['p_name'].mean().reset_index(name='avg_players').sort_values('avg_players', ascending=False)
    
    # 4. Total unique players captured per matchday (League Trend)
    # Extract md number for sorting
    import re
    def get_sort_key(s):
        m = re.search(r'\d+', str(s))
        return int(m.group()) if m else 999
        
    trend = df.groupby('match_day')['p_name'].nunique().reset_index(name='total_players')
    trend['sort_key'] = trend['match_day'].apply(get_sort_key)
    stats['players_per_md_trend'] = trend.sort_values('sort_key').drop(columns='sort_key')
    
    # 5. Unique clubs per matchday
    clubs_trend = df.groupby('match_day')['club_for'].nunique().reset_index(name='total_clubs')
    clubs_trend['sort_key'] = clubs_trend['match_day'].apply(get_sort_key)
    stats['clubs_per_md_trend'] = clubs_trend.sort_values('sort_key').drop(columns='sort_key')
    
    return stats

def get_coverage_grid(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a pivot table of Matchday x Club presence (1 if present, 0 else).
    """
    grid = df.groupby(['match_day', 'club_for']).size().unstack(fill_value=0)
    # Convert to binary
    grid = (grid > 0).astype(int)
    
    # Sort columns (Clubs) and index (Matchdays)
    import re
    def sort_key(s):
        m = re.search(r'\d+', str(s))
        return int(m.group()) if m else 999
        
    sorted_index = sorted(grid.index, key=sort_key)
    return grid.reindex(sorted_index).T # Transpose for Club (y) vs Matchday (x)

def get_max_matches_players(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Return players with highest number of analyzed matches."""
    counts = df.groupby(['p_name', 'club_for'])['match_day'].nunique().reset_index(name='matches')
    return counts.sort_values('matches', ascending=False).head(top_n)

# ============================================================================
# Performance Analysis
# ============================================================================

def get_performance_stats(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Compute aggregated performance stats (Volume & Intensity).
    """
    valid_vol = [m for m in VOLUME_METRICS if m in df.columns]
    valid_int = [m for m in INTENSITY_METRICS if m in df.columns]

    stats = {}

    # Volume: include sum (Total)
    vol_stats = df[valid_vol].agg(['sum', 'mean', 'std', 'max']).T
    vol_stats = vol_stats.rename(columns={'sum': 'Total', 'mean': 'Mean', 'std': 'Std Dev', 'max': 'Max'})
    stats['volume'] = vol_stats.reset_index().rename(columns={'index': 'Metric'})
    
    # Intensity: exclude sum (Total) by setting to NaN
    int_stats = df[valid_int].agg(['sum', 'mean', 'std', 'max']).T
    int_stats['sum'] = np.nan # Null out the sum as it makes no analytical sense for intensity
    int_stats = int_stats.rename(columns={'sum': 'Total', 'mean': 'Mean', 'std': 'Std Dev', 'max': 'Max'})
    stats['intensity'] = int_stats.reset_index().rename(columns={'index': 'Metric'})
    
    return stats

def get_max_performers(df: pd.DataFrame, metrics: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Get top players based on Absolute MAX value in the session.
    """
    leaderboards = {}
    for metric in metrics:
        if metric in df.columns:
            # Get max row for this metric
            # Or get max value per player then sort?
            # Usually we want "Single highest session record"
            top = df.nlargest(10, metric)[['p_name', 'club_for', 'match_day', metric]]
            leaderboards[metric] = top
    return leaderboards

def get_contextual_stats(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Compare Home vs Away, and Win vs Draw vs Loss.
    """
    stats = {}
    metrics = ['distance_km', 'player_load', 'top_speed_kmh', 'work_ratio']
    valid_metrics = [m for m in metrics if m in df.columns]
    
    if 'location' in df.columns:
        stats['location'] = df.groupby('location')[valid_metrics].mean()
        
    if 'result' in df.columns:
        stats['result'] = df.groupby('result')[valid_metrics].mean()
        
    return stats

def get_speed_zone_stats(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Aggregate speed zone distances/times by position group.
    """
    stats = {}
    
    if 'general_position' in df.columns:
        df['general_position'] = df['general_position'].fillna('Unknown')
    else:
        df['general_position'] = df.get('player_position', 'Unknown')

    # Distance
    valid_dist = [c for c in SPEED_ZONE_DIST_COLS if c in df.columns]
    if valid_dist:
        stats['dist'] = df.groupby('general_position')[valid_dist].mean()
        stats['dist_pct'] = stats['dist'].div(stats['dist'].sum(axis=1), axis=0) * 100
        
    # Time
    valid_time = [c for c in SPEED_ZONE_TIME_COLS if c in df.columns]
    if valid_time:
        stats['time'] = df.groupby('general_position')[valid_time].mean()
        stats['time_pct'] = stats['time'].div(stats['time'].sum(axis=1), axis=0) * 100
        
    return stats

def get_club_comparison(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Club averages for all volume and intensity metrics.
    """
    valid_vol = [m for m in VOLUME_METRICS if m in df.columns]
    valid_int = [m for m in INTENSITY_METRICS if m in df.columns]
    
    stats = {}
    if valid_vol:
        stats['volume'] = df.groupby('club_for')[valid_vol].mean()
    if valid_int:
        stats['intensity'] = df.groupby('club_for')[valid_int].mean()
        
    return stats
