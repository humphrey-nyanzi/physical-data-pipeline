"""
League-specific definitions and club rosters for FUFA football leagues.

This module defines the official club names, session patterns, and match day
configurations for different football leagues to ensure consistent data validation
and normalization across the codebase.
"""

# ============================================================================
# FWSL (Football Women's Super League) - Ugandan Women's Top Tier
# ============================================================================

FWSL_CLUBS = [
    "Kampala Queens FC",
    "She Maroons FC",
    "Makerere University WFC",
    "Uganda Martyrs Lubaga WFC",
    "Kawempe Muslim LFC",
    "Wakiso Hill WFC",
    "Olila HS WFC",
    "Rines SS WFC",
    "Amus College WFC",
    "She Corporates FC",
    "Lady Doves FC",
    "FC Tooro Queens",
]

FWSL_SESSION_PATTERN = r"^Wmd\d+-[\w\s\.]+-[\w\s\.]+-[\w\s\.]+-[\w\s\.]+-[\w\s\.]+$"
"""
Expected FWSL session title format: 'Wmd{N}-{Club1}-{Club2}-{Location}-{League}-{Result}'
Example: 'Wmd1-Kampala Queens Fc-Olila HS WFC-Home-League-Win'
"""

FWSL_USAGE_TIER_THRESHOLDS = {
    "high": 18,  # ≥18 match days = high engagement (blue)
    "medium": 13,  # 13-17 match days = medium engagement (orange)
    "low": 0,  # <13 match days = low engagement (red)
}

FWSL_UPLOADED_MATCHES = {
    "She Maroons FC": 20,
    "Kawempe Muslim LFC": 22,
    "Uganda Martyrs Lubaga WFC": 18,
    "Rines SS WFC": 22,
    "Amus College WFC": 19,
    "Wakiso Hill WFC": 18,
    "Lady Doves FC": 16,
    "Makerere University WFC": 22,
    "Kampala Queens FC": 17,
    "Olila HS WFC": 13,
    "She Corporates FC": 5,
    "FC Tooro Queens": 0,
}

# ============================================================================
# UPL (Uganda Premier League) - Ugandan Men's Top Tier
# ============================================================================

UPL_CLUBS = [
    "KCCA FC",
    "BUL FC",
    "URA FC",
    "Vipers SC",
    "Express FC",
    "SC Villa",
    "Maroons FC",
    "Wakiso Giants FC",
    "Soltilo Bright Stars FC",
    "Police FC",
    "UPDF FC",
    "NEC FC",
    "Mbarara City FC",
    "Kitara FC",
    "Lugazi FC",
    "Mbale Heroes FC",
]

UPL_SESSION_PATTERN = r"^Md\d+-[\w\s\.]+-[\w\s\.]+-[\w\s\.]+-[\w\s\.]+-[\w\s\.]+$"
"""
Expected UPL session title format: 'Md{N}-{Club1}-{Club2}-{Location}-{League}-{Result}'
Example: 'Md1-Kcca Fc-Ura Fc-Home-League-Win'
"""

UPL_USAGE_TIER_THRESHOLDS = {
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
}

# Aliases for position mapping (common typos or variants)
POSITION_ALIASES = {
    "muslim-am": "am",  # FWSL-specific typo
    "f": "fwd",  # Single letter abbreviation
}

# ============================================================================
# FWSL-specific Position Groups (plural form)
# ============================================================================

FWSL_POSITION_GROUPS = {
    "defenders": ["cb", "lb", "rb", "df", "cd", "dc", "lcb"],
    "midfielders": ["mf", "cm", "am", "dmc", "amc", "mc", "md"],
    "forwards": ["fw", "fwd", "rw", "lw", "cf"],
    "goalkeepers": ["gk"],
}

# ============================================================================
# UPL-specific Position Groups (singular form)
# ============================================================================

UPL_POSITION_GROUPS = {
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
    "forward": ["fw", "fwd", "rw", "lw", "cf"],
    "goalkeeper": ["gk"],
}

# ============================================================================
# UPL-specific Missing Position Mapping (manual fixes for incomplete data)
# ============================================================================

UPL_MISSING_POSITIONS = {
    "Saidi Mayanja": "CM",
    "Ashraf Mugume": "CM",
    "Musitafa Mujuzi": "CB",
    "Bright Anukani": "AM",
    "Kiza Arafat": "AM",
    "Joel Sserunjogi": "DM",
    "Katenga Etienne Openga": "LW",
    "Hassan Muhamud": "CB",
    "Derrick Paul": "LW",
    "Emmanuel Anyama": "CF",
    "Abubaker Mayanja": "CF",
    "Isa Mibiru": "LB",
    "Julius Poloto": "MD",
    "Peter Magambo": "DM",
}

# ============================================================================
# League Configuration Dictionaries (for programmatic access)
# ============================================================================

LEAGUE_CONFIG = {
    "fwsl": {
        "name": "Football Women's Super League",
        "clubs": FWSL_CLUBS,
        "session_pattern": FWSL_SESSION_PATTERN,
        "session_prefix": "Wmd",
        "max_matchdays": 22,
        "usage_tiers": FWSL_USAGE_TIER_THRESHOLDS,
        "uploaded_matches": FWSL_UPLOADED_MATCHES,
        "position_groups": FWSL_POSITION_GROUPS,
    },
    "upl": {
        "name": "Uganda Premier League",
        "clubs": UPL_CLUBS,
        "session_pattern": UPL_SESSION_PATTERN,
        "session_prefix": "Md",
        "max_matchdays": 30,  # UPL typically has more matchdays
        "usage_tiers": UPL_USAGE_TIER_THRESHOLDS,
        "uploaded_matches": {},  # Not defined in current data
        "position_groups": UPL_POSITION_GROUPS,
        "missing_positions": UPL_MISSING_POSITIONS,
    },
}


def get_league_clubs(league: str) -> list:
    """
    Get the list of standard club names for a given league.

    Args:
        league (str): League identifier ('fwsl' or 'upl')

    Returns:
        list: List of standard club names

    Raises:
        ValueError: If league is not recognized
    """
    league_lower = league.lower()
    if league_lower not in LEAGUE_CONFIG:
        raise ValueError(
            f"Unknown league: {league}. Must be one of: {list(LEAGUE_CONFIG.keys())}"
        )
    return LEAGUE_CONFIG[league_lower]["clubs"]


def get_league_session_pattern(league: str) -> str:
    """
    Get the regex pattern for valid session titles in a given league.

    Args:
        league (str): League identifier ('fwsl' or 'upl')

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
        league (str): League identifier ('fwsl' or 'upl')

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
