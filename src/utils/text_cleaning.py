"""
Text processing and normalization utilities for data cleaning.

Provides functions for standardizing player names, club names, positions,
and other text fields to ensure data quality and consistency.
"""

import re
import pandas as pd
from typing import List, Optional, Tuple
import difflib
from functools import lru_cache


def clean_text(s: str) -> str:
    """
    Clean and standardize text by removing extra whitespace and normalizing case.

    Process:
    1. Handle null values (return as-is)
    2. Strip leading/trailing whitespace
    3. Replace multiple spaces with single space
    4. Convert to title case

    Args:
        s (str): Text string to clean

    Returns:
        str: Cleaned text string, or original if null

    Example:
        >>> clean_text("  phoenix  fc  ")
        'Phoenix Fc'
    """
    if pd.isnull(s):
        return s

    s = s.strip()  # Remove leading/trailing whitespace
    s = re.sub(r"\s+", " ", s)  # Replace multiple spaces with single
    s = s.lower()  # Convert to lowercase
    s = s.title()  # Convert to Title Case

    return s


def normalize_name(name: str) -> str:
    """
    Normalize a club/player name for fuzzy matching.

    Process:
    1. Convert to lowercase
    2. Remove all non-alphabetic characters
    3. Remove common suffixes ('fc', 'sc')

    This creates a "canonical" form for comparison that is robust to
    punctuation, spacing, and common abbreviations.

    Args:
        name (str): Name to normalize

    Returns:
        str: Normalized name (letters only)

    Example:
        >>> normalize_name("Phoenix F.C.")
        'phoenix'

        >>> normalize_name("Metro SC")
        'villa'
    """
    name = name.lower()
    name = re.sub(r"[^a-z]", "", name)  # Keep only letters
    name = name.replace("fc", "").replace("sc", "")
    return name

@lru_cache(maxsize=1024)
def _best_match_cache_wrapper(name: str, club_tuple: Tuple[str, ...], min_score: float, return_original: bool) -> Optional[str]:
    """Internal cached version of best_match."""
    name_clean = name.strip().lower().replace(".", "")
    norm_name = normalize_name(name_clean)

    # 1. Try exact normalized match first
    for club in club_tuple:
        if norm_name == normalize_name(club):
            return club

    # 2. Try substring match on normalized names
    for club in club_tuple:
        club_norm = normalize_name(club)
        if norm_name in club_norm or club_norm in norm_name:
            return club

    # 3. Standard Library Fuzzy Matching (difflib)
    matches = difflib.get_close_matches(name.title(), club_tuple, n=1, cutoff=min_score)
    if matches:
        return matches[0]

    # 4. Token overlap scoring
    name_tokens = set(name_clean.split())
    best = None
    best_score = 0

    for club in club_tuple:
        club_tokens = set(club.strip().lower().replace(".", "").split())
        intersection = len(name_tokens & club_tokens)
        union = max(len(club_tokens), 1)
        score = intersection / union

        if score > best_score:
            best = club
            best_score = score

    if best_score >= min_score:
        return best
    
    return name if return_original else None

def best_match(name: str, club_list: List[str], min_score: float = 0.6, return_original: bool = True) -> Optional[str]:
    """
    Find the best matching club name from a list using fuzzy matching.
    
    Optimized with LRU cache to handle large datasets efficiently.
    """
    if not name or pd.isna(name):
        return name if return_original else None
    
    return _best_match_cache_wrapper(name, tuple(club_list), min_score, return_original)


