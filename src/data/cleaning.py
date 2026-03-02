"""
Unified data cleaning module for Match-Analysis.

CORRECTED to match notebook logic exactly.
"""

from typing import List, Optional, Tuple
import os
import re
import pandas as pd
import numpy as np
import logging

from ..config import constants, league_definitions
from ..utils import text_cleaning

logger = logging.getLogger(__name__)



def filter_by_position(
    df: pd.DataFrame, 
    positions: Optional[List[str]] = None,
    general_position: bool = True
) -> pd.DataFrame:
    """
    Filter dataframe to include only specified positions.
    
    Args:
        df: Input dataframe with position columns
        positions: List of position codes/names to keep (e.g., ['CB', 'LB'] or ['defender', 'midfielder'])
        general_position: If True, filter by 'general_position' column; else by 'player_position'
    
    Returns:
        Filtered dataframe containing only specified positions
    """
    if positions is None or len(positions) == 0:
        return df
    
    df = df.copy()
    
    position_col = 'general_position' if general_position else 'player_position'
    if position_col not in df.columns:
        logger.warning(f"Column '{position_col}' not found. Returning unfiltered data.")
        return df
    
    # Normalize positions to lowercase for comparison
    positions_lower = [p.lower() for p in positions]
    mask = df[position_col].astype(str).str.lower().isin(positions_lower)
    
    df_filtered = df[mask].reset_index(drop=True)
    dropped = len(df) - len(df_filtered)
    
    if dropped > 0:
        logger.info(f"Filtered by position: removed {dropped} rows not matching {positions}")
    
    return df_filtered


def load_raw_data(path: str = None) -> pd.DataFrame:
    """Load raw CSV data. Defaults to `RAW_DATA_FILE` in constants."""
    if path is None:
        path = constants.RAW_DATA_FILE
    return pd.read_csv(path)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names: lowercase, remove special characters, underscores."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[\/\(\)\-]", "", regex=True)
        .str.replace("velocity_zone", "speed_zone")
    )
    return df


def normalize_duration_to_minutes(
    df: pd.DataFrame,
    duration_col: str = "duration",
    raw_unit: str = "seconds",
    keep_raw_seconds: bool = True,
    heuristic_if_unknown: bool = True,
) -> pd.DataFrame:
    """Normalize duration values to minutes."""
    df = df.copy()
    if duration_col not in df.columns:
        return df

    duration = pd.to_numeric(df[duration_col], errors="coerce")
    unit = (raw_unit or "auto").strip().lower()

    if unit in {"auto", "unknown", ""} and heuristic_if_unknown:
        med = duration.dropna().median() if duration.notna().any() else np.nan
        mx = duration.dropna().max() if duration.notna().any() else np.nan
        if (pd.notna(med) and med > 300) or (pd.notna(mx) and mx > 240):
            unit = "seconds"
        else:
            unit = "minutes"

    if unit == "seconds":
        if keep_raw_seconds and "duration_seconds_raw" not in df.columns:
            df["duration_seconds_raw"] = duration
        df[duration_col] = duration / 60.0
    elif unit == "minutes":
        df[duration_col] = duration
    else:
        df[duration_col] = duration

    return df


def extract_and_save_training_data(df: pd.DataFrame, league: str, out_dir: str = None) -> pd.DataFrame:
    """
    Extract training data, save it to a separate CSV, and return the filtered game data.
    Looks for a column named 'tags' or 'tag' (case-insensitive).
    """
    df = df.copy()
    
    # Identify the tag column
    tag_cols = [c for c in df.columns if c.lower() in ("tags", "tag")]
    if not tag_cols:
        logger.warning("No 'tags' or 'tag' column found. Skipping training data extraction.")
        return df
        
    tag_col = tag_cols[0]
    
    # Standardize tag values for matching
    df["_clean_tag"] = df[tag_col].astype(str).str.strip().str.lower()
    
    # Extract and save training data
    training_df = df[df["_clean_tag"] == "training"].drop(columns=["_clean_tag"]).copy()
    
    if len(training_df) > 0:
        if out_dir is None:
            out_dir = constants.PROCESSED_DATA_DIR
        os.makedirs(out_dir, exist_ok=True)
        fname = f"{league.upper()}_training_data.csv"
        path = os.path.join(out_dir, fname)
        training_df.to_csv(path, index=False)
        logger.info(f"Saved {len(training_df)} training rows to {path}")
        
    # Filter df to keep only game and game training
    df_filtered = df[df["_clean_tag"].isin(["game", "game training"])].drop(columns=["_clean_tag"]).reset_index(drop=True)
    
    dropped = len(df) - len(df_filtered)
    if dropped > 0:
        logger.info(f"Filtered out {dropped} non-game rows based on '{tag_col}' column.")
        
    return df_filtered


