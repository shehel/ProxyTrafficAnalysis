#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 09:27:30 2025

@author: mrabhi
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter


main_directory = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/analysis_processed_sample"

# Get all subdirectories
folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]

# Filter only "mixed" folders
mixed_folder_paths = [path for path in folder_paths if "mixed" in path]

total_relayed_connections = 0
total_duration = 0
total_volume = 0
conn_counts = []
all_durations = []  # Store durations across all PCAPs
server_name_counter = Counter()
for folder_path in mixed_folder_paths:
    relayed_path = os.path.join(folder_path, "relayed_conn_labeled.csv")

    if os.path.exists(relayed_path):
        relayed_df = pd.read_csv(relayed_path)
        if relayed_df.empty:
            continue
        unique_conns = relayed_df.groupby('conn').first().reset_index()
        server_name_counter.update(unique_conns['server_name'].dropna())
        # Compute duration and volume per server_name
        relayed_grouped = relayed_df.groupby('conn').agg(
            duration=('ts_relative', lambda x: x.max() - x.min()),  # Duration per server
            volume=('pkt_len', 'sum'),  # Total packet volume per server
            server_name=('server_name', 'first')
        ).reset_index()
        relayed_grouped.volume=relayed_grouped.volume/1024
        num_relayed_connections = len(relayed_grouped)
        total_relayed_connections += num_relayed_connections
        conn_counts.append(num_relayed_connections)
        total_duration += relayed_grouped['duration'].sum()
        total_volume += relayed_grouped['volume'].sum()

        # Collect durations from this PCAP
        all_durations.extend(relayed_grouped['duration'].tolist())
for server_name, count in server_name_counter.items():
    print(f"{server_name}: {count}")
# Compute averages
avg_relayed_per_pcap = total_relayed_connections / len(mixed_folder_paths) if mixed_folder_paths else 0
avg_duration = total_duration / total_relayed_connections if total_relayed_connections > 0 else 0
avg_volume = (total_volume / total_relayed_connections) / 1024 if total_relayed_connections > 0 else 0

# Print results
print(f"Total number of relayed connections: {total_relayed_connections}")
print(f"Average number of relayed connections per PCAP: {avg_relayed_per_pcap:.2f}")
print(f"Average length (duration) of relayed connections: {avg_duration:.2f} seconds")
print(f"Average volume of relayed connections: {avg_volume:.2f} kB")

# Ensure all_durations is not empty before plotting
if all_durations:
    median_duration = np.median(all_durations)
    percentile_25 = np.percentile(all_durations, 25)
    percentile_75 = np.percentile(all_durations, 75)

    print(f"Median Connection Duration: {median_duration:.2f} seconds")
    print(f"25th Percentile: {percentile_25:.2f} seconds")
    print(f"75th Percentile: {percentile_75:.2f} seconds")

    # Plot histogram
    all_durations_sorted = np.sort(all_durations)
    cdf = np.arange(1, len(all_durations_sorted) + 1) / len(all_durations_sorted)
    
    # Plot CDF
    plt.figure(figsize=(10, 5))
    sns.lineplot(x=all_durations_sorted, y=cdf, color='blue', label='CDF')
    plt.axvline(median_duration, color='red', linestyle='dashed', linewidth=2, label=f'Median: {median_duration:.2f}s')
    plt.xlabel("Connection Duration (s)", fontsize=18)
    plt.xlim([-100,500])
    plt.ylabel("CDF", fontsize=18)
    # Tick font sizes
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.legend()
    plt.grid()
    plt.savefig('relayed_conn_cdf.pdf', format='pdf')
    
    plt.show()
else:
    print("No relayed connections found across PCAPs.")
