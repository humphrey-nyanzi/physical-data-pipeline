#Open each club's folder  in  both UPL and WSL league folders and check for a file named *_league_matches_cleaned.csv or *_league_matches_cleaned_fin.csv
#if a folder has both files, use the *_league_matches_cleaned_fin.csv file
#If a folder has neither file, skip it
#open the file and store the file contents in a variable as a dataframe
#close the file
#join all of the dataframes into one dataframe
#save the joined dataframe as a new file named all_league_matches_cleaned.csv
#save the file in the league folder

import os
import glob
import pandas as pd
import logging

# Setup logging
logging.basicConfig(
    filename=os.path.expanduser("~\\OneDrive\\Desktop\\FUFA\\Logs\\merge_cleaned_data.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def find_cleaned_file(club_path):
    """
    Returns the path to the cleaned file to be used, prioritizing *_cleaned_fin.csv if it exists.
    """
    fin_files = glob.glob(os.path.join(club_path, "*_league_matches_cleaned_fin.csv"))
    regular_files = glob.glob(os.path.join(club_path, "*_league_matches_cleaned.csv"))
    
    if fin_files:
        return fin_files[0]
    elif regular_files:
        return regular_files[0]
    else:
        return None

def merge_cleaned_data_for_league(league_folder):
    """
    Merges all available cleaned files in a league folder into a single DataFrame and saves it.
    """
    league_dataframes = []

    for club_name in os.listdir(league_folder):
        club_path = os.path.join(league_folder, club_name)
        if os.path.isdir(club_path):
            cleaned_file = find_cleaned_file(club_path)
            if cleaned_file:
                try:
                    df = pd.read_csv(cleaned_file)
                    league_dataframes.append(df)
                    logging.info(f"Loaded cleaned data: {cleaned_file}")
                except Exception as e:
                    logging.error(f"Failed to load file {cleaned_file}: {e}")
            else:
                logging.info(f"No cleaned file found in {club_path}. Skipping.")

    if league_dataframes:
        merged_df = pd.concat(league_dataframes, ignore_index=True)
        output_path = os.path.join(league_folder, "all_league_matches_cleaned.csv")
        try:
            merged_df.to_csv(output_path, index=False)
            logging.info(f"Merged file saved at: {output_path}")
        except Exception as e:
            logging.error(f"Failed to save merged file for {league_folder}: {e}")
    else:
        logging.warning(f"No cleaned data found to merge in {league_folder}.")

# Main execution
desktop_folder = os.path.expanduser("~\\OneDrive\\Desktop\\FUFA")
league_folders = ["UPL", "WSL"]

for league in league_folders:
    league_path = os.path.join(desktop_folder, "League Matches", league)
    if os.path.exists(league_path):
        logging.info(f"Starting merge for league: {league}")
        merge_cleaned_data_for_league(league_path)
    else:
        logging.warning(f"League folder not found: {league_path}")
