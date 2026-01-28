"""
Speed zone definitions for different seasons.
"""

SPEED_ZONE_CONFIG = {
    "2024/25": {
        "Zone 1": {"range": "0 – 3.6", "intensity": "Very Low", "descriptor": "Standing, Walking at Recovery Pace"},
        "Zone 2": {"range": "3.61 – 10.8", "intensity": "Low to Moderate", "descriptor": "Jogging and Easy Running"},
        "Zone 3": {"range": "10.81 – 18", "intensity": "Moderate to High", "descriptor": "Running"},
        "Zone 4": {"range": "18.1 – 25.2", "intensity": "High", "descriptor": "High Speed Running"},
        "Zone 5": {"range": "25.21 - 43.2", "intensity": "Maximal", "descriptor": "Sprinting"},
    },
    "2025/26": {
        "Zone 1": {"range": "0 – 3.6", "intensity": "Very Low", "descriptor": "Standing, Walking at Recovery Pace"},
        "Zone 2": {"range": "3.61 – 10.8", "intensity": "Low to Moderate", "descriptor": "Jogging and Easy Running"},
        "Zone 3": {"range": "10.81 – 18", "intensity": "Moderate to High", "descriptor": "Running"},
        "Zone 4": {"range": "18.1 – 25.2", "intensity": "High", "descriptor": "High Speed Running"},
        "Zone 5": {"range": "25.21 - 43.2", "intensity": "Maximal", "descriptor": "Sprinting"},
    },
    "2025/2026": { # Support both formats
        "Zone 1": {"range": "0 – 3.6", "intensity": "Very Low", "descriptor": "Standing, Walking at Recovery Pace"},
        "Zone 2": {"range": "3.61 – 10.8", "intensity": "Low to Moderate", "descriptor": "Jogging and Easy Running"},
        "Zone 3": {"range": "10.81 – 18", "intensity": "Moderate to High", "descriptor": "Running"},
        "Zone 4": {"range": "18.1 – 25.2", "intensity": "High", "descriptor": "High Speed Running"},
        "Zone 5": {"range": "25.21 - 43.2", "intensity": "Maximal", "descriptor": "Sprinting"},
    }
}

def get_speed_zones(season: str) -> dict:
    """Get speed zone definitions for a specific season."""
    import re
    
    # Normalize season string (e.g., 2025/2026 -> 2025/26)
    match = re.search(r"(\d{4})/(\d{2})(\d{2})", season)
    if match:
        season = f"{match.group(1)}/{match.group(3)}"
        
    return SPEED_ZONE_CONFIG.get(season, SPEED_ZONE_CONFIG["2025/26"])
