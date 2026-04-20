"""
League-specific definitions and club rosters for football leagues.

This module defines the official club names, session patterns, and match day
configurations for different football leagues to ensure consistent data validation
and normalization across the codebase.
"""

# ============================================================================
# WOMENS_LEAGUE (Women's Super League) - Women's Top Tier
# ============================================================================

WOMENS_LEAGUE_CLUBS_BY_SEASON = {
    "2024/2025": [
        "Phoenix FC", "Valkyrie FC", "University WFC",
        "Heritage WFC", "Crescent LFC", "Hillside WFC",
        "Academy HS WFC", "Sterling SS WFC", "College WFC",
        "Corporate FC", "Lady Hawks FC", "FC Queens"
    ],
    "2025/2026": [
        "Phoenix FC", "Valkyrie FC", "University WFC",
        "Heritage WFC", "Crescent LFC", "Astra Ladies FC",
        "Academy HS WFC", "Sterling SS WFC", "College WFC", 
        "Corporate FC", "Lady Hawks FC", "Saints Girls FC"  # Placeholder: Update if promotion/relegation changes
    ]
}

# Legacy fallback
WOMENS_LEAGUE_CLUBS = WOMENS_LEAGUE_CLUBS_BY_SEASON["2025/2026"]

WOMENS_LEAGUE_SESSION_PATTERN = r"^W?md\s*\d+\s*-.*"
"""
Expected WOMENS_LEAGUE session title format: 'Wmd{N}-{Club1}-{Club2}-{Location}-{League}-{Result}'
Example: 'Wmd1-Phoenix Fc-Academy HS WFC-Home-League-Win'
"""

WOMENS_LEAGUE_USAGE_TIER_THRESHOLDS = {
    "high": 18,  # ≥18 match days = high engagement (blue)
    "medium": 13,  # 13-17 match days = medium engagement (orange)
    "low": 0,  # <13 match days = low engagement (red)
}

WOMENS_LEAGUE_UPLOADED_MATCHES = {
    "Valkyrie FC": 20,
    "Crescent LFC": 22,
    "Heritage WFC": 18,
    "Sterling SS WFC": 22,
    "College WFC": 19,
    "Hillside WFC": 18,
    "Lady Hawks FC": 16,
    "University WFC": 22,
    "Phoenix FC": 17,
    "Academy HS WFC": 13,
    "Corporate FC": 5,
    "FC Queens": 0,
}

# ============================================================================
# MENS_LEAGUE (Premier League) - Men's Top Tier
# ============================================================================

MENS_LEAGUE_CLUBS_BY_SEASON = {
    "2024/2025": [
        "Capital FC", "Forge FC", "Revenue FC", "Cobras SC", "Rapid FC", "Metro SC",
        "Garrison FC", "Lakeside Giants FC", "Shining Stars FC", "Shield FC",
        "Army FC", "Eastern FC", "Western City FC", "Central FC", "Industrial FC", "Mountain Heroes FC"
    ],
    "2025/2026": [
         "Capital FC", "Forge FC", "Revenue FC", "Cobras SC", "Rapid FC", "Metro SC",
        "Garrison FC", "United Saints FC", "Calvary FC", "Shield FC",
        "Army FC", "Eastern FC", "Western City FC", "Central FC", "Industrial FC", "Laketown FC"
        
    ]
}

# Legacy fallback
MENS_LEAGUE_CLUBS = MENS_LEAGUE_CLUBS_BY_SEASON["2025/2026"]

MENS_LEAGUE_SESSION_PATTERN = r"^Md\s*\d+\s*-.*"
"""
Expected MENS_LEAGUE session title format: 'Md{N}-{Club1}-{Club2}-{Location}-{League}-{Result}'
Example: 'Md1-Capital Fc-Revenue Fc-Home-League-Win'
"""

MENS_LEAGUE_USAGE_TIER_THRESHOLDS = {
    "high": 25,  # ≥25 match days = high engagement (blue)
    "medium": 18,  # 18-24 match days = medium engagement (orange)
    "low": 0,  # <18 match days = low engagement (red)
}

# ============================================================================
# Match Metadata Enumerations
# ============================================================================

MATCH_LOCATIONS = {"Home", "Away"}
MATCH_LEAGUE_TYPES = {"League", "Cup"}
MATCH_RESULTS = {"Win", "Loss", "Draw"}

