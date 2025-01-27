#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 15:05:12 2024

@author: mounarabhi
"""
from extract_features import get_features
from host_features_limited import extract_features_by_conn
from rtt_tls_feature import get_rtt_feature
import csv
import pandas as pd
import argparse
import os
import random
import warnings
warnings.filterwarnings("ignore")
def extract_feature_per_folder(folder_paths,set_name,pkt_limit):
    """

    Features_names=["max_in", "max_out","max_total","avg_in","avg_out","avg_total","std_in","std_out","std_total","75th_percentile_in","75th_percentile_out","75th_percentile_total",
                    "nb_pkts_in","nb_pkts_out","nb_pkts_total",
                    "nb_pkts_in_f30","nb_pkts_out_f30","nb_pkts_in_l30","nb_pkts_out_l30","std_pkt_conc_out20", "avg_pkt_conc_out20","avg_per_sec","std_per_sec","avg_order_in",
                    "avg_order_out","std_order_in","std_order_out","medconc","med_per_sec","min_per_sec","max_per_sec","maxconc","perc_in","perc_out","sum_altconc",
                    "sum_alt_per_sec","sum_number_pkts","sum_intertimestats"]
    """
    Features_names=["max_in", "max_out","max_total","avg_in","avg_out","avg_total","std_in","std_out","std_total","75th_percentile_in","75th_percentile_out","75th_percentile_total",
                    "25th_percentile_in_time", "50th_percentile_in_time", "75th_percentile_in_time", "100th_percentile_in_time",     "25th_percentile_out_time", "50th_percentile_out_time", "75th_percentile_out_time", "100th_percentile_out_time", 
                    "25th_percentile_total_time", "50th_percentile_total_time", "75th_percentile_total_time", "100th_percentile_total_time",  # Time stats
                    "nb_pkts_in","nb_pkts_out","nb_pkts_total",
                    "nb_pkts_in_f30","nb_pkts_out_f30","nb_pkts_in_l30","nb_pkts_out_l30","std_pkt_conc_out20", "avg_pkt_conc_out20","avg_per_sec","std_per_sec","avg_order_in",
                    "avg_order_out","std_order_in","std_order_out","medconc","med_per_sec","min_per_sec","max_per_sec","maxconc","perc_in","perc_out","sum_altconc",
                    "sum_alt_per_sec","sum_number_pkts","sum_intertimestats"]
    
    Features_names.extend([f"altconc_{i+1}" for i in range(20)])       # 20 altconc
    Features_names.extend([f"alt_per_sec_{i+1}" for i in range(20)])   # 20 alt_per_sec
    Features_names.extend([f"conc_{i+1}" for i in range(60)])          # 60 conc
    prefixes=["relayed","background"]
    for prefix in prefixes:
        features_list = []
        for i in range( len(folder_paths)):
            folder_name = folder_paths[i]
            print(f"Processing folder {i+1}/{len(folder_paths)}: {folder_name}")
    
            if prefix== "relayed":
                file_path = folder_name+'/relayed_conn_labeled.csv'
            elif prefix=="background":
                file_path =folder_name+'/background_conn_labeled.csv'
    
     
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
                        feats[full_conn_name] = features
        
            
            # Extract features from the connection
            features_host = extract_features_by_conn(file_path, gw=False)
            """
            tcp_handshake_features=get_tcp_handshakes(folder_name)
            if prefix=="relayed":
                tcp_handshake_features_cleaned=tcp_handshake_features[tcp_handshake_features['label']==1]
                tcp_handshake_features_cleaned=tcp_handshake_features_cleaned.drop(columns='label')
            elif prefix=="background":
                tcp_handshake_features_cleaned=tcp_handshake_features[tcp_handshake_features['label']==0]
                tcp_handshake_features_cleaned=tcp_handshake_features_cleaned.drop(columns='label')
            """
            # Check if features_host contains the 'conn' column
            if 'conn' in features_host.columns:
                rtt_features=get_rtt_feature(folder_name,prefix)
                print(rtt_features.shape)
                features_k_df = pd.DataFrame(list(feats.items()), columns=['conn', 'k_features'])
                features_k_expanded = features_k_df['k_features'].apply(pd.Series)
                features_k_expanded.columns = Features_names
                features_k_final = pd.concat([features_k_df['conn'], features_k_expanded], axis=1)
                #features_k_final['pcap_nb'] = i
                #features_list.append(features_k_final)
            
                # Check if 'conn' exists in both DataFrames before merging
                if 'conn' in features_k_final.columns:
                    # Merge the DataFrames on 'conn'
                    merged_df = pd.merge(features_host, features_k_final, on='conn', how='inner')
                    concatenated_features = pd.merge(merged_df, rtt_features, on='conn', how='inner')            
                    concatenated_features['pcap_nb'] = folder_name
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
            final_features.to_csv(f'/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/features_lim_{prefix}_{set_name}_rtt.csv', index=False)
        else:
            print("No valid features to save.")
def main():

    pkt_limit = 50
    main_directory = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/processed_new'
    folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]
    mixed_folder_paths = [path for path in folder_paths if "mixed" in path]
    random.seed(9)
    random.shuffle(mixed_folder_paths)
    
    # Split folder_paths into 60%, 20%, and 20% for training, testing, and validation
    num_folders = len(mixed_folder_paths)
    train_folders = mixed_folder_paths[:int(0.6 * num_folders)]
    print(len(train_folders))
    test_folders = mixed_folder_paths[int(0.6 * num_folders):int(0.8 * num_folders)]
    print(len(test_folders))
    val_folders = mixed_folder_paths[int(0.8 * num_folders):]
    print(len(val_folders))
    extract_feature_per_folder(train_folders, "train",pkt_limit)
    extract_feature_per_folder(test_folders, "test",pkt_limit)
    extract_feature_per_folder(val_folders, "val",pkt_limit)
        
if __name__ == "__main__":
    main()
    
