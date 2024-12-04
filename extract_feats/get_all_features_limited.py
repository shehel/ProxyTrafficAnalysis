#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 15:05:12 2024

@author: mounarabhi
"""
from extract_features import get_features
from host_features_limited import extract_features_by_conn
import csv
import pandas as pd

fnames = ["intertimestats","timestats","number_pkts","thirtypkts","stdconc","avgconc","avg_per_sec","std_per_sec","avg_order_in","avg_order_out","std_order_in",
         "std_order_out","medconc","med_per_sec","min_per_sec","max_per_sec","maxconc","perc_in","perc_out","altconc","alt_per_sec","sum_altconc","sum_alt_per_sec","sum_intertimestats",
         "sum_timestats","sum_number_pkts"]
Features_names=["max_in", "max_out","max_total","avg_in","avg_out","avg_total","std_in","std_out","std_total","75th_percentile_in","75th_percentile_out","75th_percentile_total",
                "nb_pkts_in","nb_pkts_out","nb_pkts_total",
                "nb_pkts_in_f30","nb_pkts_out_f30","nb_pkts_in_l30","nb_pkts_out_l30","std_pkt_conc_out20", "avg_pkt_conc_out20","avg_per_sec","std_per_sec","avg_order_in",
                "avg_order_out","std_order_in","std_order_out","medconc","med_per_sec","min_per_sec","max_per_sec","maxconc","perc_in","perc_out","sum_altconc",
                "sum_alt_per_sec","sum_number_pkts","sum_intertimestats"]
#Features_names.extend([f"altconc_{i+1}" for i in range(20)])       # 20 altconc
#Features_names.extend([f"alt_per_sec_{i+1}" for i in range(20)])   # 20 alt_per_sec
#Features_names.extend([f"conc_{i+1}" for i in range(60)])          # 60 conc
features_list = []

for number in range(33):
    print("n=",number)
    suffix = "low"
    gw = False
    file_path = "normal_conn_" + str(number) + "_" + suffix + ".csv"
    feats = {}
    

    pkt_limit = 50  # Set the packet limit
    
    with open(file_path, 'r') as f:
        all_pkts = list(csv.reader(f, delimiter=','))
        curr_conn = ''
        conn_count = 0
        feats = {}
        conn_pkts = []  # Temporary storage for packets of the current connection
    
        for idx, pkt in enumerate(all_pkts):
            if idx == 0:
                continue  # Skip the header row
    
            conn_name = pkt[0]
    
            if conn_name != curr_conn:  # New connection encountered
                # Process the previous connection if it satisfies the packet limit
                if conn_pkts and len(conn_pkts) >= pkt_limit:
                    features = get_features(conn_pkts[:pkt_limit], curr_conn, limit=0)
                    if features:
                        full_conn_name = curr_conn
                        print(full_conn_name)
                        feats[full_conn_name] = features
    
                # Start processing the new connection
                conn_pkts = [pkt]
                curr_conn = conn_name
                conn_count += 1
            else:
                # Add packet to the current connection
                conn_pkts.append(pkt)
    
        # Final connection check (for the last connection in the file)
        if conn_pkts and len(conn_pkts) >= pkt_limit:
            features = get_features(conn_pkts[:pkt_limit], curr_conn, limit=0)
            if features:
                full_conn_name = curr_conn
                print(full_conn_name)
                feats[full_conn_name] = features

    
    # Extract features from the connection
    features_host = extract_features_by_conn(file_path, gw)
    
    # Check if features_host contains the 'conn' column
    if 'conn' in features_host.columns:
        # Convert the feats dictionary to a DataFrame and expand the '150_features'
        features_150_df = pd.DataFrame(list(feats.items()), columns=['conn', '150_features'])
        features_150_expanded = features_150_df['150_features'].apply(pd.Series)
        features_150_expanded.columns = Features_names
        features_150_final = pd.concat([features_150_df['conn'], features_150_expanded], axis=1)
    
        # Check if 'conn' exists in both DataFrames before merging
        if 'conn' in features_150_final.columns:
            # Merge the DataFrames on 'conn'
            concatenated_features = pd.merge(features_host, features_150_final, on='conn', how='inner')
            concatenated_features['number'] = number
            features_list.append(concatenated_features)
        else:
            # Handle case when 'conn' is missing in features_150_final
            print(f"Warning: 'conn' column is missing in features_150_final for {file_path}. Skipping merge.")
    else:
        # Handle case when 'conn' is missing in features_host
        print(f"Warning: 'conn' column is missing in features_host for {file_path}. Skipping merge.")

# After processing all files, concatenate the feature list
if features_list:
    final_features = pd.concat(features_list, axis=0, ignore_index=True)
    final_features.to_csv('features_lim_' + suffix + '_nrml.csv', index=False)
else:
    print("No valid features to save.")

