import csv
import os
import subprocess
from pathlib import Path
import pandas as pd
import pdb


def main():
    # Path where the CSV is located
    dataset_csv = "dataset_info.csv"

    # The base directory for your files
    BASE_PATH = Path("../ProxyData/local_pcaps/")
    
    # List containing name of all files
    all_names = []
    
    # Read the dataset CSV
    with open(dataset_csv, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Only consider rows where set == 'train'
            if row['set'].strip().lower() == 'train':
                file_name = row['subfolder_name'].strip()
                
                # Construct the full paths
                background_path = os.path.join(BASE_PATH, file_name, "background_conn_labeled.csv")
                relayed_path = os.path.join(BASE_PATH, file_name, "relayed_conn_labeled.csv")

                # Append to file name list
                all_names.append(background_path)
                all_names.append(relayed_path)
                
                # Call extract_feats/get_all_features_lib_lbl.py with each path
                subprocess.run(["python", "extract_feats/get_all_features_lim_lbl.py", background_path])
                subprocess.run(["python", "extract_feats/get_all_features_lim_lbl.py", relayed_path])

    # Merge all csv files
    relayed_csvs = [f for f in all_names if "relayed" in f]
    bg_csvs = [f for f in all_names if "background" in f]
    
    pdb.set_trace()

    merged_relayed_df = pd.concat([pd.read_csv(f) for f in relayed_csvs], ignore_index=True)
    merged_bg_df = pd.concat([pd.read_csv(f) for f in bg_csvs], ignore_index=True)

    merged_relayed_df['label'] = 1
    merged_bg_df['label'] = 0

    merged_df = pd.concat([merged_relayed_df, merged_bg_df], ignore_index=True)
    
    pdb.set_trace()
    
    merged_df.to_csv("content/subset_features_03_18/train/all_features.csv")

if __name__ == "__main__":
    main()
