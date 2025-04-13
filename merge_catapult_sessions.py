import os
import glob
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    filename=os.path.expanduser("~\\OneDrive\\Desktop\\FUFA\\Logs\\merge_script.log"),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Define the main League Matches folder and its subfolders
desktop_folder = os.path.expanduser("~\\OneDrive\\Desktop\\FUFA")
league_matches_folder = os.path.join(desktop_folder, "League Matches")
league_categories = ["WSL", "UPL"]  # Women's Super League & Uganda Premier League

def merge_team_matches(team_folder, team_name, league):
    """
    Merge all match CSV files for a given team in a specific league.
    """
    csv_files = glob.glob(os.path.join(team_folder, "*.csv"))

    if not csv_files:
        logging.warning(f"No match files found for team '{team_name}' in {league}.")
        return

    logging.info(f"Found {len(csv_files)} match files for '{team_name}' in {league}.")

    dataframes = []

    for file in csv_files:
        try:
            df = pd.read_csv(file)  # Read each match file
            df["Source File"] = os.path.basename(file)  # Add filename as a column for reference
            df["League"] = league  # Add league column for reference
            dataframes.append(df)
            logging.info(f"Loaded file: {file}")
        except Exception as e:
            logging.error(f"Error reading file {file}: {e}")

    if dataframes:
        merged_df = pd.concat(dataframes, ignore_index=True)

        # Define the output file path within the respective league folder
        output_file = os.path.join(team_folder, f"{team_name}_league_matches_all.csv")

        # Save the merged data
        merged_df.to_csv(output_file, index=False)
        logging.info(f"Successfully merged matches for '{team_name}' in {league}. Saved as '{output_file}'.")
    else:
        logging.warning(f"No valid data to merge for '{team_name}' in {league}.")

def merge_all_teams():
    """
    Finds all team folders inside 'WSL' and 'UPL' and merges their match files separately.
    """
    if not os.path.exists(league_matches_folder):
        logging.error("League Matches folder not found.")
        return

    for league in league_categories:  # Loop through WSL & UPL
        league_path = os.path.join(league_matches_folder, league)

        if not os.path.exists(league_path):
            logging.warning(f"Skipping {league}, folder not found.")
            continue
        
        logging.info(f"Processing league: {league}")

        # Loop through all team folders inside the league
        for team_folder in os.listdir(league_path):
            team_path = os.path.join(league_path, team_folder)

            if os.path.isdir(team_path):  # Ensure it's a valid team folder
                team_name = team_folder.replace(" Matches", "")  # Extract team name
                merge_team_matches(team_path, team_name, league)

# Run the script for all leagues and teams
merge_all_teams()
