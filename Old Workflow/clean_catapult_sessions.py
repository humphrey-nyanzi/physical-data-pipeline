import os
import glob
import pandas as pd
import re
import logging
import datetime

# Configure logging
logging.basicConfig(
    filename=os.path.expanduser("~\\OneDrive\\Desktop\\FUFA\\Logs\\clean_script.log"),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def clean_file(file_path, output_folder, team_identifier):
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Loaded file for cleaning: {file_path}")
    except Exception as e:
        logging.error(f"Error loading file {file_path}: {e}")
        return None

    df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], origin='1899-12-30', unit='D', errors='coerce')

    cols_to_drop_regex = df.filter(regex=r'time_in_hr_load_zone_.*%_-_.*%_max_hr').columns
    df = df.drop(columns=cols_to_drop_regex, errors='ignore')
    columns_to_remove = ['split_start_time', 'split_end_time', 'hr_load', 'hr_max_(bpm)', 
                         'time_in_red_zone_(min)', 'league', 'tags']
    df = df.drop(columns=columns_to_remove, errors='ignore')
    df = df.map(lambda x: x.strip().lower() if isinstance(x, str) else x)

    master_fname = os.path.basename(file_path).lower()
    if 'source_file' in df.columns:
        df = df[df['source_file'] != master_fname]
    if 'split_name' in df.columns:
        df = df[df['split_name'] != 'all']

    if 'session_title' in df.columns:
        try:
            df[['match_day', 'home_team', 'away_team', 'location', 'league', 'result']] = \
                df['session_title'].str.split('-', expand=True, n=5)
        except Exception as e:
            logging.error(f"Error splitting 'session_title' in {file_path}: {e}")

    if 'player_name' in df.columns:
        try:
            df[['player_nam', 'team', 'player_position']] = \
                df['player_name'].str.split('-', expand=True, n=2)
        except Exception as e:
            logging.error(f"Error splitting 'player_name' in {file_path}: {e}")

    df = df.drop(columns=['league', 'session_title', 'source_file', 'player_name'], errors='ignore')

    if 'team' in df.columns:
        extracted = df['team'].str.extract(r'^(kcca_)?(.*)$')
        if extracted is not None:
            df['team'] = extracted[1]
            df['player_position_'] = df['player_position'].fillna(df['team'])
        else:
            logging.warning("Regex extraction for team didn't match.")
    else:
        logging.warning("Column 'team' not found for extraction.")

    if 'player_position_' in df.columns:
        df.loc[df['player_position_'].isin(['mf', 'df', 'fw']), 'player_position'] = df['player_position_']

    df = df.drop(columns=['player_position_', 'team'], errors='ignore')

    if 'player_position' in df.columns:
        df['player_position'] = df['player_position'].str.replace('amc', 'am')
    if 'match_day' in df.columns:
        # Remove 'wmd' first, then 'md'
        df['match_day'] = df['match_day'].str.replace('wmd', '', regex=False)
        df['match_day'] = df['match_day'].str.replace('md', '', regex=False)
        # Convert to numeric, set errors='coerce' to NaN for invalid values
        df['match_day'] = pd.to_numeric(df['match_day'], errors='coerce').astype('Int64')
        if df['match_day'].isnull().any():
            logging.warning('Some match_day values could not be converted to int and are set as NaN.')
    if 'duration' in df.columns:
        df['duration'] = round(df['duration'] // 60, 2)

    df = df.drop(columns=['index'], errors='ignore')
    df = df.rename(columns={'player_nam': 'player_name', 'duration': 'duration(min)'})

    on_bench_df = df[df['duration(min)'] == 0] if 'duration(min)' in df.columns else pd.DataFrame()
    df = df[df['duration(min)'] != 0] if 'duration(min)' in df.columns else df
    df = df.map(lambda x: x.strip().lower() if isinstance(x, str) else x)

    if 'player_position' in df.columns:
        df['general_position'] = df['player_position'].map({
            'gk': 'goalkeeper', 'df': 'defender', 'mf': 'midfielder', 'am': 'midfielder',
            'fw': 'forward', 'rb': 'defender', 'cb': 'defender', 'lb': 'defender',
            'rw': 'forward', 'lw': 'forward', 'cm': 'midfielder', 'dm': 'midfielder',
            'cd':'defender','fwd':'forward','dmc':'midfielder'
        })

    if 'date' in df.columns:
        df = df.sort_values(by='date', ascending=False).reset_index(drop=True)
    if not on_bench_df.empty and 'date' in on_bench_df.columns:
        on_bench_df = on_bench_df.sort_values(by='date', ascending=False).reset_index(drop=True)

    cleaned_file = os.path.join(output_folder, f"{team_identifier}_league_matches_cleaned.csv")
    benched_file = os.path.join(output_folder, f"{team_identifier}_league_matches_benched.csv")

    try:
        df.to_csv(cleaned_file, index=False)
        logging.info(f"Saved cleaned data for {team_identifier}: {cleaned_file}")
    except Exception as e:
        logging.error(f"Error saving cleaned file for {team_identifier}: {e}")

    if not on_bench_df.empty:
        try:
            on_bench_df.to_csv(benched_file, index=False)
            logging.info(f"Saved benched data for {team_identifier}: {benched_file}")
        except Exception as e:
            logging.error(f"Error saving benched file for {team_identifier}: {e}")

    return df

def generate_teamwise_cleaning_report(df, team_name):
    report_lines = []
    total_rows = len(df)
    report_lines.append(f"\n\n=== Cleaning Report for {team_name} ===")
    report_lines.append(f"Total Rows: {total_rows}")

    # 1. Duplicates
    duplicates = df.duplicated().sum()
    pct_dup = (duplicates / total_rows * 100) if total_rows else 0
    report_lines.append(f"Duplicate Rows: {duplicates} ({pct_dup:.2f}%)")

    # 2. Missing values
    report_lines.append("\n--- Missing Values by Column ---")
    for col in df.columns:
        missing = df[col].isnull().sum()
        if missing > 0:
            pct_missing = missing / total_rows * 100
            line = f"{col}: Missing {missing} ({pct_missing:.2f}%)"
            report_lines.append(line)

    # 3. Who is affected
    report_lines.append("\n--- Player Names with Missing Column Values ---")
    if 'player_name' in df.columns:
        for col in df.columns:
            missing_rows = df[df[col].isnull()]
            if not missing_rows.empty:
                players = missing_rows['player_name'].dropna().unique().tolist()
                report_lines.append(f"{col}: {players}")
    else:
        report_lines.append("No 'player_name' column to reference.")

    return "\n".join(report_lines)

# === Set up directories ===
desktop_folder = os.path.expanduser("~\\OneDrive\\Desktop\\FUFA")
league_matches_folder = os.path.join(desktop_folder, "League Matches")
report_folder = os.path.join(desktop_folder, "Logs")
if not os.path.exists(report_folder):
    os.makedirs(report_folder)

league_categories = ["UPL", "WSL"]
all_reports = []

# === Process each team ===
for league in league_categories:
    league_path = os.path.join(league_matches_folder, league)
    if not os.path.exists(league_path):
        logging.warning(f"{league} folder not found at {league_path}. Skipping.")
        continue

    for club_folder in os.listdir(league_path):
        club_path = os.path.join(league_path, club_folder)
        if os.path.isdir(club_path):
            team_identifier = club_folder.replace(" Matches", "")
            master_files = glob.glob(os.path.join(club_path, "*_league_matches_all.csv"))
            if master_files:
                master_file = master_files[0]
                logging.info(f"Processing master file: {master_file} for team: {team_identifier}")
                df_clean = clean_file(master_file, club_path, team_identifier)
                if df_clean is not None:
                    report_text = generate_teamwise_cleaning_report(df_clean, team_identifier)
                    all_reports.append(report_text)
            else:
                logging.warning(f"No master file found for team {team_identifier} in folder {club_path}.")

# === Write aggregate report ===
if all_reports:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final_report_path = os.path.join(report_folder, f"teamwise_cleaning_report_{timestamp}.txt")
    with open(final_report_path, "w") as report_file:
        report_file.write("\n".join(all_reports))
    logging.info(f"Teamwise cleaning report saved to: {final_report_path}")
else:
    logging.warning("No team cleaning reports generated.")
