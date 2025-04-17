#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 08:30:51 2025

@author: mrabhi
"""

import os
import pandas as pd
from collections import defaultdict

main_directory = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/processed_new"
analysis_directory = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/analysis_processed_sample"

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

# Remove intersection
filtered_main_mixed_folders = main_mixed_folders - analysis_mixed_folders

# Full paths
mixed_folder_paths = [
    os.path.join(main_directory, folder) for folder in filtered_main_mixed_folders
]

# Load the list of domains to keep
relay_domain_file = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/random_100_relayed_domains.txt"
with open(relay_domain_file, "r") as f:
    relay_domains = set(line.strip() for line in f)
# Count server_name occurrences (grouped by conn)
server_name_counts = defaultdict(int)

for folder_path in mixed_folder_paths:
    relayed_path = os.path.join(folder_path, "relayed_conn_labeled.csv")
    
    if os.path.exists(relayed_path):
        try:
            df = pd.read_csv(relayed_path)
            
            # Group by conn to deduplicate
            grouped = df.groupby("conn").first().reset_index()
            # After grouping
            grouped = grouped[grouped["server_name"].isin(relay_domains)]

            # Count each server_name
            counts = grouped["server_name"].value_counts()

            for server_name, count in counts.items():
                server_name_counts[server_name] += count

        except Exception as e:
            print(f"Error reading {relayed_path}: {e}")

# Display results
print("\n=== Total server_name occurrences (grouped by conn) ===")
for server_name, count in sorted(server_name_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"{server_name}: {count}")