def filter_match_sessions(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """Keep only rows that look like match sessions for the given league."""
    df = df.copy()
    initial_count = len(df)
    pattern = league_definitions.get_league_session_pattern(league)
    
    if "session_title" in df.columns:
        mask = df["session_title"].astype(str).str.match(pattern, na=False, case=False)
        df_filtered = df.loc[mask].reset_index(drop=True)
        
        dropped = initial_count - len(df_filtered)
        if dropped > 0:
            logger.warning(
                f"DATA EXCLUSION: {dropped} rows did not match {league.upper()} session pattern. "
                "These likely represent non-match sessions and were excluded."
            )
        return df_filtered
    
    return df






def standardize_split_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to valid split types and standardize their names.
    
    **CRITICAL**: Notebooks explicitly filter BEFORE standardizing.
    This prevents contamination from non-standard split_name values like
    "Half 1", "1st Half (Timed)", etc.
    """
    df = df.copy()
    if 'split_name' not in df.columns:
        return df

    initial_count = len(df)
    
    # Step 1: Filter to ONLY valid split types (like notebooks do)
    # Valid raw values (before cleaning/standardization):
    # '1st.half', '2nd.half', '1St.Half', '2Nd.Half', 'all' (various cases and formatting)
    valid_pattern = r"^(1st\.half|2nd\.half|1st.half|2nd.half|all|all/game)$"
    mask = df['split_name'].astype(str).str.lower().str.match(valid_pattern, na=False)
    df = df[mask].reset_index(drop=True)
    
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(
            f"DATA EXCLUSION: {dropped} rows with invalid 'split_name' values. "
            "Only '1st Half', '2nd Half', and 'All' are recognized."
        )
    
    # Step 2: Standardize the valid values to title case with spaces
    # Convert all case variants to the standard format: '1st Half', '2nd Half', 'All'
    # First, normalize to lowercase for consistent replacement
    df['split_name'] = df['split_name'].astype(str).str.lower()
    
    # Then replace with standardized format
    df['split_name'] = df['split_name'].str.replace('1st.half', '1st Half', regex=False)
    df['split_name'] = df['split_name'].str.replace('2nd.half', '2nd Half', regex=False)
    df['split_name'] = df['split_name'].str.replace('all/game', 'All', regex=False)
    df['split_name'] = df['split_name'].str.replace('all', 'All', regex=False)
    
    return df


def extract_session_info(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract matchday, teams, location, league, and result from session_title.

    Parses the standard Catapult session title format:
    'MD# - Team A - Team B - Location - League - Result'

    Args:
        df: Input dataframe with 'session_title' column.

    Returns:
        Dataframe with additional columns: 'match_day', 'club_for', 'club_against', 
        'location', 'league', and 'result'.
    """
    if "session_title" not in df.columns:
        return df

    df = df.copy()

    # 1. Clean the session title
    # Note: re-processing with str.replace(r"\s*-\s*", "-") ensures exactly one hyphen separator
    df["session_title"] = (
        df["session_title"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.+", "", regex=True)
        .str.replace(r"\s*-\s*", "-", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )

    # 2. Extract session components
    # Support both UPL (Md \d+) and FWSL (Wmd \d+) formats, with or without spaces
    # We use a non-greedy approach for teams to handle potential hyphens in names gracefully
    session_regex = re.compile(
        r"^(W?Md\s*\d+)-"      # Group 1: match_day (e.g. Md 01 or Md01)
        r"(.+?)-"              # Group 2: club_for
        r"(.+?)-"              # Group 3: club_against
        r"([^-]+)"             # Group 4: Part 1
        r"(?:-([^-]+))?"       # Group 5: Part 2 (Optional)
        r"(?:-([^-]+))?"       # Group 6: Part 3 (Optional)
        r"(?:\s|$)",           # End of relevant content
        re.IGNORECASE,
    )

    extracted = df["session_title"].str.extract(session_regex)
    if extracted.isnull().all().all():
        logger.warning("Could not extract session info from any session_title values.")
        return df

    extracted.columns = [
        "match_day",
        "ex_club_for",
        "ex_club_against",
        "part1",
        "part2",
        "part3",
    ]

    location_set = {"Home", "Away"}
    league_set = {"League", "Cup"}
    result_set = {"Win", "Loss", "Draw"}

    # Vectorized extraction of location, league, and result
    # We check all three potential parts (part1, part2, part3) for matches in the sets
    def get_component(row, valid_set):
        for col in ['part1', 'part2', 'part3']:
            val = str(row[col]).strip().title() if pd.notna(row[col]) else None
            if val in valid_set:
                return val
        return None

    extracted["location"] = extracted.apply(get_component, axis=1, valid_set=location_set)
    extracted["league"] = extracted.apply(get_component, axis=1, valid_set=league_set)
    extracted["result"] = extracted.apply(get_component, axis=1, valid_set=result_set)

    # Note: apply(axis=1) is better than iterrows, but for even more speed we could
    # use vectorized set membership if we melt the dataframe, but this is a good first step.
    # Given the small number of columns (3 parts), this is significantly faster than iterrows.

    # Keep only fully matched rows
    initial_count = len(df)
    valid_mask = extracted[["location", "league", "result"]].notnull().all(axis=1)
    df = df.loc[valid_mask].reset_index(drop=True)
    extracted = extracted.loc[valid_mask].reset_index(drop=True)
    
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(
            f"LOGICAL ERROR: {dropped} rows could not be fully parsed "
            "(missing location, league, or result). These records were excluded."
        )

    df["match_day"] = extracted["match_day"]
    df["club_for"] = extracted["ex_club_for"]
    df["club_against"] = extracted["ex_club_against"]
    df["location"] = extracted["location"]
    df["result"] = extracted["result"]

    return df


def validate_matchday_logic(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """Validate that matchdays are within the logical bounds for the league."""
    if "match_day" not in df.columns:
        return df

    df = df.copy()
    config = league_definitions.get_league_config(league)
    max_md = config.get("max_matchdays", 30)

    md_numeric = pd.to_numeric(
        df["match_day"].str.extract(r"(\d+)")[0], errors="coerce"
    )
    invalid_mask = md_numeric > max_md

    if invalid_mask.any():
        invalid_mds = df.loc[invalid_mask, "match_day"].unique()
        logger.error(
            f"LOGICAL ERROR: Found matchdays {invalid_mds} exceeding {league.upper()} maximum of {max_md}. "
            "These records will be excluded."
        )
        df = df[~invalid_mask].reset_index(drop=True)

    return df


def extract_player_columns(df: pd.DataFrame, league: str = None) -> pd.DataFrame:
    """
    Extracts player name, club and position from 'player_name' column.
    
    Also handles UPL-specific missing positions dictionary.
    """
    df = df.copy()

    if "p_name" in df.columns and "player_name" not in df.columns:
        df = df.rename(columns={"p_name": "player_name"})

    if "player_name" not in df.columns:
        raise KeyError("player_name column required for player extraction")

    # Step 1: Extract player info using unified utils
    # Note: text_cleaning.extract_player_info handles format fixing internally
    df, player_cols = text_cleaning.extract_player_info(df, player_name_column='player_name')
    
    # Step 2: Add extracted columns back to df
    df = pd.concat([df, player_cols], axis=1)

    # Step 3: Handle missing positions (UPL-specific)
    if league and league.lower() == 'upl':
        missing_positions = {
            'Saidi Mayanja': 'CM',
            'Ashraf Mugume': 'CM',
            'Musitafa Mujuzi': 'CB',
            'Bright Anukani': 'AM',
            'Kiza Arafat': 'AM',
            'Joel Sserunjogi': 'DM',
            'Katenga Etienne Openga': 'LW',
            'Hassan Muhamud': 'CB',
            'Derrick Paul': 'LW',
            'Emmanuel Anyama': 'CF',
            'Abubaker Mayanja': 'CF',
            'Isa Mibiru': 'LB',
            'Julius Poloto': 'MD',
            'Peter Magambo': 'DM',
        }
        mask = df['player_position'] == 'None'
        df.loc[mask, 'player_position'] = df.loc[mask, 'p_name'].map(missing_positions).fillna('None')

    # Step 4: Ensure mandatory columns
    if "club_for" not in df.columns:
        df["club_for"] = df["player_club_"]

    if "club_against" not in df.columns:
        df["club_against"] = pd.NA

    # Step 5: Clean extracted text fields BUT PRESERVE split_name standardization
    df = text_cleaning.apply_text_cleaning_to_columns(df, columns=[c for c in df.columns if c != 'split_name'])

    # Step 6: Normalize positions
    mapping = league_definitions.POSITION_MAPPING
    aliases = league_definitions.POSITION_ALIASES
    df = text_cleaning.normalize_positions(
        df, mapping, aliases=aliases, target_column="general_position"
    )

    if df["general_position"].isnull().any():
        unmapped = df.loc[df["general_position"].isnull(), "player_position"].unique()
        logger.warning(
            f"LOGICAL ERROR: Unmapped player positions found: {unmapped}. "
            "These players will be excluded from position-specific analysis."
        )

    return df


def normalize_clubs(df: pd.DataFrame, league: str, season: str ) -> pd.DataFrame:
    """Normalize the `club_for` and `club_against` columns to canonical names."""
    df = df.copy()
    clubs = league_definitions.get_league_clubs(league, season)
    
    corrections = None
    if league.lower() == "fwsl":
        corrections = constants.CLUB_CORRECTIONS_FWSL
    elif league.lower() == "upl":
        corrections = constants.CLUB_CORRECTIONS_UPL

    def resolve_club(name, club_list, corrections_map):
        if pd.isna(name):
            return None

        match = text_cleaning.best_match(name, club_list, min_score=0.5, return_original=False)
        if match:
            return match

        if corrections_map and name in corrections_map:
            return corrections_map[name]

        return None

    # Strictly fix club_for (drop invalid rows)
    if "club_for" in df.columns:
        df["club_for_clean"] = df["club_for"].astype(str).apply(
            lambda x: resolve_club(x, clubs, corrections)
        )

        dropped_mask = df["club_for_clean"].isnull()
        if dropped_mask.any():
            dropped_names = df.loc[dropped_mask, "club_for"].unique()
            count = dropped_mask.sum()
            logger.warning(
                f"DATA EXCLUSION: {count} rows with invalid 'club_for' names: {dropped_names}. "
                "These do not match official list and will be excluded (no close match found)."
            )
            df = df[~dropped_mask].reset_index(drop=True)

        df["club_for"] = df["club_for_clean"]
        df.drop(columns=["club_for_clean"], inplace=True)

    # Leniently fix club_against (keep original if no match)
    if "club_against" in df.columns:
        df["club_against"] = df["club_against"].astype(str).apply(
            lambda x: text_cleaning.best_match(x, clubs, min_score=0.5, return_original=True)
        )
        if corrections:
            df["club_against"] = df["club_against"].replace(corrections)

    return df


def filter_gk(df: pd.DataFrame, exclude: bool = True) -> pd.DataFrame:
    """Filter out goalkeepers if exclude=True."""
    df = df.copy()
    if "player_position" in df.columns:
        if exclude:
            df = df[df['player_position'].str.lower() != 'gk']
    return df


def remove_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows."""
    df = df.copy()
    initial_count = len(df)
    duplicate_rows = df.duplicated()
    df = df[~duplicate_rows].reset_index(drop=True)
    
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.info(f"Removed {dropped} duplicate rows.")
    
    return df


def drop_sparse_columns(df: pd.DataFrame, threshold: float = None) -> pd.DataFrame:
    """Drop columns that are mostly zeros or NA."""
    df = df.copy()
    if threshold is None:
        threshold = constants.SPARSE_COLUMN_THRESHOLD

    must_keep = set(constants.CORE_METRICS) | set(constants.COMPUTED_METRICS.keys())

    def prop_zeros(s: pd.Series) -> float:
        if s.dtype == "O":
            return 0.0
        return (s.fillna(0) == 0).mean()

    keep = [
        c for c in df.columns
        if c in must_keep or prop_zeros(df[c]) < threshold
    ]
    
    dropped_count = len(df.columns) - len(keep)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} sparse columns (>95% zeros).")
    
    return df[keep]


def remove_outliers(
    df: pd.DataFrame, columns: Optional[List[str]] = None, iqr_mult: float = None
) -> pd.DataFrame:
    """Remove rows that are outliers in specified columns using IQR."""
    df = df.copy()
    if columns is None:
        columns = ["distance_km", "duration"]
    if iqr_mult is None:
        iqr_mult = constants.OUTLIER_IQR_MULTIPLIER

    initial_count = len(df)
    mask = pd.Series(True, index=df.index)
    
    for col in columns:
        if col not in df.columns:
            continue
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - iqr_mult * iqr
        upper = q3 + iqr_mult * iqr
        mask &= df[col].between(lower, upper) | df[col].isna()

    df = df.loc[mask].reset_index(drop=True)
    dropped = initial_count - len(df)
    
    if dropped > 0:
        logger.info(f"Removed {dropped} outlier rows (IQR method).")
    
    return df


def aggregate_halves(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge first and second half rows into single player-match record.
    
    This function performs a complex outer join on match session data to combine 
    half-by-half metrics into a single match-level record per player.

    Workflow:
    1. Filter the dataset into 1st Half, 2nd Half, and 'All' session types.
    2. Perform an outer join on core keys (player, matchday, etc.) using constants.get_merge_keys().
    3. Aggregate metrics by summing (e.g., total distance) or taking the maximum (e.g., top speed).
    4. Auto-discover and sum remaining numeric columns (e.g., speed zone data) to ensure no data loss.
    5. Fall back to 'All' session data if half-by-half splits are missing.

    **CRITICAL**: 
    - split_name must be standardized BEFORE calling this function.
    - Uses constants.AGGREGATE_SUM_METRICS and AGGREGATE_MAX_METRICS for explicit rules.
    
    Args:
        df: Dataframe with half-split rows.

    Returns:
        Dataframe with one row per player-match.
    """
    df = df.copy()

    # Identify split column (should be 'split_name' from Catapult)
    split_col = next((c for c in df.columns if c in ['split_name', 'period_name']), None)
    
    if not split_col or 'split_name' not in df.columns:
        logger.warning("No 'split_name' column found. Skipping half aggregation.")
        return df

    # Filter to ONLY first and second halves (after standardization)
    # Valid values after standardization: '1st Half', '2nd Half'
    half1_df = df[df['split_name'] == '1st Half'].copy()
    half2_df = df[df['split_name'] == '2nd Half'].copy()
    all_df = df[df['split_name'] == 'All'].copy()

    logger.info(
        f"Aggregating halves: {len(half1_df)} H1 rows, "
        f"{len(half2_df)} H2 rows, {len(all_df)} All rows"
    )

    # If we have half data, use it; otherwise fall back to 'All'
    if len(half1_df) > 0 and len(half2_df) > 0:
        # Use half-based merging (like notebooks)
        merge_keys = constants.get_merge_keys()
        
        # Check that all merge keys exist
        missing_h1 = [k for k in merge_keys if k not in half1_df.columns]
        missing_h2 = [k for k in merge_keys if k not in half2_df.columns]
        
        if missing_h1:
            logger.error(f"H1 data missing columns: {missing_h1}. Falling back to 'All' split.")
            return all_df.drop('split_name', axis=1).reset_index(drop=True) if len(all_df) > 0 else df
        if missing_h2:
            logger.error(f"H2 data missing columns: {missing_h2}. Falling back to 'All' split.")
            return all_df.drop('split_name', axis=1).reset_index(drop=True) if len(all_df) > 0 else df
        
        # Drop split_name before rename to avoid duplication
        half1_df = half1_df.drop('split_name', axis=1)
        half2_df = half2_df.drop('split_name', axis=1)
        if len(all_df) > 0:
            all_df = all_df.drop('split_name', axis=1)

        # Rename columns for merge
        half1_df_rn = half1_df.rename(columns=lambda x: x + '_H1' if x not in merge_keys else x)
        half2_df_rn = half2_df.rename(columns=lambda x: x + '_H2' if x not in merge_keys else x)
        if len(all_df) > 0:
            all_df_rn = all_df.rename(columns=lambda x: x + '_ALL' if x not in merge_keys else x)
        
        # Merge
        df_merged = pd.merge(half1_df_rn, half2_df_rn, on=merge_keys, how='outer')
        if len(all_df) > 0:
            df_merged = pd.merge(df_merged, all_df_rn, on=merge_keys, how='outer')

        # Aggregate using constants
        df_combined = df_merged[merge_keys].copy()
        
        # --- Explicitly listed sum/max metrics ---
        sum_cols = [c for c in constants.AGGREGATE_SUM_METRICS if (c + '_H1') in df_merged.columns or (c + '_H2') in df_merged.columns]
        max_cols = [c for c in constants.AGGREGATE_MAX_METRICS if (c + '_H1') in df_merged.columns or (c + '_H2') in df_merged.columns]
        

        for col in sum_cols:
            h1 = f"{col}_H1"
            h2 = f"{col}_H2"
            
            # Robust numeric conversion before addition
            h1_vals = pd.to_numeric(df_merged[h1], errors='coerce').fillna(0) if h1 in df_merged.columns else 0
            h2_vals = pd.to_numeric(df_merged[h2], errors='coerce').fillna(0) if h2 in df_merged.columns else 0
            df_combined[col] = h1_vals + h2_vals

        for col in max_cols:
            h1 = f"{col}_H1"
            h2 = f"{col}_H2"
            cols_present = [c for c in [h1, h2] if c in df_merged.columns]
            if cols_present:
                # Ensure they are numeric before max
                for c in cols_present:
                    df_merged[c] = pd.to_numeric(df_merged[c], errors='coerce').fillna(0)
                df_combined[col] = df_merged[cols_present].max(axis=1)

        # --- Auto-discover remaining numeric columns not yet handled ---
        # This catches zone columns (acceleration/deceleration counts, speed zone 
        # columns etc.) that might vary by league
        all_h1_cols = [c for c in df_merged.columns if c.endswith("_H1")]
        extra_sum_count = 0
        for h1_col in all_h1_cols:
            col_root = h1_col[:-3]
            if col_root in df_combined.columns:
                continue # Already handled
            
            h2_col = f"{col_root}_H2"
            if h2_col in df_merged.columns:
                # Robustly attempt numeric addition
                try:
                    h1_vals = pd.to_numeric(df_merged[h1_col], errors='coerce').fillna(0)
                    h2_vals = pd.to_numeric(df_merged[h2_col], errors='coerce').fillna(0)
                    df_combined[col_root] = h1_vals + h2_vals
                    extra_sum_count += 1
                except Exception as e:
                    logger.debug(f"Skipping auto-aggregation for non-numeric column '{col_root}': {e}")
        
        if extra_sum_count > 0:
            logger.info(f"Auto-aggregated {extra_sum_count} additional numeric columns (zone data, etc.) by summing halves.")

        # Handle special cases (from notebooks)
        if 'distance_per_min_mmin' in df_combined.columns and 'duration' in df_combined.columns:
            dur_nonzero = df_combined["duration"].replace(0, np.nan)
            df_combined['distance_per_min_mmin'] = (df_combined['distance_km'] * 1000) / dur_nonzero

        if 'work_ratio_ALL' in df_merged.columns:
            df_combined['work_ratio'] = df_merged['work_ratio_ALL']

        if 'power_score_wkg_ALL' in df_merged.columns:
            df_combined['power_score_wkg'] = df_merged['power_score_wkg_ALL']

        return df_combined.reset_index(drop=True)
    
    elif len(all_df) > 0:
        # Fall back to 'All' split (no half data)
        logger.warning("No half data found. Using 'All' split rows instead.")
        return all_df.drop('split_name', axis=1).reset_index(drop=True)
    
    else:
        # No useful split data
        logger.warning("No valid split data found. Returning data as-is.")
        return df


def filter_active_sessions(
    df: pd.DataFrame, min_distance: float = None, min_duration: float = None
) -> pd.DataFrame:
    """Filter out sessions that are too short or have very low distance."""
    df = df.copy()
    if min_distance is None:
        min_distance = constants.MIN_SESSION_DISTANCE_KM
    if min_duration is None:
        min_duration = constants.MIN_SESSION_DURATION_MINUTES

    initial_count = len(df)
    mask = pd.Series(True, index=df.index)
    
    if "distance_km" in df.columns:
        mask &= df["distance_km"] >= min_distance
    if "duration" in df.columns:
        mask &= df["duration"] >= min_duration

    df = df.loc[mask].reset_index(drop=True)
    dropped = initial_count - len(df)
    
    if dropped > 0:
        logger.info(
            f"Filtered active sessions: removed {dropped} rows "
            f"(distance < {min_distance} km or duration < {min_duration} min)"
        )
    
    return df


def compute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute metrics that are derived from raw data columns.
    
    Includes computation of:
    - Total accelerations/decelerations (summed from speed zones).
    - Total actions (accel + decel).
    - Rate metrics (accel/min, decel/min, distance/min).
    - Physical Efficiency Score (Total Actions / Distance).

    **IMPORTANT**: Should be called AFTER aggregating halves to ensure rates 
    are calculated based on total match duration.

    Args:
        df: Input dataframe with aggregated numeric columns.

    Returns:
        Dataframe with added derived metric columns.
    """
    df = df.copy()

    # Sum acceleration/dec columns
    acc_cols = constants.ACCELERATION_ZONE_COLUMNS
    dec_cols = constants.DECELERATION_ZONE_COLUMNS

    existing_acc = [c for c in acc_cols if c in df.columns]
    existing_dec = [c for c in dec_cols if c in df.columns]

    if not existing_acc:
        existing_acc = [
            c for c in df.columns 
            if 'acceleration' in c.lower() and 'zone' in c.lower() 
            and 'count' in c.lower() and 'total' not in c.lower()
        ]
    if not existing_dec:
        existing_dec = [
            c for c in df.columns 
            if 'deceleration' in c.lower() and 'zone' in c.lower() 
            and 'count' in c.lower() and 'total' not in c.lower()
        ]

    if existing_acc:
        df["total_accelerations"] = df[existing_acc].sum(axis=1)
    else:
        df["total_accelerations"] = 0

    if existing_dec:
        df["total_decelerations"] = df[existing_dec].sum(axis=1)
    else:
        df["total_decelerations"] = 0

    # Total actions = accelerations + decelerations
    df["total_actions"] = df["total_accelerations"] + df["total_decelerations"]

    # Rate metrics (computed last, AFTER aggregation)
    if "duration" in df.columns:
        dur_nonzero = df["duration"].replace(0, np.nan)
        df["acc_counts_per_min"] = df["total_accelerations"] / dur_nonzero
        df["dec_counts_per_min"] = df["total_decelerations"] / dur_nonzero
        
        if "distance_km" in df.columns:
            df["distance_per_min_mmin"] = (df["distance_km"] * 1000) / dur_nonzero
    else:
        df["acc_counts_per_min"] = np.nan
        df["dec_counts_per_min"] = np.nan
        df["distance_per_min_mmin"] = np.nan

    return df


def save_processed(df: pd.DataFrame, league: str, out_dir: str = None) -> str:
    """Save processed dataframe to processed data directory and return path."""
    if out_dir is None:
        out_dir = constants.PROCESSED_DATA_DIR
    os.makedirs(out_dir, exist_ok=True)

    fname = (
        constants.FWSL_PROCESSED_OUTPUT
        if league.lower() == "fwsl"
        else constants.UPL_PROCESSED_OUTPUT
    )
    path = os.path.join(out_dir, fname)
    df.to_csv(path, index=False)
    logger.info(f"Saved processed data to {path}")
    return path


def clean_pipeline(
    raw_path: Optional[str] = None, 
    league: str = "fwsl", 
    season: str = "2025/2026",
    include_gk: bool = False
) -> Tuple[pd.DataFrame, str]:
    """
    Run the full cleaning pipeline for a given league.
    
    **CRITICAL ORDER** (must aggregate BEFORE filtering):
    
    1. Load & standardize columns
    2. Normalize duration (seconds → minutes)
    3. Filter match sessions
    4. Standardize split_name values (MUST be before other text cleaning)
    5. Clean ALL text columns (EXCEPT split_name which is already standardized)
    6. Extract session info
    7. Validate matchday logic
    8. Extract player columns (with position handling)
    9. Normalize clubs
    10. Filter out goalkeepers
    11. Remove duplicate rows
    12. Drop sparse columns
    13. **Aggregate halves (BEFORE filtering - critical!)**
    14. Filter active sessions (with aggregated data)
    15. Remove outliers (with aggregated data)
    16. Compute derived metrics (AFTER aggregation)
    17. Save
    
    Returns:
        Tuple of (cleaned_dataframe, output_path)
    """
    logger.info(f"Starting clean_pipeline for {league.upper()}")
    
    # 1. Load
    df = load_raw_data(raw_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # 2. Standardize
    df = standardize_columns(df)
    
    # Note: Numeric type coercion now happens defensively inside aggregate_halves
    # via pd.to_numeric(errors='coerce'), preventing TypeErrors without corrupting text columns.

    # 3. Normalize duration
    df = normalize_duration_to_minutes(
        df,
        duration_col="duration",
        raw_unit="seconds",
        keep_raw_seconds=True,
        heuristic_if_unknown=True,
    )

    # 3.5. Extract training data
    df = extract_and_save_training_data(df, league=league)

    # 4. Filter session rows
    df = filter_match_sessions(df, league)

    # 5. Clean ALL text columns EXCEPT split_name (must stay pristine for standardization)
    # Standardize split_name FIRST (before other text cleaning)
    df = standardize_split_names(df)

    # 6. Now clean all OTHER text columns
    df = text_cleaning.apply_text_cleaning_to_columns(df, columns=[c for c in df.columns if c != 'split_name'])

    # 7. Extract session info
    df = extract_session_info(df)

    # 8. Validate matchday logic
    df = validate_matchday_logic(df, league)

    # 9. Extract player columns
    df = extract_player_columns(df, league=league)

    # 10. Normalize clubs
    df = normalize_clubs(df, league, season)

    # 11. Filter goalkeepers
    if not include_gk:
        df = filter_gk(df, exclude=True)

    # 12. Remove duplicates ✓
    df = remove_duplicate_rows(df)

    # 13. Drop sparse columns ✓
    df = drop_sparse_columns(df)

    # 14. **CRITICAL: Aggregate halves BEFORE filtering** ✓
    # Must happen before active session/outlier filtering because individual halves
    # may not meet minimum duration/distance, but aggregated match data will
    df = aggregate_halves(df)

    # 15. Filter active sessions (now with aggregated full-match data)
    df = filter_active_sessions(df)

    # 16. Remove outliers (now with aggregated full-match data)
    df = remove_outliers(df)

    # 17. Compute derived metrics ✓ (CRITICAL: after aggregation)
    df = compute_derived_metrics(df)

    logger.info(f"Pipeline complete. Output: {len(df)} rows, {len(df.columns)} columns")

    # 18. Save
    out_path = save_processed(df, league)

    return df, out_path