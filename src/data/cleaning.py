"""
Unified data cleaning module for Match-Analysis.

Rejection Audit
---------------
Every filter step captures the dropped rows in a shared ``RejectionLog``.
At the end of ``clean_pipeline`` the log is flushed to
``logs/rejected/<run_id>/`` as individual CSVs, one per rejection reason,
plus a combined ``all_rejections.csv``.  A compact summary table is also
printed to the terminal.

Training Data Output
--------------------
Training rows are saved to::

    data/training/<season>/<league>/<LEAGUE>_<season>_training_data.csv

e.g.  data/training/2024-25/UPL/UPL_2024-25_training_data.csv
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


# ──────────────────────────────────────────────────────────────────────────────
# Rejection Audit
# ──────────────────────────────────────────────────────────────────────────────

class RejectionLog:
    """
    Accumulates rows dropped at each pipeline step so they can be written
    to the audit folder for investigation.
    """

    def __init__(self):
        self._entries: List[pd.DataFrame] = []

    def record(self, df: pd.DataFrame, step: str, reason: str) -> None:
        """
        Attach ``step`` and ``reason`` columns to *df* and store it.
        Does nothing if *df* is empty.
        """
        if df is None or df.empty:
            return
        tagged = df.copy()
        tagged["_rejection_step"]   = step
        tagged["_rejection_reason"] = reason
        self._entries.append(tagged)

    def flush(self, out_dir: str, run_id: str = "") -> None:
        """
        Write all accumulated rejections to *out_dir*.

        Files written:
          • all_rejections.csv                – every dropped row
          • <step>__<reason>.csv              – one file per unique (step, reason)

        A compact summary is printed to the terminal.
        """
        if not self._entries:
            logger.info("No rejection data to write.")
            return

        os.makedirs(out_dir, exist_ok=True)
        combined = pd.concat(self._entries, ignore_index=True)

        # ── Combined file ─────────────────────────────────────────────────────
        combined_path = os.path.join(out_dir, "all_rejections.csv")
        combined.to_csv(combined_path, index=False)

        # ── Per-step/reason files ─────────────────────────────────────────────
        for (step, reason), group in combined.groupby(
            ["_rejection_step", "_rejection_reason"], sort=False
        ):
            safe_step   = re.sub(r"[^\w]", "_", step)
            safe_reason = re.sub(r"[^\w]", "_", reason)[:60]
            fname = f"{safe_step}__{safe_reason}.csv"
            fpath = os.path.join(out_dir, fname)
            group.to_csv(fpath, index=False)

        # ── Terminal summary ──────────────────────────────────────────────────
        self._print_summary(combined, out_dir)

    def _print_summary(self, combined: pd.DataFrame, out_dir: str) -> None:
        """Print a colour-coded rejection summary table."""
        try:
            from ..utils.console import Console, _A, _paint
        except Exception:
            Console = None

        total_dropped = len(combined)
        summary = (
            combined
            .groupby(["_rejection_step", "_rejection_reason"])
            .size()
            .reset_index(name="rows_dropped")
            .sort_values("rows_dropped", ascending=False)
        )

        if Console:
            from ..utils.console import _paint, _A, _BOX
            print()
            print(_paint(_A.BOLD, _A.BYELLOW, f"  {_BOX['sTL']}{_BOX['h']} Data Rejection Audit  ({total_dropped:,} rows total) " + _BOX['h'] * 22))
            print(_paint(_A.BYELLOW, f"  {_BOX['v']}"))
            hdr = f"  {_BOX['v']}  {'Step':<28}  {'Reason':<28}  {'Rows':>6}"
            print(_paint(_A.DIM, _A.WHITE, hdr))
            print(_paint(_A.BYELLOW, f"  {_BOX['v']}  " + _BOX['h'] * 70))
            for _, row in summary.iterrows():
                step_str   = str(row['_rejection_step'])[:28]
                reason_str = str(row['_rejection_reason'])[:28]
                count      = int(row['rows_dropped'])
                bar_char   = "█" if Console._is_utf8() else "#"
                bar        = bar_char * min(count // max(total_dropped // 20, 1), 20)
                line = f"  {_BOX['v']}  {step_str:<28}  {reason_str:<28}  {count:>6,}  {bar}"
                colour = _A.BRED if count > total_dropped * 0.2 else _A.BYELLOW
                print(_paint(colour, line))
            print(_paint(_A.BYELLOW, f"  {_BOX['v']}"))
            print(_paint(_A.BOLD, _A.BYELLOW, f"  {_BOX['sBL']}{_BOX['h']} Saved to: {out_dir}"))
            print()
        else:
            print(f"\n=== Data Rejection Audit ({total_dropped} rows) ===")
            print(summary.to_string(index=False))
            print(f"Saved to: {out_dir}\n")


# ──────────────────────────────────────────────────────────────────────────────
# Filter helpers – each returns (kept_df, dropped_df)
# ──────────────────────────────────────────────────────────────────────────────

def filter_by_position(
    df: pd.DataFrame,
    positions: Optional[List[str]] = None,
    general_position: bool = True,
) -> pd.DataFrame:
    """
    Filter dataframe to include only specified positions.

    Args:
        df: Input dataframe with position columns
        positions: List of position codes/names to keep
        general_position: If True, filter by 'general_position'; else by 'player_position'

    Returns:
        Filtered dataframe containing only specified positions
    """
    if positions is None or len(positions) == 0:
        return df

    df = df.copy()
    position_col = "general_position" if general_position else "player_position"

    if position_col not in df.columns:
        logger.warning(f"Column '{position_col}' not found. Returning unfiltered data.")
        return df

    positions_lower = [p.lower() for p in positions]
    mask = df[position_col].astype(str).str.lower().isin(positions_lower)
    df_filtered = df[mask].reset_index(drop=True)
    dropped = len(df) - len(df_filtered)
    if dropped > 0:
        logger.info(f"Filtered by position: removed {dropped} rows not matching {positions}")

    return df_filtered


def load_raw_data(path: str = None) -> pd.DataFrame:
    """Load raw CSV data."""
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
        mx  = duration.dropna().max()    if duration.notna().any() else np.nan
        if (pd.notna(med) and med > 300) or (pd.notna(mx) and mx > 240):
            unit = "seconds"
        else:
            unit = "minutes"

    if unit == "seconds":
        if keep_raw_seconds and "duration_seconds_raw" not in df.columns:
            df["duration_seconds_raw"] = duration
        df[duration_col] = duration / 60.0
    else:
        df[duration_col] = duration

    return df


def extract_and_save_training_data(
    df: pd.DataFrame,
    league: str,
    season: str = "",
    out_base_dir: str = None,
    rejection_log: "RejectionLog | None" = None,
) -> pd.DataFrame:
    """
    Extract training data, save it to a season-organised folder, and
    return a dataframe containing only game/game-training rows.

    Output path:
        data/training/<season>/<league>/<LEAGUE>_<season>_training_data.csv

    e.g.  data/training/2024-25/UPL/UPL_2024-25_training_data.csv
    """
    df = df.copy()

    tag_cols = [c for c in df.columns if c.lower() in ("tags", "tag")]
    if not tag_cols:
        logger.warning("No 'tags' or 'tag' column found. Skipping training data extraction.")
        return df

    tag_col = tag_cols[0]
    df["_clean_tag"] = df[tag_col].astype(str).str.strip().str.lower()

    training_df = df[df["_clean_tag"] == "training"].drop(columns=["_clean_tag"]).copy()

    if len(training_df) > 0:
        # Build a season-organised path, e.g. data/training/2024-25/UPL/
        season_str = season.replace("/", "-") if season else "unknown_season"
        league_str = league.upper()

        if out_base_dir is None:
            out_base_dir = "data/training"

        league_dir = os.path.join(out_base_dir, season_str, league_str)
        os.makedirs(league_dir, exist_ok=True)

        fname = f"{league_str}_{season_str}_training_data.csv"
        path  = os.path.join(league_dir, fname)
        training_df.to_csv(path, index=False)
        logger.info(
            f"Saved {len(training_df)} training rows -> {path}  "
            f"[season={season_str}, league={league_str}]"
        )

    # Log training rows to rejection log (they are NOT erroneous, but excluded from match analysis)
    if rejection_log is not None and not training_df.empty:
        rejection_log.record(
            training_df,
            step="extract_training_data",
            reason="tag == 'training'  (valid training sessions, saved separately)",
        )

    # Filter to keep only game / game-training rows
    df_filtered = (
        df[df["_clean_tag"].isin(["game", "game training"])]
        .drop(columns=["_clean_tag"])
        .reset_index(drop=True)
    )

    # Rows that are neither training nor game — genuinely unknown
    unknown_mask = ~df["_clean_tag"].isin(["game", "game training", "training"])
    unknown_df   = df[unknown_mask].drop(columns=["_clean_tag"]).copy()
    if not unknown_df.empty and rejection_log is not None:
        rejection_log.record(
            unknown_df,
            step="extract_training_data",
            reason="tag not in [game, game training, training]  (unknown session type)",
        )
        logger.warning(
            f"DATA EXCLUSION: {len(unknown_df)} rows have unrecognised tag values "
            f"and were excluded. Check the rejection audit CSV."
        )

    dropped = len(df) - len(df_filtered)
    if dropped > 0:
        logger.info(
            f"Filtered out {dropped} non-game rows based on '{tag_col}' column."
        )

    return df_filtered


def filter_match_sessions(
    df: pd.DataFrame,
    league: str,
    rejection_log: "RejectionLog | None" = None,
) -> pd.DataFrame:
    """Keep only rows that look like match sessions for the given league."""
    df = df.copy()
    initial_count = len(df)
    pattern = league_definitions.get_league_session_pattern(league)

    if "session_title" not in df.columns:
        return df

    mask       = df["session_title"].astype(str).str.match(pattern, na=False, case=False)
    dropped_df = df[~mask].copy()
    df_filtered = df[mask].reset_index(drop=True)

    dropped = initial_count - len(df_filtered)
    if dropped > 0:
        logger.warning(
            f"DATA EXCLUSION: {dropped} rows did not match {league.upper()} session pattern. "
            "These likely represent non-match sessions and were excluded."
        )
        if rejection_log is not None:
            rejection_log.record(
                dropped_df,
                step="filter_match_sessions",
                reason=f"session_title does not match {league.upper()} pattern",
            )

    return df_filtered


def standardize_split_names(
    df: pd.DataFrame,
    rejection_log: "RejectionLog | None" = None,
) -> pd.DataFrame:
    """
    Filter to valid split types and standardize their names.

    **CRITICAL**: Notebooks explicitly filter BEFORE standardizing.
    """
    df = df.copy()
    if "split_name" not in df.columns:
        return df

    initial_count = len(df)
    valid_pattern = r"^(1st\.half|2nd\.half|1st.half|2nd.half|all|all/game)$"
    mask = df["split_name"].astype(str).str.lower().str.match(valid_pattern, na=False)

    dropped_df  = df[~mask].copy()
    df = df[mask].reset_index(drop=True)

    dropped = initial_count - len(df)
    if dropped > 0:
        unique_bad = dropped_df["split_name"].unique().tolist()
        logger.warning(
            f"DATA EXCLUSION: {dropped} rows with invalid 'split_name' values "
            f"({unique_bad[:10]}). Only '1st Half', '2nd Half', and 'All' are recognised."
        )
        if rejection_log is not None:
            rejection_log.record(
                dropped_df,
                step="standardize_split_names",
                reason=f"split_name not in [1st Half, 2nd Half, All] – found {unique_bad[:5]}",
            )

    # Standardize
    df["split_name"] = df["split_name"].astype(str).str.lower()
    df["split_name"] = df["split_name"].str.replace("1st.half",   "1st Half", regex=False)
    df["split_name"] = df["split_name"].str.replace("2nd.half",   "2nd Half", regex=False)
    df["split_name"] = df["split_name"].str.replace("all/game",   "All",      regex=False)
    df["split_name"] = df["split_name"].str.replace("all",        "All",      regex=False)

    return df


def extract_session_info(
    df: pd.DataFrame,
    rejection_log: "RejectionLog | None" = None,
) -> pd.DataFrame:
    """
    Extract matchday, teams, location, league, and result from session_title.
    """
    if "session_title" not in df.columns:
        return df

    df = df.copy()
    df["session_title"] = (
        df["session_title"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.+", "",   regex=True)
        .str.replace(r"\s*-\s*", "-", regex=True)
        .str.replace(r"\s+", " ",  regex=True)
        .str.title()
    )

    session_regex = re.compile(
        r"^(W?Md\s*\d+)-"
        r"(.+?)-"
        r"(.+?)-"
        r"([^-]+)"
        r"(?:-([^-]+))?"
        r"(?:-([^-]+))?"
        r"(?:\s|$)",
        re.IGNORECASE,
    )

    extracted = df["session_title"].str.extract(session_regex)
    if extracted.isnull().all().all():
        logger.warning("Could not extract session info from any session_title values.")
        return df

    extracted.columns = ["match_day", "ex_club_for", "ex_club_against", "part1", "part2", "part3"]

    location_set = {"Home", "Away"}
    league_set   = {"League", "Cup"}
    result_set   = {"Win", "Loss", "Draw"}

    def get_component(row, valid_set):
        for col in ["part1", "part2", "part3"]:
            val = str(row[col]).strip().title() if pd.notna(row[col]) else None
            if val in valid_set:
                return val
        return None

    extracted["location"] = extracted.apply(get_component, axis=1, valid_set=location_set)
    extracted["league"]   = extracted.apply(get_component, axis=1, valid_set=league_set)
    extracted["result"]   = extracted.apply(get_component, axis=1, valid_set=result_set)

    initial_count = len(df)
    valid_mask  = extracted[["location", "league", "result"]].notnull().all(axis=1)
    dropped_df  = df[~valid_mask].copy()
    df          = df[valid_mask].reset_index(drop=True)
    extracted   = extracted[valid_mask].reset_index(drop=True)

    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(
            f"LOGICAL ERROR: {dropped} rows could not be fully parsed "
            "(missing location, league, or result). These records were excluded."
        )
        if rejection_log is not None:
            rejection_log.record(
                dropped_df,
                step="extract_session_info",
                reason="session_title missing location / league / result component",
            )

    df["match_day"]    = extracted["match_day"]
    df["club_for"]     = extracted["ex_club_for"]
    df["club_against"] = extracted["ex_club_against"]
    df["location"]     = extracted["location"]
    df["result"]       = extracted["result"]

    return df


def validate_matchday_logic(
    df: pd.DataFrame,
    league: str,
    rejection_log: "RejectionLog | None" = None,
) -> pd.DataFrame:
    """Validate that matchdays are within logical bounds for the league."""
    if "match_day" not in df.columns:
        return df

    df = df.copy()
    config  = league_definitions.get_league_config(league)
    max_md  = config.get("max_matchdays", 30)

    md_numeric   = pd.to_numeric(df["match_day"].str.extract(r"(\d+)")[0], errors="coerce")
    invalid_mask = md_numeric > max_md

    if invalid_mask.any():
        invalid_mds = df.loc[invalid_mask, "match_day"].unique()
        logger.error(
            f"LOGICAL ERROR: Found matchdays {invalid_mds} exceeding "
            f"{league.upper()} maximum of {max_md}. These records will be excluded."
        )
        if rejection_log is not None:
            rejection_log.record(
                df[invalid_mask].copy(),
                step="validate_matchday_logic",
                reason=f"match_day > {max_md} (exceeds {league.upper()} season maximum)",
            )
        df = df[~invalid_mask].reset_index(drop=True)

    return df


def extract_player_columns(
    df: pd.DataFrame,
    league: str = None,
    rejection_log: "RejectionLog | None" = None,
) -> pd.DataFrame:
    """Extracts player name, club and position from 'player_name' column."""
    df = df.copy()

    if "p_name" in df.columns and "player_name" not in df.columns:
        df = df.rename(columns={"p_name": "player_name"})

    if "player_name" not in df.columns:
        raise KeyError("player_name column required for player extraction")

    df, player_cols = text_cleaning.extract_player_info(df, player_name_column="player_name")
    df = pd.concat([df, player_cols], axis=1)

    if league and league.lower() == "upl":
        missing_positions = {
            "Saidi Mayanja":        "CM",
            "Ashraf Mugume":        "CM",
            "Musitafa Mujuzi":      "CB",
            "Bright Anukani":       "AM",
            "Kiza Arafat":          "AM",
            "Joel Sserunjogi":      "DM",
            "Katenga Etienne Openga": "LW",
            "Hassan Muhamud":       "CB",
            "Derrick Paul":         "LW",
            "Emmanuel Anyama":      "CF",
            "Abubaker Mayanja":     "CF",
            "Isa Mibiru":           "LB",
            "Julius Poloto":        "MD",
            "Peter Magambo":        "DM",
        }
        mask = df["player_position"] == "None"
        df.loc[mask, "player_position"] = (
            df.loc[mask, "p_name"].map(missing_positions).fillna("None")
        )

    if "club_for" not in df.columns:
        df["club_for"] = df["player_club_"]
    if "club_against" not in df.columns:
        df["club_against"] = pd.NA

    df = text_cleaning.apply_text_cleaning_to_columns(
        df, columns=[c for c in df.columns if c != "split_name"]
    )

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
        if rejection_log is not None:
            rejection_log.record(
                df[df["general_position"].isnull()].copy(),
                step="extract_player_columns",
                reason=f"player_position not mapped to general_position: {list(unmapped[:5])}",
            )

    return df


def normalize_clubs(
    df: pd.DataFrame,
    league: str,
    season: str,
    rejection_log: "RejectionLog | None" = None,
) -> pd.DataFrame:
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

    if "club_for" in df.columns:
        df["club_for_clean"] = df["club_for"].astype(str).apply(
            lambda x: resolve_club(x, clubs, corrections)
        )
        dropped_mask  = df["club_for_clean"].isnull()
        if dropped_mask.any():
            dropped_names = df.loc[dropped_mask, "club_for"].unique()
            count = dropped_mask.sum()
            logger.warning(
                f"DATA EXCLUSION: {count} rows with invalid 'club_for' names: {dropped_names}. "
                "These do not match the official list and will be excluded."
            )
            if rejection_log is not None:
                rejection_log.record(
                    df[dropped_mask].copy(),
                    step="normalize_clubs",
                    reason=f"club_for not in official {league.upper()} club list: {list(dropped_names[:5])}",
                )
            df = df[~dropped_mask].reset_index(drop=True)

        df["club_for"] = df["club_for_clean"]
        df.drop(columns=["club_for_clean"], inplace=True)

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
    if "player_position" in df.columns and exclude:
        df = df[df["player_position"].str.lower() != "gk"]
    return df


def remove_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows."""
    df = df.copy()
    initial_count = len(df)
    df = df[~df.duplicated()].reset_index(drop=True)
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

    keep = [c for c in df.columns if c in must_keep or prop_zeros(df[c]) < threshold]
    dropped_count = len(df.columns) - len(keep)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} sparse columns (>95% zeros).")
    return df[keep]