def normalize_club_names(
    df: pd.DataFrame,
    club_columns: List[str],
    club_list: List[str],
    corrections: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Normalize club names in a DataFrame using best_match and manual corrections.

    Args:
        df (pd.DataFrame): DataFrame with club name columns
        club_columns (List[str]): Column names containing club names
        club_list (List[str]): List of standard club names
        corrections (Optional[dict]): Manual corrections mapping
                                     e.g., {'Bad Name': 'Good Name'}

    Returns:
        pd.DataFrame: DataFrame with normalized club names

    Example:
        >>> df = pd.DataFrame({
        ...     'club_for': ['Phoenix FC', 'Capital Fc'],
        ...     'club_against': ['Valkyrie FC', 'Cobras SC']
        ... })
        >>> clubs = ['Phoenix FC', 'Capital FC', 'Valkyrie FC', 'Cobras SC']
        >>> normalize_club_names(df, ['club_for', 'club_against'], clubs)
    """
    df = df.copy()

    for col in club_columns:
        if col in df.columns:
            # First pass: fuzzy matching
            df[col] = df[col].astype(str).apply(lambda x: best_match(x, club_list))

            # Second pass: manual corrections
            if corrections:
                df[col] = df[col].replace(corrections)

    return df


def normalize_positions(
    df: pd.DataFrame,
    position_mapping: dict,
    aliases: Optional[dict] = None,
    target_column: str = "general_position",
) -> pd.DataFrame:
    """
    Normalize player position codes to standardized groups.

    Args:
        df (pd.DataFrame): DataFrame with player_position column
        position_mapping (dict): Mapping from position codes to groups
                                e.g., {'cb': 'defender', 'cm': 'midfielder'}
        aliases (Optional[dict]): Typo corrections before main mapping
                                 e.g., {'f': 'fw'}
        target_column (str): Name of output column with normalized positions

    Returns:
        pd.DataFrame: DataFrame with new normalized position column

    Example:
        >>> df = pd.DataFrame({'player_position': ['cb', 'cm', 'fw', 'gk']})
        >>> mapping = {'cb': 'defender', 'cm': 'midfielder', 'fw': 'forward', 'gk': 'goalkeeper'}
        >>> normalize_positions(df, mapping)
        #   player_position general_position
        # 0              cb          defender
        # 1              cm        midfielder
        # 2              fw           forward
        # 3              gk        goalkeeper
    """
    df = df.copy()

    # Convert to lowercase
    df["player_position"] = df["player_position"].str.lower()

    # Apply aliases if provided
    if aliases:
        for old, new in aliases.items():
            df["player_position"] = df["player_position"].str.replace(old, new)

    # Apply position mapping
    df[target_column] = df["player_position"].map(position_mapping)

    return df


def fix_player_name_format(name: str) -> str:
    """
    Fix incorrectly formatted player names.

    Handles cases where the format is 'Name - Club_Position' instead of
    'Name - Club - Position' and converts to the correct format.

    Args:
        name (str): Player name string

    Returns:
        str: Fixed player name string

    Example:
        >>> fix_player_name_format('John Doe - Capital FC_CM')
        'John Doe - Capital FC - CM'

        >>> fix_player_name_format('Jane Smith - Phoenix FC - FW')
        'Jane Smith - Phoenix FC - FW'  # Already correct
    """
    if re.fullmatch(r".+ - .+_.+", name):
        return re.sub(r"(.+ - .+?)_(.+)", r"\1 - \2", name)
    return name


def extract_player_info(
    df: pd.DataFrame, player_name_column: str = "player_name"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract player name, club, and position from a concatenated string column.

    Expected format: 'Player Name - Club Name - Position'

    Args:
        df (pd.DataFrame): DataFrame with player_name column
        player_name_column (str): Name of column to parse

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            - DataFrame with rows having valid player info
            - DataFrame with extracted columns (p_name, player_club_, player_position)

    Example:
        >>> df = pd.DataFrame({
        ...     'player_name': [
        ...         'John Doe - Capital FC - CM',
        ...         'Jane Smith - Phoenix FC - FW'
        ...     ]
        ... })
        >>> df_clean, player_cols = extract_player_info(df)
    """
    # Step 1: Fix incorrectly formatted entries
    df_copy = df.copy()
    df_copy[player_name_column] = df_copy[player_name_column].apply(
        fix_player_name_format
    )

    # Step 2: Extract fields
    player_regex = re.compile(
        r"^(.+?)\s*-\s*"  # Player name
        r"(.+?)\s*-\s*"  # Club
        r"(.+?)$"  # Position
    )

    player_cols = df_copy[player_name_column].str.extract(player_regex)
    player_cols.columns = ["p_name", "player_club_", "player_position"]

    # Step 3: Keep only valid rows
    valid = player_cols.dropna().copy()
    df_clean = df.loc[valid.index].reset_index(drop=True)
    player_cols = player_cols.loc[valid.index].reset_index(drop=True)

    return df_clean, player_cols


def apply_text_cleaning_to_columns(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Apply text cleaning to categorical columns in a DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to clean
        columns (Optional[List[str]]): Specific columns to clean.
                                      If None, cleans all object-type columns.

    Returns:
        pd.DataFrame: DataFrame with cleaned text columns
    """
    df = df.copy()

    if columns is None:
        columns = [col for col in df.columns if df[col].dtype == "object"]

    for col in columns:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype(str).apply(clean_text)

    return df
