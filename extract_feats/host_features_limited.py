#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 14:55:46 2024

@author: mounarabhi
"""
import pandas as pd

def calc_seconds(ts_list):
    return ts_list[-1] - ts_list[0]

def extract_features_by_conn(file_path, gw=True, max_pkts=50):
    # Load the CSV
    df = pd.read_csv(file_path)
    
    # Group by 'conn'
    grouped = df.groupby('conn')

    # Store features for each connection
    all_features = []
    group_start_times = []

    for conn_name, group in grouped:
        # Skip connections with fewer than `min_rows` rows
        if len(group) < max_pkts:
            continue
        group = group.head(max_pkts)

        features = {'conn': conn_name}
        # Sort by timestamp for accurate calculations
        group = group.sort_values(by='ts_relative')

        # Total connections
        #features['total_connections'] = len(group)  # 1 (NOT USED AS WE LIMIT TO 5) PKTS ONLY

        # packets rates ( #of pkts/ duration)
        total_time = calc_seconds(group['ts_relative'].tolist())
        features['pkts_rate'] = len(group) / total_time if total_time > 0 else 0  # 2

    
        # Duration analysis
        first_ts = group['ts_relative'].iloc[0]
        last_ts = group['ts_relative'].iloc[-1]
        durations = last_ts - first_ts
        features['duration'] = durations

        # Time gaps between connections
        group_start_times.append(first_ts)  # First timestamp in the group

        # volume features
        total_pkts = group['pkt_len']
        features['mean_total_pkts'] = total_pkts.mean() if not total_pkts.empty else 0  # 10
        features['median_total_pkts'] = total_pkts.median() if not total_pkts.empty else 0  # 11
        features['mode_total_pkts'] = total_pkts.mode()[0] if not total_pkts.empty else 0  # 12


        if gw:
            group_sent = group[(group['dst_ip'] == '10.0.2.16') | (group['dst_ip'] == '10.0.2.15')]
            group_recv = group[(group['src_ip'] == '10.0.2.16') | (group['src_ip'] == '10.0.2.15')]
        else:
            group_recv = group[(group['dst_ip'] == '10.0.2.16') | (group['dst_ip'] == '10.0.2.15')]
            group_sent = group[(group['src_ip'] == '10.0.2.16') | (group['src_ip'] == '10.0.2.15')]

        total_sent = group_sent['pkt_len']
        features['mean_bytes_sent'] = total_sent.mean() if not total_sent.empty else 0  # 16
        features['median_bytes_sent'] = total_sent.median() if not total_sent.empty else 0  # 17
        features['mode_bytes_sent'] = total_sent.mode()[0] if not total_sent.empty else 0  # 18

        total_recv = group_recv['pkt_len']
        features['mean_bytes_recv'] = total_recv.mean() if not total_recv.empty else 0  # 19
        features['median_bytes_recv'] = total_recv.median() if not total_recv.empty else 0  # 20
        features['mode_bytes_recv'] = total_recv.mode()[0] if not total_recv.empty else 0  # 21

        # Append features for this connection
        all_features.append(features)

    # Calculate time gaps between connection groups
    group_start_times = sorted(group_start_times)
    time_diffs = [abs(group_start_times[i + 1] - group_start_times[i]) for i in range(len(group_start_times) - 1)]

    # Add avg_time_gap 
    for i, features in enumerate(all_features[:-1]):  
        features['gap_between_conns'] = time_diffs[i]  
    if all_features:
        all_features[-1]['gap_between_conns'] = 0  # Set last connection's gap to 0

    # Convert the list of dictionaries to a DataFrame for easier analysis
    features_df = pd.DataFrame(all_features)
    return features_df


        
