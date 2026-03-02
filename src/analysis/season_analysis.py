"""
Season Analysis Module

Provides specialized analysis functions for season and half-season reports.
Handles time-based filtering (season, half-season, date range) and 
league-wide aggregations.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

from src.config import constants
from ..reporting import report_builder

logger = logging.getLogger(__name__)

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
    
    if 'match_day' in df.columns:
        # Vectorized matchday number extraction
        df['md_num'] = df['match_day'].astype(str).str.extract(r'(\d+)').fillna(0).astype(int)
        
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
    trend = df.groupby('match_day')['p_name'].nunique().reset_index(name='total_players')
    # Vectorized sort key extraction
    trend['sort_key'] = trend['match_day'].astype(str).str.extract(r'(\d+)').fillna(999).astype(int)
    stats['players_per_md_trend'] = trend.sort_values('sort_key').drop(columns='sort_key')
    
    # 5. Unique clubs per matchday
    clubs_trend = df.groupby('match_day')['club_for'].nunique().reset_index(name='total_clubs')
    clubs_trend['sort_key'] = clubs_trend['match_day'].astype(str).str.extract(r'(\d+)').fillna(999).astype(int)
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
    
    Delegates to report_builder.get_metric_summary for consistency.
    """
    vol_metrics = constants.VOLUME_METRICS
    int_metrics = constants.INTENSITY_METRICS

    # report_builder.get_metric_summary combines both, but returns a single table.
    # season_analysis expects a dict with 'volume' and 'intensity' keys for Legacy reasons.
    
    stats = {}

    # Volume: include sum (Total)
    valid_vol = [m for m in vol_metrics if m in df.columns]
    vol_df = df[valid_vol].agg(['sum', 'mean', 'std', 'max']).T
    vol_df = vol_df.rename(columns={'sum': 'Total', 'mean': 'Mean', 'std': 'Std Dev', 'max': 'Max'})
    stats['volume'] = vol_df.reset_index().rename(columns={'index': 'Metric'})
    
    # Intensity: exclude sum (Total) by setting to NaN
    valid_int = [m for m in int_metrics if m in df.columns]
    int_df = df[valid_int].agg(['sum', 'mean', 'std', 'max']).T
    int_df['sum'] = np.nan # Null out the sum as it makes no analytical sense for intensity
    int_df = int_df.rename(columns={'sum': 'Total', 'mean': 'Mean', 'std': 'Std Dev', 'max': 'Max'})
    stats['intensity'] = int_df.reset_index().rename(columns={'index': 'Metric'})
    
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
    Aggregate speed zone distances by position group.
    
    Delegates to report_builder.get_speed_zone_breakdown for robust multi-pattern matching.
    """
    stats = {}
    
    # Ensure general_position exists
    if 'general_position' not in df.columns:
        df = df.copy()
        df['general_position'] = df.get('player_position', 'Unknown').fillna('Unknown')
    else:
        df['general_position'] = df['general_position'].fillna('Unknown')

    # Use the more robust report_builder implementation
    zone_by_position, zone_pct = report_builder.get_speed_zone_breakdown(df)
    
    if not zone_by_position.empty:
        stats['dist'] = zone_by_position
        stats['dist_pct'] = zone_pct
        
    return stats

def get_club_comparison(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Club averages for all volume and intensity metrics.
    """
    vol_metrics = constants.VOLUME_METRICS
    int_metrics = constants.INTENSITY_METRICS
    
    valid_vol = [m for m in vol_metrics if m in df.columns]
    valid_int = [m for m in int_metrics if m in df.columns]
    
    stats = {}
    if valid_vol:
        stats['volume'] = df.groupby('club_for')[valid_vol].mean()
    if valid_int:
        stats['intensity'] = df.groupby('club_for')[valid_int].mean()
        
    return stats
