#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Updated on Tue Mar 18 10:07:39 2025

@author: mounarabhi
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Define the main directory
main_directory = '/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/analysis_processed_sample'

# Get all folder paths that contain "mixed"
folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]
mixed_folder_paths = [path for path in folder_paths if "mixed" in path]
control_domains = [
    "perr.h-cdn.com", "perr.lum-sdk.io", "perr.l-agent.me", 
    "proxyjs.lum-sdk.io", "geo.brdtest.com", "clientsdk.lum-sdk.io", 
    "perr.l-err.biz", "proxyjs.luminatinet.com", "lumtest.com",	"client.earnapp.com", "earnapp.com"

]
# Initialize data structures
gateway_durations = []
relayed_durations = []
traffic_per_connection = {}
relayed_counts_per_gateway = []
simultaneous_open_counts = []
long_simultaneous_gateways_with_traffic = 0
simultaneous_traffic_counts = {}

for folder_path in mixed_folder_paths:
    relayed_path = os.path.join(folder_path, "relayed_conn_labeled.csv")
    gateway_path = os.path.join(folder_path, "proxy_conn.csv")

    if os.path.exists(relayed_path) and os.path.exists(gateway_path):
        relayed_df = pd.read_csv(relayed_path)
        gateway_df = pd.read_csv(gateway_path)
        gateway_df = gateway_df[~gateway_df['server_name'].isin(control_domains)]


        # Compute gateway connection durations
        gateway_grouped = gateway_df.groupby('conn')['ts_relative'].agg(['min', 'max']).reset_index()
        gateway_grouped['duration'] = gateway_grouped['max'] - gateway_grouped['min']
        gateway_durations.extend(gateway_grouped['duration'].tolist())

        # Compute relayed connection durations
        relayed_grouped = relayed_df.groupby('conn')['ts_relative'].agg(['min', 'max']).reset_index()
        relayed_grouped['duration'] = relayed_grouped['max'] - relayed_grouped['min']
        relayed_durations.extend(relayed_grouped['duration'].tolist())

        # Compute traffic per connection
        if 'pkt_len' in gateway_df.columns:
            gateway_traffic = gateway_df.groupby('conn')['pkt_len'].sum().to_dict()
            traffic_per_connection.update(gateway_traffic)

        if 'pkt_len' in relayed_df.columns:
            relayed_traffic = relayed_df.groupby('conn')['pkt_len'].sum().to_dict()
            traffic_per_connection.update(relayed_traffic)

        # Compute relayed counts per gateway
        for _, gateway in gateway_grouped.iterrows():
            relayed_within_gateway = relayed_grouped[(relayed_grouped['min'] >= gateway['min']) &
                                                     (relayed_grouped['max'] <= gateway['max'])]
            relayed_counts_per_gateway.append(len(relayed_within_gateway))

        # Find simultaneous connections opened within 0.01 seconds
        gateway_start_times = gateway_grouped['min'].sort_values().reset_index(drop=True)
        simultaneous_counts = np.zeros(len(gateway_start_times), dtype=int)
        
        for i, start in enumerate(gateway_start_times[:-1]):
            simultaneous_counts[i] = ((gateway_start_times[i+1:] - start) <= 0.001).sum()
            simultaneous_open_counts.append(simultaneous_counts[i])

        # Count how many simultaneous gateways longer than 5s have traffic
        for _, gateway in gateway_grouped.iterrows():
            conn_id = gateway['conn']
            if gateway['duration'] > 5 and traffic_per_connection.get(conn_id, 0) > 0:
                long_simultaneous_gateways_with_traffic += 1

        # Compute active traffic counts in simultaneous groups
        if 'ts_relative' in gateway_df.columns and 'pkt_len' in gateway_df.columns:
            gateway_grouped['total_traffic'] = gateway_df.groupby('conn')['pkt_len'].sum().values
            gateway_grouped['active'] = gateway_grouped['total_traffic'] > 10000

            for num_simultaneous in np.unique(simultaneous_counts):
                total_count = np.sum(simultaneous_counts == num_simultaneous)
                active_count = np.sum((simultaneous_counts == num_simultaneous) & (gateway_grouped['active']))
                simultaneous_traffic_counts[num_simultaneous] = (total_count, active_count)


# Convert to arrays for plotting
simultaneous_values = sorted(simultaneous_traffic_counts.keys())
total_connections = [simultaneous_traffic_counts[k][0] for k in simultaneous_values]
active_connections = [simultaneous_traffic_counts[k][1] for k in simultaneous_values]

# Bar plot of Simultaneous Connections vs. Active Connections
plt.figure(figsize=(8, 5))
plt.bar(simultaneous_values, total_connections, label="Total Simultaneous Connections", color="gray", alpha=0.6)
plt.bar(simultaneous_values, active_connections, label="Active Connections (>5kB)", color="blue", alpha=0.8)
plt.xlabel("Number of Simultaneous Connections")
plt.ylabel("Count")
plt.title("Active Gateway Connections with Traffic vs. Simultaneous Openings")
plt.legend()
plt.grid(True)
plt.show()


# Convert lists to NumPy arrays
gateway_durations = np.array(gateway_durations)
simultaneous_open_counts = np.array(simultaneous_open_counts)
relayed_counts_per_gateway = np.array(relayed_counts_per_gateway)

# Compute average relayed connections per connection
avg_relayed_per_gateway = np.mean(relayed_counts_per_gateway) if len(relayed_counts_per_gateway) > 0 else 0

# --- PLOTS ---

# 1. CDF of Gateway Connection Duration
sorted_gateway_durations = np.sort(gateway_durations)
cdf_gateway = np.arange(1, len(sorted_gateway_durations) + 1) / len(sorted_gateway_durations)
 
plt.figure(figsize=(8, 5))
plt.scatter(sorted_gateway_durations, cdf_gateway, marker ='o',s=6)
plt.xlabel("Gateway Connection Duration (seconds)", fontsize=12)
plt.ylabel("CDF", fontsize=12)
plt.xlim([-1,2000])
plt.title("CDF of Gateway Connection Duration")
plt.grid(True)
plt.show()
# 2. CDF of Simultaneous Connections Opened (Sorted)
sorted_simultaneous_open_counts = np.sort(simultaneous_open_counts)
cdf_simultaneous = np.arange(1, len(sorted_simultaneous_open_counts) + 1) / len(sorted_simultaneous_open_counts)

plt.figure(figsize=(8, 5))
plt.scatter(sorted_simultaneous_open_counts, cdf_simultaneous, color="green")
plt.xlabel("Number of Simultaneous Connections")
plt.ylabel("CDF")
plt.title("CDF of Simultaneous Gateway Connection Openings (Sorted)")
plt.grid(True)
plt.show()


# 4. Print Statistics
print(f"Average Relayed Connections per Gateway: {avg_relayed_per_gateway:.2f}")
print(f"Simultaneous Gateways (>5s duration) with Traffic: {long_simultaneous_gateways_with_traffic}")
