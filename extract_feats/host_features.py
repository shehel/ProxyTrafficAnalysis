#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 11:13:23 2024

@author: mounarabhi
"""
import pandas as pd
from datetime import datetime

def calc_seconds(ts_list):
    return ts_list[-1] - ts_list[0]

def extract_features_by_conn(file_path, gw=True):
    # Load the CSV
    df = pd.read_csv(file_path)
    

    # Group by 'conn'
    grouped = df.groupby('conn')

    # Store features for each connection
    all_features = []
    group_start_times = []
    all_durations=[]
    for conn_name, group in grouped:
        features = {'conn': conn_name}
        # Sort by timestamp for accurate calculations
        group = group.sort_values(by='conn')

        # Total connections
        features['total_connections'] = len(group)  # 1

        # Connection rate: total connections per second
        # Connection rate: total connections per second
        total_time = calc_seconds(group['ts_relative'].tolist())
        features['connection_rate'] = len(group) / total_time if total_time > 0 else 0  # 2

        # Unique destination ports
        unique_dports = group['dst_port'].nunique()
        features['unique_dports'] = unique_dports  # 3

        # Most common destination port
        most_common_dport = group['dst_port'].mode()[0] if not group['dst_port'].empty else 0
        features['most_common_dst_port'] = most_common_dport  # 4

        # Duration analysis
        first_ts=group['ts_relative'].iloc[0]
        last_ts=group['ts_relative'].iloc[-1]
        durations = last_ts-first_ts
        features['duration']=durations
        # long duration connections (more  than 9 minutes)
        #group_duration=group["ts_relative"].iloc[-1]-group["ts_relative"].iloc[0]
        #long_durations =  1 if group_duration >= 9 * 60 else 0 
        #features['long_durations'] = long_durations  # 8

        # Time gaps between connections
        group_start_times.append(group['ts_relative'].iloc[0])  # First timestamp in the group


        # Traffic analysis
        total_pkts = group['pkt_len']
        features['mean_total_pkts'] = total_pkts.mean() if not total_pkts.empty else 0  # 10
        features['median_total_pkts'] = total_pkts.median() if not total_pkts.empty else 0  # 11
        features['mode_total_pkts'] = total_pkts.mode()[0] if not total_pkts.empty else 0  # 12

        total_data = group['pkt_len'] 
        features['mean_total_data'] = total_data.mean() if not total_data.empty else 0  # 13
        features['median_total_data'] = total_data.median() if not total_data.empty else 0  # 14
        features['mode_total_data'] = total_data.mode()[0] if not total_data.empty else 0  # 15
        
        
        if gw==True:
            group_sent=group[(group['dst_ip']=='10.0.2.16')| (group['dst_ip']=='10.0.2.15')]
            group_recv=group[(group['src_ip']=='10.0.2.16')| (group['src_ip']=='10.0.2.15')]
        else:
            group_recv=group[(group['dst_ip']=='10.0.2.16')| (group['dst_ip']=='10.0.2.15')]
            group_sent=group[(group['src_ip']=='10.0.2.16')| (group['src_ip']=='10.0.2.15')]
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
    for i, features in enumerate(all_features[:-1]):  # Exclude the last group because it has no gap
        features['gap_between_conns'] = time_diffs[i]  # 21s
    if all_features:
        all_features[-1]['gap_between_conns'] = 0  # Set last connection's gap to 0
    # Convert the list of dictionaries to a DataFrame for easier analysis
    features_df = pd.DataFrame(all_features)
    return features_df

# Example usage
avg_durations=[]
suffixes=["low","high"]
for suffix in suffixes:
    for i in range(33):
        csv_path = "proxy_conn_"+str(i)+"_"+suffix+".csv"
        features_df = extract_features_by_conn(csv_path,gw=False)
        avg_durations.append(features_df['duration'].mean())
#print(features_df)

# Save to CSV
#features_df.to_csv("connection_features.csv", index=False)
#average duration for background traffic is 191.463
#average duration for proxy traffic is 465.602
