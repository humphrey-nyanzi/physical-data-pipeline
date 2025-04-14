import os
import glob
import pandas as pd
import re
import logging

# Configure logging to write to a log file on the Desktop
logging.basicConfig(
    filename=os.path.expanduser("~\\OneDrive\\Desktop\\FUFA\\Logs\\rename_script.log"),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def sanitize_filename(name):
    """
    Remove or replace characters that are not allowed in filenames.
    For Windows, this removes \ / : * ? " < > |.
    """
    return re.sub(r'[\\/*?:"<>|]', "", name)

def generate_unique_filename(directory, filename):
    """
    Ensure filename uniqueness by appending a counter if necessary.
    """
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base} ({counter}){ext}"
        counter += 1
    return new_filename

def match_team(candidate,team_list):
    """
    Given a candidate team name(from the session title) and a list of official team names,
    try to find a match using several fallback strategies:
    1. Exact match
    2.Check if the candidate is a substring of any team name
    3.Compare the first two words
    4. Compare the first word
    returns the matched team name(as stored in the official list) or None if no match is found
    """
    candidate = candidate.upper().strip()

    #1. Exact match
    for team in team_list:
        if candidate == team.upper():
            return team.upper()
        
    #2. substring match
    for team in team_list:
        if candidate in team.upper():
            return team.upper()
        
    #3. First two words match(if candidate has two or more words)
    candidate_words=candidate.split()
    if len(candidate_words) >= 2:
        candidate_prefix = ''.join(candidate_words[:2])
        for team in team_list:
            team_words=team.upper().split()
            if len(team_words) >=2 and candidate_prefix == ''.join(team_words[:2]):
                return team.upper()
            
    #First word match as last resort
    if candidate_words:
        candidate_first=candidate_words[0]
        for team in team_list:
            if candidate_first in team.upper():
                return team.upper()
            
    return None


# Define the Downloads folder path and the Desktop folder path
downloads_folder = os.path.expanduser("~\\Downloads")
fufa_folder = os.path.expanduser("~\\OneDrive\\Desktop\\FUFA")

# Define the parent folder for league matches on the desktop
league_matches_folder = os.path.join(fufa_folder, "League Matches")
if not os.path.exists(league_matches_folder):
    os.makedirs(league_matches_folder)
    logging.info(f"Created folder: {league_matches_folder}")
else:
    logging.info(f"Folder already exists: {league_matches_folder}")

# Create subfolders for UPL and WSL within League Matches
upl_folder = os.path.join(league_matches_folder, "UPL")
wsl_folder = os.path.join(league_matches_folder, "WSL")
for folder in [upl_folder, wsl_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        logging.info(f"Created folder: {folder}")
    else:
        logging.info(f"Folder already exists: {folder}")

# Define lists for UPL and WSL teams (update these lists as needed)
upl_teams = ["KCCA FC", "Vipers SC", "SC Villa", "Express FC", "URA FC", "Maroons FC", 'Lugazi FC', 'Police FC', 'BUL FC',
             'UPDF FC', 'Mbarara City FC', 'Soltilo Bright Stars FC', 'Wakiso Giants FC', 'Mbale Heroes FC', 'Kitara FC', 'NEC FC']
wsl_teams = ['Kampala Queens FC', 'Tooro Queens FC', 'Wakiso Hill WFC', 'She Corporates FC', 'She Maroons FC', 'Olila HS WFC', 'Rines SS WFC',
             'Kawempe Muslim LFC', 'Uganda Martyrs WFC', 'Makerere University WFC', 'Lady Doves WFC', 'Amus College WFC'] 

# Create the file pattern for files starting with "Catapult-Export-" and ending with ".csv"
pattern = os.path.join(downloads_folder, "Catapult-Export-*.csv")
files = glob.glob(pattern)
logging.info(f"Found {len(files)} files matching pattern: {pattern}")

for file_path in files:
    try:
        logging.info(f"Processing file: {file_path}")
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # Check if the "Session Title" column exists
        if "Session Title" in df.columns:
            # Extract the first value under "Session Title"
            session_name = str(df["Session Title"].iloc[0])
            session_name = sanitize_filename(session_name)
            
            # Convert session name to UPPER CASE
            session_name_title = session_name.upper()
            
            # Split the session title using hyphen as delimiter
            session_parts = session_name_title.split("-")
            if len(session_parts) > 1:
                # Extract the second part and take only the whole word 
                team_candidate = session_parts[1].strip()
                #use match team function with official team lists
                matched_team=match_team(team_candidate,list(upl_teams)+list(wsl_teams))
                if matched_team is not None:
                    team_name = matched_team
                else:
                    team_name = "UNKNOWN"
                    logging.warning(f"Could not match team for team: {team_candidate}")
            else:
                team_name='UNKONWN'
                logging.warning(f'Session title did not have expected hyphen format: {session_name_title}')
            
            # Convert team lists to UPPER case for comparison
            upl_teams_upper = [x.upper() for x in upl_teams]
            wsl_teams_upper = [x.upper() for x in wsl_teams]
            team_name = team_name.upper()

            if team_name in upl_teams_upper:
                league_folder = upl_folder
                logging.info(f"Team {team_name} identified as UPL team.")
            elif team_name in wsl_teams_upper:
                league_folder = wsl_folder
                logging.info(f"Team {team_name} identified as WSL team.")
            else:
                league_folder = upl_folder  # Defaulting to UPL if team not found
                logging.warning(f"Team '{team_name}' not found in team lists; defaulting to UPL.")

            # Create the team folder inside the appropriate league folder (e.g., "KCCA Matches")
            team_folder_name = f"{team_name.title()} Matches"
            team_folder_path = os.path.join(league_folder, team_folder_name)
            if not os.path.exists(team_folder_path):
                os.makedirs(team_folder_path)
                logging.info(f"Created folder: {team_folder_path}")
            else:
                logging.info(f"Folder already exists: {team_folder_path}")
            
            new_file_name = generate_unique_filename(team_folder_path, f"{session_name}.csv")

            # Define the new file name (in UPPER CASE) with .csv extension
            temp_new_file_path = os.path.join(downloads_folder, new_file_name)
            os.rename(file_path, temp_new_file_path)
            logging.info(f"Renamed '{file_path}' to '{temp_new_file_path}'")
            
            # Final destination: move the file into the team folder
            
            final_file_path = os.path.join(team_folder_path, new_file_name)
            os.rename(temp_new_file_path, final_file_path)
            logging.info(f"Moved file to '{final_file_path}'\n")
        else:
            logging.error(f"Column 'Session Title' not found in {file_path}")
    except Exception as e:
        logging.exception(f"Error processing file {file_path}: {e}")
