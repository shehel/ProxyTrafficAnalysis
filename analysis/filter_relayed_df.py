#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 12:08:33 2025

@author: mrabhi
"""
import os
import pandas as pd

main_directory = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/processed_new"
pcap_directory = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/analysis_sample"
analysis_directory = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/analysis_processed_sample"

# Load the list of domains to keep
relay_domain_file = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/random_100_relayed_domains.txt"
with open(relay_domain_file, "r") as f:
    relay_domains = set(line.strip() for line in f)

# Get all subdirectories containing "mixed"
main_mixed_folders = {
    folder for folder in os.listdir(main_directory)
    if os.path.isdir(os.path.join(main_directory, folder)) and "mixed" in folder
}

# Get 'mixed' folders from analysis_directory
analysis_mixed_folders = {
    folder for folder in os.listdir(analysis_directory)
    if os.path.isdir(os.path.join(analysis_directory, folder)) and "mixed" in folder
}

# Remove intersection (exclude already analyzed folders)
filtered_main_mixed_folders = main_mixed_folders - analysis_mixed_folders

# Get full paths
mixed_folder_paths = [
    os.path.join(main_directory, folder) for folder in filtered_main_mixed_folders
]

filtered_data = []

for folder_path in mixed_folder_paths:
    print(f"Processing: {folder_path}")
    relayed_path = os.path.join(folder_path, "relayed_conn_labeled.csv")

    if os.path.exists(relayed_path):
        try:
            relayed_df = pd.read_csv(relayed_path)

            # Deduplicate by 'conn' first
            deduped_df = relayed_df.groupby("conn").first().reset_index()

            # Filter by server_name in relay_domains
            filtered_df = deduped_df[deduped_df["server_name"].isin(relay_domains)]

            # Track source folder
            filtered_df["folder_path"] = folder_path

            # Append to result list
            filtered_data.append(filtered_df)

        except Exception as e:
            print(f"Error reading {relayed_path}: {e}")

# Combine all filtered data into one DataFrame
if filtered_data:
    final_df = pd.concat(filtered_data, ignore_index=True)
    
    # Save result
    output_path = os.path.join(main_directory, "relayed_rq3.csv")
    final_df.to_csv(output_path, index=False)
    print(f"\n✅ Filtered data saved to: {output_path}")
    
    # Optional: show domain counts
    print("\n=== Server Name Occurrences (Grouped by conn) ===")
    counts = final_df["server_name"].value_counts()
    print(counts)
else:
    print("\n⚠️ No matching server_name entries found.")
