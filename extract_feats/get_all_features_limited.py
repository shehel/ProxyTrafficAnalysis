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
import argparse

def enter_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefix', metavar='the prefix of filename', help='input the prefix of filename (proxy or normal)', required=True)
    parser.add_argument('--number', metavar='number of pcap instance used to extract features', help='input the number of pcap instance used to extract features', required=True)
    parser.add_argument('--suffix', metavar='the suffix of filename', help='input the suffix of filename (low, high, medium)', required=True)
    parser.add_argument('--limit', metavar='the limit of number of pkts to be considered for feature extraction', help='the min limit of pkts number that will be used for extracting features', required=True)
    args = parser.parse_args()
    return args

def main():

    args = enter_cmd_args()
    prefix = args.prefix
    number = int(args.number)
    suffix = args.suffix
    pkt_limit = int(args.limit)
    
    Features_names=["max_in", "max_out","max_total","avg_in","avg_out","avg_total","std_in","std_out","std_total","75th_percentile_in","75th_percentile_out","75th_percentile_total",
                    "nb_pkts_in","nb_pkts_out","nb_pkts_total",
                    "nb_pkts_in_f30","nb_pkts_out_f30","nb_pkts_in_l30","nb_pkts_out_l30","std_pkt_conc_out20", "avg_pkt_conc_out20","avg_per_sec","std_per_sec","avg_order_in",
                    "avg_order_out","std_order_in","std_order_out","medconc","med_per_sec","min_per_sec","max_per_sec","maxconc","perc_in","perc_out","sum_altconc",
                    "sum_alt_per_sec","sum_number_pkts","sum_intertimestats"]
    features_list = []

    
    for i in range(number):
        if prefix== "proxy":
            gw = True
            file_path = "proxy_conn_" + str(i) + "_" + suffix + ".csv"
        elif prefix=="normal":
            gw = False
            file_path = "normal_conn_" + str(i) + "_" + suffix + ".csv"

 
        feats = {}
        
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
            features_k_df = pd.DataFrame(list(feats.items()), columns=['conn', 'k_features'])
            features_k_expanded = features_k_df['k_features'].apply(pd.Series)
            features_k_expanded.columns = Features_names
            features_k_final = pd.concat([features_k_df['conn'], features_k_expanded], axis=1)
        
            # Check if 'conn' exists in both DataFrames before merging
            if 'conn' in features_k_final.columns:
                # Merge the DataFrames on 'conn'
                concatenated_features = pd.merge(features_host, features_k_final, on='conn', how='inner')
                concatenated_features['pcap_nb'] = i
                features_list.append(concatenated_features)
            else:
                # Handle case when 'conn' is missing in features_k_final
                print(f"Warning: 'conn' column is missing in features_final for {file_path}. Skipping merge.")
        else:
            # Handle case when 'conn' is missing in features_host
            print(f"Warning: 'conn' column is missing in features_host for {file_path}. Skipping merge.")
    
    # After processing all files, concatenate the feature list
    if features_list:
        final_features = pd.concat(features_list, axis=0, ignore_index=True)
        final_features.to_csv('features_lim_' + suffix + '_gw.csv', index=False)
    else:
        print("No valid features to save.")
        
if __name__ == "__main__":
    main()
    