# ============================================================================
# Common Position Mappings (across both leagues)
# ============================================================================

POSITION_MAPPING = {
    # Goalkeepers (excluded from analysis in most cases)
    "gk": "goalkeeper",
    # Defenders
    "df": "defender",
    "rb": "defender",
    "cb": "defender",
    "lb": "defender",
    "cd": "defender",
    "dc": "defender",
    "lcb": "defender",
    # Midfielders
    "mf": "midfielder",
    "cm": "midfielder",
    "am": "midfielder",
    "dm": "midfielder",
    "dmc": "midfielder",
    "amc": "midfielder",
    "mc": "midfielder",
    "md": "midfielder",
    # Forwards
    "fw": "forward",
    "fwd": "forward",
    "rw": "forward",
    "lw": "forward",
    "cf": "forward",
    "mfwd":"forward",
    "dfwd":"forward",
    "fwdw":"forward",
    "fwdwd":"forward",
    "cfwd":"foward"
}

# Aliases for position mapping (common typos or variants)
POSITION_ALIASES = {
    "muslim-am": "am",  # League-specific typo
    "f": "fwd",  # Single letter abbreviation
}

# ============================================================================
# WOMENS_LEAGUE-specific Position Groups (plural form)
# ============================================================================

WOMENS_LEAGUE_POSITION_GROUPS = {
    "defenders": ["cb", "lb", "rb", "df", "cd", "dc", "lcb"],
    "midfielders": ["mf", "cm", "am", "dmc", "amc", "mc", "md"],
    "forwards": ["fw", "fwd", "rw", "lw", "cf", "mfwd", "dfwd", "fwdw", "fwdwd", "cfwd"],
    "goalkeepers": ["gk"],
}

# ============================================================================
# MENS_LEAGUE-specific Position Groups (singular form)
# ============================================================================

MENS_LEAGUE_POSITION_GROUPS = {
    "defender": [
        "df",
        "rb",
        "cb",
        "lb",
        "cd",
        "fwd",
        "dmc",
        "amc",
        "dc",
        "cf",
        "mc",
        "lcb",
        "md",
    ],
    "midfielder": ["mf", "cm", "am", "dm", "dmc", "amc", "mc", "md"],
    "forward": ["fw", "fwd", "rw", "lw", "cf", "mfwd", "dfwd", "fwdw", "fwdwd", "cfwd"],
    "goalkeeper": ["gk"],
}

# ============================================================================
# MENS_LEAGUE-specific Missing Position Mapping (manual fixes for incomplete data)
# ============================================================================

MENS_LEAGUE_MISSING_POSITIONS = {
    "Player_01": "CM",
    "Player_02": "CM",
    "Player_03": "CB",
    "Player_04": "AM",
    "Player_05": "AM",
    "Player_06": "DM",
    "Player_07": "LW",
    "Player_08": "CB",
    "Player_09": "LW",
    "Player_10": "CF",
    "Player_11": "CF",
    "Player_12": "LB",
    "Player_13": "MD",
    "Player_14": "DM",
}

# ============================================================================
# League Configuration Dictionaries (for programmatic access)
# ============================================================================

import os
import importlib

PROFILE_NAME = os.getenv("MATCH_ANALYSIS_PROFILE", "generic").lower()
if PROFILE_NAME != "generic":
    try:
        profile = importlib.import_module(f"src.config.profiles.{PROFILE_NAME}_profile")
        WOMENS_LEAGUE_CLUBS_BY_SEASON = getattr(profile, "WOMENS_LEAGUE_CLUBS_BY_SEASON", WOMENS_LEAGUE_CLUBS_BY_SEASON)
        WOMENS_LEAGUE_CLUBS = WOMENS_LEAGUE_CLUBS_BY_SEASON.get("2025/2026", [])
        MENS_LEAGUE_CLUBS_BY_SEASON = getattr(profile, "MENS_LEAGUE_CLUBS_BY_SEASON", MENS_LEAGUE_CLUBS_BY_SEASON)
        MENS_LEAGUE_CLUBS = MENS_LEAGUE_CLUBS_BY_SEASON.get("2025/2026", [])
    except ImportError as e:
        print(f"Warning: Could not load profile '{PROFILE_NAME}': {e}")

