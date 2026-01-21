"""
Unified data cleaning module for Match-Analysis.

Provides a single entry point for cleaning raw Catapult exports for the
FWSL and UPL leagues. Functions are parameterized by league and reuse
utilities and configuration from `src.utils` and `src.config`.

The goal of this module is to encapsulate the repeated cleaning pipeline
found in `cleaning_FWSL_2025.ipynb` and `cleaning_UPL_2025.ipynb` so the
notebooks can become lightweight orchestration layers that call into
this module.
"""

from typing import List, Optional, Tuple
import os
import re
import pandas as pd
import numpy as np

from ..config import constants, league_definitions
from ..utils import text_cleaning


def load_raw_data(path: str = None) -> pd.DataFrame:
    """Load raw CSV data. Defaults to `RAW_DATA_FILE` in constants."""
    if path is None:
        path = constants.RAW_DATA_FILE
    return pd.read_csv(path)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names: lowercase, remove special characters, underscores.

    Matches exactly the logic from the project's cleaning notebooks.
    """
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[\/\(\)\-]", "", regex=True)
    )
    return df


def normalize_duration_to_minutes(
    df: pd.DataFrame,
    duration_col: str = "duration",
    raw_unit: str = "seconds",
    keep_raw_seconds: bool = True,
    heuristic_if_unknown: bool = True,
) -> pd.DataFrame:
    """Normalize duration values to minutes.

    The Catapult raw exports often store `duration` in **seconds**, while the rest of
    this codebase assumes processed data uses **minutes**.

    Strategy:
    - If `raw_unit` is "seconds": convert to minutes.
    - If `raw_unit` is "minutes": leave as-is.
    - If `raw_unit` is "auto"/unknown and `heuristic_if_unknown` is True:
      infer seconds vs minutes using typical match duration ranges.

    If `keep_raw_seconds` is True and conversion occurs, the original values are
    preserved in `duration_seconds_raw`.
    """

    df = df.copy()
    if duration_col not in df.columns:
        return df

    # Ensure numeric
    duration = pd.to_numeric(df[duration_col], errors="coerce")

    unit = (raw_unit or "auto").strip().lower()

    # Heuristic: if durations look too large for minutes, assume seconds.
    # Typical match sessions are < 240 minutes; if median is > 300, it's almost
    # certainly seconds.
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
        # Unknown unit; keep numeric but do not transform.
        df[duration_col] = duration

    return df


def filter_match_sessions(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """Keep only rows that look like match sessions for the given league.

    Uses `session_pattern` from `league_definitions`.
    """
    df = df.copy()
    pattern = league_definitions.get_league_session_pattern(league)
    if "session_title" in df.columns:
        mask = df["session_title"].astype(str).str.match(pattern, na=False, case=False)
        return df.loc[mask].reset_index(drop=True)
    # If no session_title column, just return input
    return df


def extract_player_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts player name, club and position from the player string.

    Expects a column named `player_name` in the raw data that follows the
    'Name - Club - Position' pattern used across the notebooks.

    Handles both `player_name` and `p_name` column names for compatibility.
    """
    df = df.copy()

    # Handle column name variations (p_name -> player_name)
    if "p_name" in df.columns and "player_name" not in df.columns:
        df = df.rename(columns={"p_name": "player_name"})

    if "player_name" not in df.columns:
        raise KeyError("player_name column required for player extraction")

    cleaned_df, player_cols = text_cleaning.extract_player_info(df, "player_name")
    for col in player_cols.columns:
        cleaned_df[col] = player_cols[col]

    # Standardize text fields
    cleaned_df = text_cleaning.apply_text_cleaning_to_columns(
        cleaned_df, ["p_name", "player_club_", "player_position"]
    )
    
    # Ensure mandatory join columns are present
    # player_club_ and club_for are both kept as per MERGE_KEYS
    if "club_for" not in cleaned_df.columns:
        cleaned_df["club_for"] = cleaned_df["player_club_"]

    # Ensure club_against exists (needed for normalization/tables even if empty)
    if "club_against" not in cleaned_df.columns:
        cleaned_df["club_against"] = pd.NA

    # Normalize positions (general_position)
    mapping = league_definitions.POSITION_MAPPING
    aliases = league_definitions.POSITION_ALIASES
    cleaned_df = text_cleaning.normalize_positions(
        cleaned_df, mapping, aliases=aliases, target_column="general_position"
    )

    return cleaned_df


