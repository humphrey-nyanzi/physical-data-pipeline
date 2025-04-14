import os
import glob
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    filename=os.path.expanduser("~\\Desktop\\FUFA\\Logs\\merge_script.log"),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Define the main League Matches folder and its subfolders
desktop_folder = os.path.expanduser("~\\Desktop\\FUFA")
league_matches_folder = os.path.join(desktop_folder, "League Matches")
league_categories = ["WSL", "UPL"]  # Women's Super League & Uganda Premier League

def merge_team_matches(team_folder, team_name, league):
    """
    Merge new match CSV files for a given team in a specific league into an existing master file.
    If no master file exists, create one from scratch. 
    Skips files matching the patterns for master, cleaned, or benched files.
    """
    # Define the output file path within the respective team folder
    output_file = os.path.join(team_folder, f"{team_name}_league_matches_all.csv")
    
    # Get list of CSV files in the team folder (all match files)
    csv_files = glob.glob(os.path.join(team_folder, "*.csv"))
    
    # Exclude files that are the master, cleaned, or benched files
    filtered_files = []
    for file in csv_files:
        file_name = os.path.basename(file).lower()
        if ("league_matches_all" in file_name) or \
           ("league_matches_cleaned" in file_name) or \
           ("league_matches_benched" in file_name):
            logging.info(f"Skipping file (excluded by pattern): {file_name}")
            continue
        filtered_files.append(file)
    
    if not filtered_files:
        logging.warning(f"No match files found for team '{team_name}' in {league} after filtering.")
        return

    # If the master merged file already exists, load it and note its source files
    if os.path.exists(output_file):
        try:
            master_df = pd.read_csv(output_file)
            # Assume that the master file includes a "Source File" column.
            processed_files = set(master_df["Source File"].unique())
            logging.info(f"Master file exists for '{team_name}' with {len(processed_files)} processed files.")
        except Exception as e:
            logging.error(f"Error reading master file {output_file}: {e}")
            master_df = pd.DataFrame()
            processed_files = set()
    else:
        master_df = pd.DataFrame()
        processed_files = set()
        logging.info(f"No master file for '{team_name}'. Creating new master file.")
    
    new_dataframes = []
    
    # Process each CSV file if it hasn't been merged already.
    for file in filtered_files:
        file_name = os.path.basename(file)
        if file_name in processed_files:
            logging.info(f"Skipping already processed file: {file_name}")
            continue
        
        try:
            df = pd.read_csv(file)
            df["Source File"] = file_name  # Mark source file for tracking
            df["League"] = league          # Add league column for reference
            new_dataframes.append(df)
            logging.info(f"Loaded new file: {file_name}")
        except Exception as e:
            logging.error(f"Error reading file {file}: {e}")
    
    if new_dataframes:
        new_data = pd.concat(new_dataframes, ignore_index=True)
        # Append new data to the existing master dataframe
        master_df = pd.concat([master_df, new_data], ignore_index=True)
        
        # Save the updated master file
        try:
            master_df.to_csv(output_file, index=False)
            logging.info(f"Successfully updated master file for '{team_name}' in {league}. Saved as '{output_file}'.")
        except Exception as e:
            logging.error(f"Error saving master file {output_file}: {e}")
    else:
        logging.info(f"No new data to merge for '{team_name}' in {league}.")

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