def remove_outliers(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    iqr_mult: float = None,
    rejection_log: "RejectionLog | None" = None,
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
        q1    = df[col].quantile(0.25)
        q3    = df[col].quantile(0.75)
        iqr   = q3 - q1
        lower = q1 - iqr_mult * iqr
        upper = q3 + iqr_mult * iqr
        mask &= df[col].between(lower, upper) | df[col].isna()

    dropped_df  = df[~mask].copy()
    df = df[mask].reset_index(drop=True)
    dropped = initial_count - len(df)

    if dropped > 0:
        logger.info(f"Removed {dropped} outlier rows (IQR method).")
        if rejection_log is not None:
            rejection_log.record(
                dropped_df,
                step="remove_outliers",
                reason=f"IQR outlier in columns {columns} (multiplier={iqr_mult})",
            )

    return df


def aggregate_halves(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge first and second half rows into single player-match record.
    (See full docstring in original module.)
    """
    df = df.copy()

    split_col = next((c for c in df.columns if c in ["split_name", "period_name"]), None)
    if not split_col or "split_name" not in df.columns:
        logger.warning("No 'split_name' column found. Skipping half aggregation.")
        return df

    half1_df = df[df["split_name"] == "1st Half"].copy()
    half2_df = df[df["split_name"] == "2nd Half"].copy()
    all_df   = df[df["split_name"] == "All"].copy()

    logger.info(
        f"Aggregating halves: {len(half1_df)} H1 rows, "
        f"{len(half2_df)} H2 rows, {len(all_df)} All rows"
    )

    if len(half1_df) > 0 and len(half2_df) > 0:
        merge_keys = constants.get_merge_keys()

        missing_h1 = [k for k in merge_keys if k not in half1_df.columns]
        missing_h2 = [k for k in merge_keys if k not in half2_df.columns]

        if missing_h1:
            logger.error(f"H1 data missing columns: {missing_h1}. Falling back to 'All' split.")
            return all_df.drop("split_name", axis=1).reset_index(drop=True) if len(all_df) > 0 else df
        if missing_h2:
            logger.error(f"H2 data missing columns: {missing_h2}. Falling back to 'All' split.")
            return all_df.drop("split_name", axis=1).reset_index(drop=True) if len(all_df) > 0 else df

        half1_df = half1_df.drop("split_name", axis=1)
        half2_df = half2_df.drop("split_name", axis=1)
        if len(all_df) > 0:
            all_df = all_df.drop("split_name", axis=1)

        half1_df_rn = half1_df.rename(columns=lambda x: x + "_H1" if x not in merge_keys else x)
        half2_df_rn = half2_df.rename(columns=lambda x: x + "_H2" if x not in merge_keys else x)
        if len(all_df) > 0:
            all_df_rn = all_df.rename(columns=lambda x: x + "_ALL" if x not in merge_keys else x)

        df_merged = pd.merge(half1_df_rn, half2_df_rn, on=merge_keys, how="outer")
        if len(all_df) > 0:
            df_merged = pd.merge(df_merged, all_df_rn, on=merge_keys, how="outer")

        df_combined = df_merged[merge_keys].copy()

        sum_cols = [c for c in constants.AGGREGATE_SUM_METRICS
                    if (c + "_H1") in df_merged.columns or (c + "_H2") in df_merged.columns]
        max_cols = [c for c in constants.AGGREGATE_MAX_METRICS
                    if (c + "_H1") in df_merged.columns or (c + "_H2") in df_merged.columns]

        for col in sum_cols:
            h1 = f"{col}_H1"
            h2 = f"{col}_H2"
            h1_vals = pd.to_numeric(df_merged[h1], errors="coerce").fillna(0) if h1 in df_merged.columns else 0
            h2_vals = pd.to_numeric(df_merged[h2], errors="coerce").fillna(0) if h2 in df_merged.columns else 0
            df_combined[col] = h1_vals + h2_vals

        for col in max_cols:
            h1 = f"{col}_H1"
            h2 = f"{col}_H2"
            cols_present = [c for c in [h1, h2] if c in df_merged.columns]
            if cols_present:
                for c in cols_present:
                    df_merged[c] = pd.to_numeric(df_merged[c], errors="coerce").fillna(0)
                df_combined[col] = df_merged[cols_present].max(axis=1)

        # Auto-discover remaining numeric columns (zone data etc.)
        all_h1_cols = [c for c in df_merged.columns if c.endswith("_H1")]
        extra_sum_count = 0
        for h1_col in all_h1_cols:
            col_root = h1_col[:-3]
            if col_root in df_combined.columns:
                continue
            h2_col = f"{col_root}_H2"
            if h2_col in df_merged.columns:
                try:
                    h1_vals = pd.to_numeric(df_merged[h1_col], errors="coerce").fillna(0)
                    h2_vals = pd.to_numeric(df_merged[h2_col], errors="coerce").fillna(0)
                    df_combined[col_root] = h1_vals + h2_vals
                    extra_sum_count += 1
                except Exception as e:
                    logger.debug(f"Skipping auto-aggregation for '{col_root}': {e}")

        if extra_sum_count > 0:
            logger.info(f"Auto-aggregated {extra_sum_count} additional numeric columns (zone data).")

        if "distance_per_min_mmin" in df_combined.columns and "duration" in df_combined.columns:
            dur_nonzero = df_combined["duration"].replace(0, np.nan)
            df_combined["distance_per_min_mmin"] = (df_combined["distance_km"] * 1000) / dur_nonzero

        if "work_ratio_ALL" in df_merged.columns:
            df_combined["work_ratio"] = df_merged["work_ratio_ALL"]
        if "power_score_wkg_ALL" in df_merged.columns:
            df_combined["power_score_wkg"] = df_merged["power_score_wkg_ALL"]

        return df_combined.reset_index(drop=True)

    elif len(all_df) > 0:
        logger.warning("No half data found. Using 'All' split rows instead.")
        return all_df.drop("split_name", axis=1).reset_index(drop=True)
    else:
        logger.warning("No valid split data found. Returning data as-is.")
        return df


def filter_active_sessions(
    df: pd.DataFrame,
    min_distance: float = None,
    min_duration: float = None,
    rejection_log: "RejectionLog | None" = None,
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

    dropped_df  = df[~mask].copy()
    df = df[mask].reset_index(drop=True)
    dropped = initial_count - len(df)

    if dropped > 0:
        logger.info(
            f"Filtered active sessions: removed {dropped} rows "
            f"(distance < {min_distance} km or duration < {min_duration} min)"
        )
        if rejection_log is not None:
            rejection_log.record(
                dropped_df,
                step="filter_active_sessions",
                reason=(
                    f"distance_km < {min_distance} km  OR  "
                    f"duration < {min_duration} min  (below minimum match thresholds)"
                ),
            )

    return df


def compute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute metrics that are derived from raw data columns.
    Should be called AFTER aggregating halves.
    """
    df = df.copy()

    acc_cols = constants.ACCELERATION_ZONE_COLUMNS
    dec_cols = constants.DECELERATION_ZONE_COLUMNS

    existing_acc = [c for c in acc_cols if c in df.columns]
    existing_dec = [c for c in dec_cols if c in df.columns]

    if not existing_acc:
        existing_acc = [
            c for c in df.columns
            if "acceleration" in c.lower() and "zone" in c.lower()
            and "count" in c.lower() and "total" not in c.lower()
        ]
    if not existing_dec:
        existing_dec = [
            c for c in df.columns
            if "deceleration" in c.lower() and "zone" in c.lower()
            and "count" in c.lower() and "total" not in c.lower()
        ]

    df["total_accelerations"] = df[existing_acc].sum(axis=1) if existing_acc else 0
    df["total_decelerations"] = df[existing_dec].sum(axis=1) if existing_dec else 0
    df["total_actions"]       = df["total_accelerations"] + df["total_decelerations"]

    if "duration" in df.columns:
        dur_nonzero = df["duration"].replace(0, np.nan)
        df["acc_counts_per_min"]    = df["total_accelerations"] / dur_nonzero
        df["dec_counts_per_min"]    = df["total_decelerations"] / dur_nonzero
        if "distance_km" in df.columns:
            df["distance_per_min_mmin"] = (df["distance_km"] * 1000) / dur_nonzero
    else:
        df["acc_counts_per_min"]    = np.nan
        df["dec_counts_per_min"]    = np.nan
        df["distance_per_min_mmin"] = np.nan

    if "player_load" in df.columns and "duration" in df.columns:
        df["work_ratio"] = df.get("work_ratio", df["player_load"] / dur_nonzero)

    if "top_speed_ms" in df.columns:
        df["top_speed_kmh"] = pd.to_numeric(df["top_speed_ms"], errors="coerce") * 3.6

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


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────────────────────────────────────

def clean_pipeline(
    raw_path: Optional[str] = None,
    league: str = "fwsl",
    season: str = "2025/2026",
    include_gk: bool = False,
    run_id: str = "",
    rejection_log_dir: str = "",
) -> Tuple[pd.DataFrame, str]:
    """
    Run the full cleaning pipeline for a given league.

    **CRITICAL ORDER** (must aggregate BEFORE filtering):

    1.  Load & standardize columns
    2.  Normalize duration (seconds -> minutes)
    3.  Extract & save training data  (season-organised folder)
    4.  Filter match sessions
    5.  Standardize split_name values
    6.  Clean all OTHER text columns
    7.  Extract session info
    8.  Validate matchday logic
    9.  Extract player columns
    10. Normalize clubs
    11. Filter out goalkeepers
    12. Remove duplicate rows
    13. Drop sparse columns
    14. **Aggregate halves (BEFORE filtering — critical!)**
    15. Filter active sessions (with aggregated data)
    16. Remove outliers (with aggregated data)
    17. Compute derived metrics (AFTER aggregation)
    18. Save processed data
    19. Flush rejection audit CSVs -> logs/rejected/<run_id>/

    Returns:
        Tuple of (cleaned_dataframe, output_path)
    """
    rlog = RejectionLog()
    season_str = season.replace("/", "-")

    logger.info(f"Starting clean_pipeline for {league.upper()}  [season={season_str}]")

    # 1. Load
    df = load_raw_data(raw_path)
    total_raw = len(df)
    logger.info(f"Loaded {total_raw:,} rows, {len(df.columns)} columns")

    # 2. Standardize
    df = standardize_columns(df)

    # 3. Normalize duration
    df = normalize_duration_to_minutes(
        df,
        duration_col="duration",
        raw_unit="seconds",
        keep_raw_seconds=True,
        heuristic_if_unknown=True,
    )

    # 3.5 Extract & save training data (season-aware)
    df = extract_and_save_training_data(
        df, league=league, season=season, rejection_log=rlog
    )

    # 4. Filter session rows
    df = filter_match_sessions(df, league, rejection_log=rlog)

    # 5. Standardize split_name FIRST
    df = standardize_split_names(df, rejection_log=rlog)

    # 6. Clean all OTHER text columns
    df = text_cleaning.apply_text_cleaning_to_columns(
        df, columns=[c for c in df.columns if c != "split_name"]
    )

    # 7. Extract session info
    df = extract_session_info(df, rejection_log=rlog)

    # 8. Validate matchday logic
    df = validate_matchday_logic(df, league, rejection_log=rlog)

    # 9. Extract player columns
    df = extract_player_columns(df, league=league, rejection_log=rlog)

    # 10. Normalize clubs
    df = normalize_clubs(df, league, season, rejection_log=rlog)

    # 11. Filter goalkeepers
    if not include_gk:
        df = filter_gk(df, exclude=True)

    # 12. Remove duplicates
    df = remove_duplicate_rows(df)

    # 13. Drop sparse columns
    df = drop_sparse_columns(df)

    # 14. Aggregate halves (CRITICAL: BEFORE active session filtering)
    df = aggregate_halves(df)

    # 15. Filter active sessions
    df = filter_active_sessions(df, rejection_log=rlog)

    # 16. Remove outliers
    df = remove_outliers(df, rejection_log=rlog)

    # 17. Compute derived metrics
    df = compute_derived_metrics(df)

    logger.info(
        f"Pipeline complete. Output: {len(df):,} rows  "
        f"(from {total_raw:,} raw  ->  {total_raw - len(df):,} total dropped)"
    )

    # 18. Save processed data
    out_path = save_processed(df, league)

    # 19. Flush rejection audit CSVs
    if rejection_log_dir:
        audit_dir = rejection_log_dir
    else:
        # Default: logs/rejected/  (timestamped if run_id provided)
        run_suffix = f"_{run_id}" if run_id else ""
        audit_dir  = os.path.join("logs", "rejected", f"{league.upper()}_{season_str}{run_suffix}")

    rlog.flush(audit_dir, run_id=run_id)

    return df, out_path