def extract_session_info(df: pd.DataFrame) -> pd.DataFrame:
    """Extract matchday, teams, location, league, and result from session_title.

    Standard format: 'Md1-Kcca Fc-Ura Fc-Home-League-Win'
    """
    if "session_title" not in df.columns:
        return df

    df = df.copy()

    # 1. Clean the session title
    df["session_title"] = (
        df["session_title"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.+", "", regex=True)  # remove dots like "F.C."
        .str.replace(r"\s*-\s*", "-", regex=True)  # normalize spacing around hyphens
        .str.replace(r"\s+", " ", regex=True)  # reduce internal whitespace
        .str.title()  # ensure proper capitalization
    )

    # 2. Extract session components: 6 fields + ignore trailing data
    session_regex = re.compile(
        r"^(Md\d+)-"  # Matchday
        r"(.+?)-"  # Club For
        r"(.+?)-"  # Club Against
        r"(.+?)"  # Part 1: location/league/result
        r"[-\s]+(.+?)"  # Part 2: location/league/result
        r"[-\s]+(.+?)"  # Part 3: location/league/result
        r"(?:\s|$)",  # Ignore trailing info
        re.IGNORECASE,
    )

    extracted = df["session_title"].str.extract(session_regex)
    if extracted.isnull().all().all():
        return df

    # Assign temporary column names
    extracted.columns = [
        "match_day",
        "ex_club_for",
        "ex_club_against",
        "part1",
        "part2",
        "part3",
    ]

    # Define sets to identify
    location_set = {"Home", "Away"}
    league_set = {"League", "Cup"}
    result_set = {"Win", "Loss", "Draw"}

    # Assign actual values to correct columns
    extracted["location"] = None
    extracted["league"] = None
    extracted["result"] = None

    for i, row in extracted.iterrows():
        for val in [row["part1"], row["part2"], row["part3"]]:
            if pd.isna(val):
                continue
            val_clean = val.strip().title()
            if val_clean in location_set:
                extracted.at[i, "location"] = val_clean
            elif val_clean in league_set:
                extracted.at[i, "league"] = val_clean
            elif val_clean in result_set:
                extracted.at[i, "result"] = val_clean

    # Keep only fully matched rows for filtering
    valid_mask = extracted[["location", "league", "result"]].notnull().all(axis=1)
    df = df.loc[valid_mask].reset_index(drop=True)
    extracted = extracted.loc[valid_mask].reset_index(drop=True)

    # Add extracted columns to df
    # Notebook extracts club_for and club_against from session title too
    df["match_day"] = extracted["match_day"]
    df["club_for"] = extracted["ex_club_for"]
    df["club_against"] = extracted["ex_club_against"]
    df["location"] = extracted["location"]
    df["result"] = extracted["result"]

    return df


def normalize_clubs(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """Normalize the `club_for` and `club_against` columns to canonical names."""
    df = df.copy()
    clubs = league_definitions.get_league_clubs(league)
    corrections = None
    if league.lower() == "fwsl":
        corrections = constants.CLUB_CORRECTIONS_FWSL
    elif league.lower() == "upl":
        corrections = constants.CLUB_CORRECTIONS_UPL

    df = text_cleaning.normalize_club_names(
        df, ["club_for", "club_against"], clubs, corrections=corrections
    )
    return df


def compute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute metrics that are present in the notebooks but derived.

    Examples: total_accelerations, total_decelerations, acc/dec per minute.
    """
    df = df.copy()

    # Sum acceleration/dec columns if present
    acc_cols = constants.ACCELERATION_ZONE_COLUMNS
    dec_cols = constants.DECELERATION_ZONE_COLUMNS

    existing_acc = [c for c in acc_cols if c in df.columns]
    existing_dec = [c for c in dec_cols if c in df.columns]

    if existing_acc:
        df["total_accelerations"] = df[existing_acc].sum(axis=1)
    else:
        df["total_accelerations"] = 0

    if existing_dec:
        df["total_decelerations"] = df[existing_dec].sum(axis=1)
    else:
        df["total_decelerations"] = 0

    # Derived rate metrics
    if "duration" in df.columns:
        dur_nonzero = df["duration"].replace(0, np.nan)
        df["acc_counts_per_min"] = df["total_accelerations"] / dur_nonzero
        df["dec_counts_per_min"] = df["total_decelerations"] / dur_nonzero
        
        if "distance_km" in df.columns:
            # distance_km * 1000 / duration -> m/min
            df["distance_per_min_mmin"] = (df["distance_km"] * 1000) / dur_nonzero
    else:
        df["acc_counts_per_min"] = np.nan
        df["dec_counts_per_min"] = np.nan
        df["distance_per_min_mmin"] = np.nan

    return df


def drop_sparse_columns(df: pd.DataFrame, threshold: float = None) -> pd.DataFrame:
    """Drop columns that are mostly zeros or NA based on `SPARSE_COLUMN_THRESHOLD`.

    Note: Always keeps columns listed in `constants.CORE_METRICS` or
    `constants.COMPUTED_METRICS` to avoid breaking downstream analysis.
    """
    df = df.copy()
    if threshold is None:
        threshold = constants.SPARSE_COLUMN_THRESHOLD

    # Metrics we must keep
    must_keep = set(constants.CORE_METRICS) | set(constants.COMPUTED_METRICS.keys())

    # Columns where proportion of zeros is greater than threshold
    def prop_zeros(s: pd.Series) -> float:
        if s.dtype == "O":
            return 0.0
        return (s.fillna(0) == 0).mean()

    keep = [
        c
        for c in df.columns
        if c in must_keep or prop_zeros(df[c]) < threshold
    ]
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

    return df.loc[mask].reset_index(drop=True)


def aggregate_halves(df: pd.DataFrame) -> pd.DataFrame:
    """Merge first and second half rows into a single player-match record.

    Uses `MERGE_KEYS` and `AGGREGATE_SUM_METRICS` / `AGGREGATE_MAX_METRICS` from constants.
    """
    df = df.copy()

    merge_keys = constants.get_merge_keys()

    # Determine aggregate columns
    sum_cols = [c for c in constants.AGGREGATE_SUM_METRICS if c in df.columns]
    max_cols = [c for c in constants.AGGREGATE_MAX_METRICS if c in df.columns]

    agg_dict = {c: "sum" for c in sum_cols}
    agg_dict.update({c: "max" for c in max_cols})

    grouped = df.groupby(merge_keys).agg(agg_dict).reset_index()

    # Copy non-aggregated columns from the first occurrence
    # (e.g., p_name, player_club_ should already be in merge keys)
    return grouped


def filter_active_sessions(
    df: pd.DataFrame, min_distance: float = None, min_duration: float = None
) -> pd.DataFrame:
    """Filter out sessions that are too short or have very low distance."""
    df = df.copy()
    if min_distance is None:
        min_distance = constants.MIN_SESSION_DISTANCE_KM
    if min_duration is None:
        min_duration = constants.MIN_SESSION_DURATION_MINUTES

    mask = pd.Series(True, index=df.index)
    if "distance_km" in df.columns:
        mask &= df["distance_km"] >= min_distance
    if "duration" in df.columns:
        mask &= df["duration"] >= min_duration

    return df.loc[mask].reset_index(drop=True)


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
    return path


def clean_pipeline(
    raw_path: Optional[str] = None, league: str = "fwsl"
) -> Tuple[pd.DataFrame, str]:
    """Run the full cleaning pipeline for a given league.

    Returns the cleaned dataframe and the path where it was saved.

    Notes:
        - The raw Catapult export stores `duration` in seconds.
        - This pipeline standardizes processed outputs to `duration` in minutes.
    """
    # Load
    df = load_raw_data(raw_path)

    # Standardize
    df = standardize_columns(df)

    # Normalize units (seconds -> minutes) before any filtering/derived metrics
    df = normalize_duration_to_minutes(
        df,
        duration_col="duration",
        raw_unit="seconds",
        keep_raw_seconds=True,
        heuristic_if_unknown=True,
    )

    # Filter session rows
    df = filter_match_sessions(df, league)

    # Extract session info (match_day, location, result)
    df = extract_session_info(df)

    # Extract player columns (p_name, player_club_, player_position, club_for)
    df = extract_player_columns(df)

    # Normalize clubs
    df = normalize_clubs(df, league)

    # Compute derived metrics
    df = compute_derived_metrics(df)

    # Drop sparse columns
    df = drop_sparse_columns(df)

    # Filter active sessions
    df = filter_active_sessions(df)

    # Remove outliers
    df = remove_outliers(df)

    # Aggregate halves
    df = aggregate_halves(df)

    # Re-compute derived metrics (especially rates) after aggregation
    df = compute_derived_metrics(df)

    # Save
    out_path = save_processed(df, league)

    return df, out_path
