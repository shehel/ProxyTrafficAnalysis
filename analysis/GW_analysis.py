#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 13:56:53 2024

@author: mounarabhi
"""
import pandas as pd
import matplotlib.pyplot as plt
import re
import os
from collections import Counter
import numpy as np
from scipy.stats import mode

def extract_ip(server_name):
    match = re.search(r'(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})', server_name)
    if match:
        return match.group(1).replace('-', '.')
    return None

# Unwanted gateway domains
control_domains = [
    "perr.h-cdn.com", "perr.lum-sdk.io", "perr.l-agent.me", 
    "proxyjs.lum-sdk.io", "geo.brdtest.com", "clientsdk.lum-sdk.io", 
    "perr.l-err.biz", "proxyjs.luminatinet.com", "lumtest.com",	"client.earnapp.com", "earnapp.com"

]

main_directory = '/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/analysis_processed_sample'
folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]
mixed_folder_paths = [path for path in folder_paths if "mixed" in path]
all_data = []
all_ips = []
connection_counts = []
time_successive_proxy = []
connection_details = []
all_stats = []

for folder_path in mixed_folder_paths:
    gateway_path = os.path.join(folder_path, "proxy_conn.csv")

    try:
        proxy_connection = pd.read_csv(gateway_path)
    except FileNotFoundError:
        print("File not found. Skipping.")
        continue

    # Filter out rows with unwanted gateway domains
    proxy_connection = proxy_connection[~proxy_connection['server_name'].isin(control_domains)]
    
    proxy_conn_out = proxy_connection[(proxy_connection['src_ip'] == '10.0.2.16') | (proxy_connection['src_ip'] == '10.0.2.15')]
    unique_proxy_conns = proxy_conn_out['conn'].unique()
    sorted_unique_connections = sorted(unique_proxy_conns, key=lambda x: int(x.split('_')[2]))
    
    connection_counter = 1
    i = 0
    while i < len(sorted_unique_connections) - 1:
        current_conn = sorted_unique_connections[i]
        conn_group = proxy_conn_out[proxy_conn_out['conn'] == current_conn]
        start_end_times = conn_group['ts_relative'].agg(['min', 'max'])
        start_1, end_1 = start_end_times['min'], start_end_times['max']
        duration = end_1 - start_1
        gateway_name = conn_group['server_name'].iloc[0]
        
        connection_details.append({
            'folder': folder_path,
            'gateway_name': gateway_name,
            'time_in': start_1,
            'time_out': end_1,
            'duration': duration
        })
        
        # Find all subsequent connections within 0.1s
        j = i + 1
        k = i
        while j < len(sorted_unique_connections):
            prev_conn = sorted_unique_connections[k]
            prev_start = proxy_conn_out[proxy_conn_out['conn'] == prev_conn]['ts_relative'].min()
            next_conn = sorted_unique_connections[j]
            next_start = proxy_conn_out[proxy_conn_out['conn'] == next_conn]['ts_relative'].min()
            if abs(next_start - prev_start) < 0.05:
                connection_counter += 1
                j += 1  # Skip over this connection
                k += 1
            else:
                break
        
        connection_counts.append(connection_counter)
        connection_counter = 1
        i = j  # Move to the next unprocessed connection

    if connection_counter > 0:
        connection_counts.append(connection_counter)

    grouped_conn_in = proxy_connection.groupby('conn')['server_name'].unique().reset_index()
    grouped_conn_in['folder'] = folder_path
    all_data.append(grouped_conn_in)

    for server_list in grouped_conn_in['server_name']:
        for server in server_list:
            ip = extract_ip(server)
            if ip:
                all_ips.append(ip)

final_df = pd.concat(all_data, ignore_index=True)
final_df.columns = ['conn', 'unique_server_names', 'instance']
connection_df = pd.DataFrame(connection_details)

ip_counts = Counter(all_ips)
redundant_ips_df = pd.DataFrame(ip_counts.items(), columns=['IP', 'Count']).sort_values(by='Count', ascending=False)

# Visualization for redundant IPs and other plots
top_n = 32
top_redundant_ips_df = redundant_ips_df.head(top_n)
plt.figure(figsize=(10, 6))
plt.bar(top_redundant_ips_df['IP'], top_redundant_ips_df['Count'], width=0.4, color='black')
plt.xlabel('IP Address', fontsize=15)
plt.ylabel('Occurence', fontsize=15)
#plt.title('Redundancy of gateways IPs')
plt.xticks(rotation=45, ha='right', fontsize=14)
plt.tight_layout()
plt.savefig('redundancy_of_gateways_ips.pdf', format='pdf')
plt.show()

print(connection_df['duration'].describe())

connection_counts = np.array(connection_counts)
sorted_counts = np.sort(connection_counts)
cdf = np.arange(1, len(sorted_counts) + 1) / len(sorted_counts)
plt.figure(figsize=(10, 6))
plt.plot(sorted_counts, cdf, marker='.', linestyle='none', color='black')
plt.xticks(np.arange(0, 7, 1))
plt.xlabel("Number of simultaneous gateways (within 0.05s)", fontsize=18)
plt.ylabel("CDF", fontsize=16)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
#plt.title("Cumulative Distribution Function of Connections to Gateway", fontsize=15)
plt.grid(True)
plt.savefig('cdf_of_gateway_conn_per_proxy.pdf', format='pdf')
plt.show()

plt.figure(figsize=(10, 6))
plt.hist(connection_counts, bins=range(1, max(connection_counts) + 2), align='left', width=0.6, color='black')
plt.xlabel("Number of Gateways Opened per Proxy Connection", fontsize=18)
plt.ylabel("Count", fontsize=16)
# Tick font sizes
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
#plt.title("Distribution of # of Connections to Gateway", fontsize=15)
plt.xticks(range(1, max(connection_counts) + 1))
plt.savefig('number_of_gateway_conn_per_proxy.pdf', format='pdf')
plt.show()

"""
plt.figure(figsize=(8, 6))
plt.boxplot(connection_df['duration'], showfliers=False)
plt.xlabel("Duration of Gateway Connection")
plt.title("Box Plot of Gateway Connection Durations")
plt.show()
"""

data = connection_df['duration'].dropna()  # Drop NaN values
sorted_data = np.sort(data)
cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)

# Find the mode (duration that occurs most frequently)
mode_result = mode(data)
mode_duration = mode_result[0]  # Access the mode value correctly

# Plot the CDF
plt.figure(figsize=(8, 6))
plt.plot(sorted_data, cdf, marker='.', linestyle='none')
# Mark the mode on the plot
#plt.axvline(x=mode_duration, color='r', linestyle='--')
# Annotate the mode value on the x-axis
#plt.text(mode_duration, -0.13, f'{mode_duration:.2f}', color='r', ha='center', va='bottom', fontsize=10)
plt.xlabel("Duration of gateway connection (s)", fontsize=15)
plt.ylabel("CDF", fontsize=15)
plt.xlim([-30,1000])
plt.grid(True)
plt.savefig('cdf_of_gateway_duration.pdf', format='pdf')

plt.show()
