import re

def parse_matchday(session_title):
    """
    Extract matchday number from session title.
    Handles: MD11, MD-11, MD 11, md11, etc.
    Returns: int matchday number or None
    """
    if not isinstance(session_title, str):
        return None
    
    # Look for MD pattern (case insensitive)
    match = re.search(r'\bMD[\s\-]?(\d{1,2})\b', session_title, re.IGNORECASE)
    if match:
        md_num = int(match.group(1))
        # Validate reasonable range (max MD for UPL is 30 for WSL is 22)
        if 1 <= md_num <= 30:
            return md_num
    return None

def parse_session_info(session_title):
    """
    Parse session title to extract match information.
    Format: MD#-TeamA-TeamB-Home/Away-League-Win/Loss/Draw
    Alternative (missing league): MD#-TeamA-TeamB-Home/Away-Win/Loss/Draw
    Returns: dict with parsed info or None if invalid
    """
    if not isinstance(session_title, str):
        return None
    
    # Try to parse matchday first
    md = parse_matchday(session_title)
    if md is None:
        return None
    
    # Split on hyphens
    parts = [p.strip() for p in session_title.split('-')]
    
    # Needs 6 parts usually, but sometimes 5 if league is missed
    if len(parts) < 5:
        return None
    
    try:
        info = {
            'matchday': md,
            'team1': parts[1],
            'team2': parts[2],
            'venue': parts[3],
        }
        
        if len(parts) >= 6:
            info['league'] = parts[4]
            info['result'] = parts[5]
        elif len(parts) == 5:
            # Assume League is missing
            info['league'] = "Unknown"
            info['result'] = parts[4]
            
        return info
    except IndexError:
        return None

def parse_player_details(full_name_str):
    """
    Parse 'First Last-Club-Position' string.
    Returns: (Name, Position)
    """
    if not isinstance(full_name_str, str):
        return full_name_str, ""
        
    parts = [p.strip() for p in full_name_str.split('-')]
    
    if len(parts) >= 3:
        # First Last - Club - Position
        name = parts[0]
        # club = parts[1] # Ignored as per user request (use session team instead)
        position = parts[2]
        return name, position
    elif len(parts) == 2:
        # Assume Name - Position or Name - Club? 
        # Risky, but let's assume Name - Position if generic
        return parts[0], parts[1]
    else:
        return full_name_str, ""