LEAGUE_CONFIG = {
    "womens_league": {
        "name": "Women's Super League",
        "clubs_by_season": WOMENS_LEAGUE_CLUBS_BY_SEASON,
        "clubs": WOMENS_LEAGUE_CLUBS, # Default/Fallback
        "session_pattern": WOMENS_LEAGUE_SESSION_PATTERN,
        "session_prefix": "Wmd",
        "max_matchdays": 22,
        "usage_tiers": WOMENS_LEAGUE_USAGE_TIER_THRESHOLDS,
        "uploaded_matches": WOMENS_LEAGUE_UPLOADED_MATCHES,
        "position_groups": WOMENS_LEAGUE_POSITION_GROUPS,
    },
    "mens_league": {
        "name": "Premier League",
        "clubs_by_season": MENS_LEAGUE_CLUBS_BY_SEASON,
        "clubs": MENS_LEAGUE_CLUBS, # Default/Fallback
        "session_pattern": MENS_LEAGUE_SESSION_PATTERN,
        "pattern": MENS_LEAGUE_SESSION_PATTERN,
        "max_matchdays": 30,  # MENS_LEAGUE typically has more matchdays
        "usage_tiers": MENS_LEAGUE_USAGE_TIER_THRESHOLDS,
        "uploaded_matches": {},  # Not defined in current data
        "position_groups": MENS_LEAGUE_POSITION_GROUPS,
        "missing_positions": MENS_LEAGUE_MISSING_POSITIONS,
    },
}


def _normalize_season(season_str: str) -> str:
    """
    Normalize season strings to 'YYYY/YYYY' format.
    Examples: '25/26' -> '2025/2026', '2025/26' -> '2025/2026'
    """
    if not season_str:
        return "2025/2026"  # Default
        
    s = str(season_str).strip()
    
    # Handle '25/26' -> '2025/2026'
    if len(s) == 5 and s[2] == '/':
        parts = s.split('/')
        if len(parts) == 2 and len(parts[0]) == 2 and len(parts[1]) == 2:
            return f"20{parts[0]}/20{parts[1]}"
            
    # Handle '2025/26' -> '2025/2026'
    if len(s) == 7 and s[4] == '/':
        parts = s.split('/')
        if len(parts) == 2 and len(parts[0]) == 4 and len(parts[1]) == 2:
            return f"{parts[0]}/20{parts[1]}"
            
    return s


def get_league_clubs(league: str, season: str = "2025/2026") -> list:
    """
    Get the list of standard club names for a given league and season.

    Args:
        league (str): League identifier ('womens_league' or 'mens_league')
        season (str): Season identifier (e.g., '2025/2026'). Default '2025/2026'.

    Returns:
        list: List of standard club names for that season.

    Raises:
        ValueError: If league is not recognized
    """
    league_lower = league.lower()
    if league_lower not in LEAGUE_CONFIG:
        raise ValueError(
            f"Unknown league: {league}. Must be one of: {list(LEAGUE_CONFIG.keys())}"
        )
    
    config = LEAGUE_CONFIG[league_lower]
    season_norm = _normalize_season(season)
    
    # Try to find season specific list
    if "clubs_by_season" in config and season_norm in config["clubs_by_season"]:
        return config["clubs_by_season"][season_norm]
        
    # Fallback to default clubs if season not found
    return config["clubs"]


def get_league_session_pattern(league: str) -> str:
    """
    Get the regex pattern for valid session titles in a given league.

    Args:
        league (str): League identifier ('womens_league' or 'mens_league')

    Returns:
        str: Regex pattern string

    Raises:
        ValueError: If league is not recognized
    """
    league_lower = league.lower()
    if league_lower not in LEAGUE_CONFIG:
        raise ValueError(
            f"Unknown league: {league}. Must be one of: {list(LEAGUE_CONFIG.keys())}"
        )
    return LEAGUE_CONFIG[league_lower]["session_pattern"]


def get_league_config(league: str) -> dict:
    """
    Get the complete configuration dictionary for a given league.

    Args:
        league (str): League identifier ('womens_league' or 'mens_league')

    Returns:
        dict: League configuration dictionary

    Raises:
        ValueError: If league is not recognized
    """
    league_lower = league.lower()
    if league_lower not in LEAGUE_CONFIG:
        raise ValueError(
            f"Unknown league: {league}. Must be one of: {list(LEAGUE_CONFIG.keys())}"
        )
    return LEAGUE_CONFIG[league_lower]
