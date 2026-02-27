"""
League-specific definitions and club rosters for FUFA football leagues.

This module defines the official club names, session patterns, and match day
configurations for different football leagues to ensure consistent data validation
and normalization across the codebase.
"""

# ============================================================================
# FWSL (Football Women's Super League) - Ugandan Women's Top Tier
# ============================================================================

# ============================================================================
# FWSL (Football Women's Super League) - Ugandan Women's Top Tier
# ============================================================================

FWSL_CLUBS_BY_SEASON = {
    "2024/2025": [
        "Kampala Queens FC", "She Maroons FC", "Makerere University WFC",
        "Uganda Martyrs Lubaga WFC", "Kawempe Muslim LFC", "Wakiso Hill WFC",
        "Olila HS WFC", "Rines SS WFC", "Amus College WFC",
        "She Corporates FC", "Lady Doves FC", "FC Tooro Queens"
    ],
    "2025/2026": [
        "Kampala Queens FC", "She Maroons FC", "Makerere University WFC",
        "Uganda Martyrs Lubaga WFC", "Kawempe Muslim LFC", "Asubo Ladies FC",
        "Olila HS WFC", "Rines SS WFC", "Amus College WFC", 
        "She Corporates FC", "Lady Doves FC", "St Noa Girls-Zana FC"  # Placeholder: Update if promotion/relegation changes
    ]
}

# Legacy fallback
FWSL_CLUBS = FWSL_CLUBS_BY_SEASON["2025/2026"]

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

UPL_CLUBS_BY_SEASON = {
    "2024/2025": [
        "KCCA FC", "BUL FC", "URA FC", "Vipers SC", "Express FC", "SC Villa",
        "Maroons FC", "Wakiso Giants FC", "Soltilo Bright Stars FC", "Police FC",
        "UPDF FC", "NEC FC", "Mbarara City FC", "Kitara FC", "Lugazi FC", "Mbale Heroes FC"
    ],
    "2025/2026": [
         "KCCA FC", "BUL FC", "URA FC", "Vipers SC", "Express FC", "SC Villa",
        "Maroons FC", "Buhimba United Saints FC", "Calvary FC", "Police FC",
        "UPDF FC", "NEC FC", "Mbarara City FC", "Kitara FC", "Lugazi FC", "Entebbe UPPC FC"
        
    ]
}

# Legacy fallback
UPL_CLUBS = UPL_CLUBS_BY_SEASON["2025/2026"]

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
    "mfwd":"forward",
    "dfwd":"forward",
    "fwdw":"forward",
    "fwdwd":"forward",
    "cfwd":"foward"
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
    "forwards": ["fw", "fwd", "rw", "lw", "cf", "mfwd", "dfwd", "fwdw", "fwdwd", "cfwd"],
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
    "forward": ["fw", "fwd", "rw", "lw", "cf", "mfwd", "dfwd", "fwdw", "fwdwd", "cfwd"],
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
        "name": "FUFA Women's Super League",
        "clubs_by_season": FWSL_CLUBS_BY_SEASON,
        "clubs": FWSL_CLUBS, # Default/Fallback
        "session_pattern": FWSL_SESSION_PATTERN,
        "session_prefix": "Wmd",
        "max_matchdays": 22,
        "usage_tiers": FWSL_USAGE_TIER_THRESHOLDS,
        "uploaded_matches": FWSL_UPLOADED_MATCHES,
        "position_groups": FWSL_POSITION_GROUPS,
    },
    "upl": {
        "name": "Uganda Premier League",
        "clubs_by_season": UPL_CLUBS_BY_SEASON,
        "clubs": UPL_CLUBS, # Default/Fallback
        "session_pattern": UPL_SESSION_PATTERN,
        "session_prefix": "Md",
        "max_matchdays": 30,  # UPL typically has more matchdays
        "usage_tiers": UPL_USAGE_TIER_THRESHOLDS,
        "uploaded_matches": {},  # Not defined in current data
        "position_groups": UPL_POSITION_GROUPS,
        "missing_positions": UPL_MISSING_POSITIONS,
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
        league (str): League identifier ('fwsl' or 'upl')
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
