#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 09:13:57 2025

@author: mrabhi
"""
import os
import pandas as pd
from collections import Counter

# Define the main directory
main_directory = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/processed_new"

# Get all subdirectories
folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]

# Filter only "mixed" folders
mixed_folder_paths = [path for path in folder_paths if "mixed" in path]

# List to store all domains
all_domains = []

# Iterate through mixed folders and extract domains
for folder_path in mixed_folder_paths:
    relayed_path = os.path.join(folder_path, "relayed_conn_labeled.csv")
    
    if os.path.exists(relayed_path):  # Check if file exists
        relayed_conn = pd.read_csv(relayed_path)
        
        if "server_name" in relayed_conn.columns:  # Ensure column exists
            all_domains.extend(relayed_conn["server_name"].dropna().tolist())

# Save domains to a CSV
unique_domains = list(set(all_domains))
output_csv = "all_domains.csv"
pd.DataFrame(all_domains, columns=["domain"]).to_csv(output_csv, index=False)
output_csv1 = "unique_domains.csv"
pd.DataFrame(unique_domains, columns=["domain"]).to_csv(output_csv1, index=False)
# Count occurrences and get top 10 most repeated domains
domain_counts = Counter(all_domains)
top_domains = domain_counts.most_common(20)

# Print results
print("Top 20 most repeated domains:")
for domain, count in top_domains:
    print(f"{domain}: {count}")
