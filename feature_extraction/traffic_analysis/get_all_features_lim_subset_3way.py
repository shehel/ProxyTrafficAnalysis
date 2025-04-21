#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modified Feature Extractor for 3-way Classification
"""
from extract_features import get_features
from host_features_limited import extract_features_by_conn
from rtt_tls_feature import get_rtt_feature
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import pandas as pd
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings
import numpy as np
import json
import tqdm
import pdb
warnings.filterwarnings("ignore")


class FeatureExtractor:
    def __init__(self, json_path='background_distributions.json'):
        self.Features_names = [
            "max_in", "max_out", "max_total", "avg_in", "avg_out", "avg_total",
            "std_in", "std_out", "std_total", "75th_percentile_in", "75th_percentile_out", "75th_percentile_total",
            "25th_percentile_in_time", "50th_percentile_in_time", "75th_percentile_in_time", "100th_percentile_in_time",
            "25th_percentile_out_time", "50th_percentile_out_time", "75th_percentile_out_time", "100th_percentile_out_time",
            "25th_percentile_total_time", "50th_percentile_total_time", "75th_percentile_total_time", "100th_percentile_total_time",
            "nb_pkts_in", "nb_pkts_out", "nb_pkts_total",
            "nb_pkts_in_f30", "nb_pkts_out_f30", "nb_pkts_in_l30", "nb_pkts_out_l30",
            "std_pkt_conc_out20", "avg_pkt_conc_out20", "avg_per_sec", "std_per_sec", "avg_order_in",
            "avg_order_out", "std_order_in", "std_order_out", "medconc", "med_per_sec", "min_per_sec",
            "max_per_sec", "maxconc", "perc_in", "perc_out", "sum_altconc", "sum_alt_per_sec",
            "sum_number_pkts", "sum_intertimestats"
        ]
        self.Features_names.extend([f"altconc_{i+1}" for i in range(20)])
        self.Features_names.extend([f"alt_per_sec_{i+1}" for i in range(20)])
        self.Features_names.extend([f"conc_{i+1}" for i in range(60)])
        self.Features_names.extend(['rtt'])
        # Add new instance variables
        self.use_empirical_sampling = True
        self.empirical_packet_lengths = None
        self.background_length_distribution = None

        self.pkts_limit = 20
        self.comp_pkts_limit = 20
        
        # Load empirical samples
        self.load_empirical_samples(json_path)
    
    def load_empirical_samples(self, json_path='background_distributions.json'):
        """Load empirical packet length samples from JSON file"""
        try:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
                self.empirical_packet_lengths = json_data['length']['empirical_samples']
                self.background_length_distribution = json_data['length']
                self.background_timing_distribution = json_data['timing']
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load empirical samples: {e}")
            self.use_empirical_sampling = False

    def process_single_file(self, file_path: str, file_type: str, folder_name: str = None) -> pd.DataFrame:
        """Process a single CSV file and extract features"""
        try:
            features = {}
            df = pd.read_csv(file_path)
            if file_type == 'relayed':
                df['ts_relative'] = pd.to_numeric(df['ts_relative'], errors='coerce')
                df['pkt_len'] = pd.to_numeric(df['pkt_len'], errors='coerce')
                for conn_id, conn_data in df.groupby(["conn"]):
                    conn_data = conn_data.sort_values('ts_relative')
                    if len(conn_data) > 3 and conn_data.iloc[3]['pkt_len'] > 1300:
                        conn_data = conn_data.drop(conn_data.index[3]).reset_index(drop=True)
                        conn_data = conn_data.drop(conn_data.index[4]).reset_index(drop=True)
                        new_length = np.random.choice(self.empirical_packet_lengths)
                        conn_data.at[3, 'pkt_len'] = new_length
                                                
                    ########ATTACK#######
                    conn_data.reset_index(drop=True, inplace=True)
                    new_timing = np.random.lognormal(
                        mean=self.background_timing_distribution['mean'],
                        sigma=self.background_timing_distribution['std']
                    )
    
                    # Calculate current timing difference
                    old_timing = conn_data.loc[3]['ts_relative'] - conn_data.loc[2]['ts_relative']
    
                    # Calculate and apply timing adjustment
                    timing_adjustment = old_timing - new_timing
                    conn_data.loc[3:, 'ts_relative'] = conn_data.loc[3:, 'ts_relative'] - timing_adjustment
                    
                    #######################                
                    df.drop(df[df['conn'] == conn_id[0]].index, inplace=True)
                    df = pd.concat([df, conn_data], ignore_index=True)
                        

                print("df_shape",df.shape)
                all_pkts = [df.columns.tolist()] + df.astype(str).values.tolist()
                curr_conn = ''
                conn_pkts = []

                for idx, pkt in enumerate(all_pkts):
                    # If the first row is a header, skip it
                    if idx == 0:
                        continue
                    
                    conn_name = pkt[0]
                    # If we detect a new connection, process the old one first
                    if conn_name != curr_conn:
                        # If we had a previous connection with enough packets
                        if conn_pkts and len(conn_pkts) >= self.pkts_limit:
                            # Now compute features
                            conn_features = get_features(conn_pkts[:self.comp_pkts_limit], curr_conn, limit=0)
                            try:
                                rtt = calculate_rttv2(conn_pkts)
                                conn_features.append(rtt)
                            except ValueError as e:
                                print(f"Error in RTT calculation: {e}")
                                exit(1)

                            if conn_features:
                                features[curr_conn] = conn_features

                        # Start a new conn_pkts list for the new connection
                        conn_pkts = [pkt]
                        curr_conn = conn_name
                    else:
                        # Same connection, just append
                        conn_pkts.append(pkt)

                # Process final connection
                if conn_pkts and len(conn_pkts) >= self.pkts_limit:
                    # Get features and save them
                    conn_features = get_features(conn_pkts[:self.comp_pkts_limit], curr_conn, limit=0)
                    try:
                        rtt = calculate_rttv2(conn_pkts)
                        conn_features.append(rtt)
                    except ValueError as e:
                        print(f"Error in RTT calculation: {e}")
                        exit(1)

                    if conn_features:
                        features[curr_conn] = conn_features

            # Extract additional features
            if file_type == 'proxy':
                features_host = extract_features_by_conn(file_path, gw=True, max_pkts=self.pkts_limit, comp_pkts_limit=self.comp_pkts_limit)
            else:
                if file_type == 'relayed':
                    features_host = extract_features_by_conn(file_path, gw=False, max_pkts=self.pkts_limit, comp_pkts_limit=self.comp_pkts_limit, bias_fix=True,
                                                             attack=False, fix_dict={"empirical_packet_lengths": self.empirical_packet_lengths,
                                                                                    "timing_distribution": self.background_timing_distribution})
                else:
                    features_host = extract_features_by_conn(file_path, gw=False, max_pkts=self.pkts_limit, comp_pkts_limit=self.comp_pkts_limit)
                
            if 'conn' in features_host.columns:
                features_k_df = pd.DataFrame(list(features.items()), columns=['conn', 'k_features'])
                features_k_expanded = features_k_df['k_features'].apply(pd.Series)
                features_k_expanded.columns = self.Features_names
                features_k_final = pd.concat([features_k_df['conn'], features_k_expanded], axis=1)

                merged_df = pd.merge(features_host, features_k_final, on='conn', how='inner')
                
                # Assign class label based on file_type (0: background, 1: proxy, 2: relayed)
                if file_type == "background":
                    merged_df['label'] = 0
                elif file_type == "proxy":
                    merged_df['label'] = 1
                elif file_type == "relayed":
                    merged_df['label'] = 2
                
                # Add folder name as pcap_nb if provided
                if folder_name:
                    merged_df['pcap'] = folder_name
                
                # Keep only necessary columns for output
                output_columns = self.Features_names + ['label']
                if 'pcap' in merged_df.columns:
                    output_columns.append('pcap')
                    output_columns.append('conn')
                
                return merged_df

            return pd.DataFrame()  # Return empty DataFrame if no features were extracted

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error

    def save_batch(self, data_dfs, set_name, batch_num, output_dir):
        """Save a batch of data to CSV"""
        if not data_dfs:
            return
        
        batch_df = pd.concat(data_dfs, ignore_index=True)
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f'k_features_batch_{batch_num}.csv')
        batch_df.to_csv(output_file, index=False)
        print(f"Saved batch {batch_num} with {len(batch_df)} rows")

    def process_files_multithreaded(self, folders_path, output_dir):
        """Process files in batches to limit memory usage"""
        BATCH_SIZE = 10  # Number of folders to process in each batch
        batch_number = 0
        total_files = len(folders_path) * 3  # Each folder has 3 files
        total_batches = (len(folders_path) + BATCH_SIZE - 1) // BATCH_SIZE
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\nProcessing {total_files} files...")
        
        # Process folders in batches
        with tqdm.tqdm(total=total_batches, desc=f"Total batches") as batch_pbar:
            for batch_start in range(0, len(folders_path), BATCH_SIZE):
                batch_folders = folders_path[batch_start:batch_start + BATCH_SIZE]
                current_batch = []
                
                with ThreadPoolExecutor(max_workers=8) as executor:
                    futures = []
                    
                    # Submit jobs for all files in the current batch of folders
                    for folder in batch_folders:
                        folder_name = os.path.basename(folder)
                        
                        # Define paths for all three file types
                        proxy_path = os.path.join(folder, "proxy_conn.csv")
                        relayed_path = os.path.join(folder, "relayed_conn_labeled.csv")
                        background_path = os.path.join(folder, "background_conn_labeled.csv")
                        
                        # Submit proxy file processing
                        if os.path.exists(proxy_path):
                            proxy_future = executor.submit(
                                self.process_single_file, 
                                str(proxy_path), 
                                'proxy', 
                                folder_name
                            )
                            futures.append(proxy_future)
                        
                        # Submit relayed file processing
                        if os.path.exists(relayed_path):
                            relayed_future = executor.submit(
                                self.process_single_file, 
                                str(relayed_path), 
                                'relayed', 
                                folder_name
                            )
                            futures.append(relayed_future)
                            
                        # Submit background file processing
                        if os.path.exists(background_path):
                            background_future = executor.submit(
                                self.process_single_file, 
                                str(background_path), 
                                'background', 
                                folder_name
                            )
                            futures.append(background_future)
                
                    # Process results for current batch
                    with tqdm.tqdm(total=len(futures), 
                               desc=f"Batch {batch_number + 1}/{total_batches} files") as file_pbar:
                        for future in as_completed(futures):
                            features_df = future.result()
                            
                            if not features_df.empty:
                                current_batch.append(features_df)
                            
                            file_pbar.update(1)
                
                # Save current batch if not empty
                if current_batch:
                    self.save_batch(current_batch, "features", batch_number, output_dir)
                    batch_number += 1
                
                # Update batch progress
                batch_pbar.update(1)
                
                # Clear memory
                current_batch.clear()
                futures = []
                import gc
                gc.collect()

    def process_files_without_batching(self, folders_path, output_dir):
        """Process all files without batching to avoid potential issues"""
        all_features = []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\nProcessing files...")
        
        with tqdm.tqdm(total=len(folders_path), desc=f"Processing folders") as folder_pbar:
            for folder in folders_path:
                folder_name = os.path.basename(folder)
                
                # Define paths for all three file types
                proxy_path = os.path.join(folder, "proxy_conn.csv")
                relayed_path = os.path.join(folder, "relayed_conn_labeled.csv")
                background_path = os.path.join(folder, "background_conn_labeled.csv")
                
                print(folder_name)
                
                # Process proxy file
                if os.path.exists(proxy_path):
                    proxy_features = self.process_single_file(str(proxy_path), 'proxy', folder_name)
                    if not proxy_features.empty:
                        all_features.append(proxy_features)
                
                # Process relayed file
                if os.path.exists(relayed_path):
                    relayed_features = self.process_single_file(str(relayed_path), 'relayed', folder_name)
                    if not relayed_features.empty:
                        all_features.append(relayed_features)
                
                # Process background file
                if os.path.exists(background_path):
                    background_features = self.process_single_file(str(background_path), 'background', folder_name)
                    if not background_features.empty:
                        all_features.append(background_features)
                
                folder_pbar.update(1)
        
        # Save all features to a single file
        if all_features:
            all_features_df = pd.concat(all_features, ignore_index=True)
            output_file = os.path.join(output_dir, 'k_features.parquet')
            all_features_df.to_parquet(output_file, index=False)
            print(f"Saved all features with {len(all_features_df)} rows to {output_file}")
        else:
            print("No features were extracted.")


def calculate_rtt(conn_pkts: List[List[str]]) -> float:
    """
    Calculate Round Trip Time (RTT) from connection packets.
    
    Args:
        conn_pkts (List[List[str]]): List of connection packets where each packet is a list containing:
            - index 2: timestamp
            - index 3: destination IP
            - index 5: source IP 
            - index 7: packet length
    
    Returns:
        float: RTT value in seconds
        
    Raises:
        ValueError: If RTT calculation fails
    """
    try:
        tcp_syn = float(conn_pkts[0][2])
        large_pkt_count = 0
        
        # Find second received packet with >200 bytes
        for i in range(1, len(conn_pkts)):
            if int(conn_pkts[i][7]) > 200 and (conn_pkts[i][5] == conn_pkts[0][3]):
                large_pkt_count += 1
                if large_pkt_count == 2:
                    tls_serverhello = float(conn_pkts[i][2])
                    return tls_serverhello - tcp_syn
                    
        
    except Exception as e:
        raise ValueError(f"RTT calculation failed: {str(e)}")


def calculate_rttv2(conn_pkts: List[List[str]]) -> float:
    """
    Calculate Round Trip Time (RTT) using TCP and TLS timing differences.
    
    Args:
        conn_pkts (List[List[str]]): List of connection packets where each packet is a list containing:
            - index 2: timestamp
            - index 3: destination IP
            - index 5: source IP 
            - index 7: packet length
    
    Returns:
        float: Difference between RTT TLS and RTT TCP in seconds
        
    Raises:
        ValueError: If RTT calculation fails
    """
    try:
        # Get source IP from first packet
        source_ip = conn_pkts[0][5]
        
        # Create lists for outgoing packets (source IP matches first packet's source IP)
        outgoing_packets = []
        for pkt in conn_pkts:
            if pkt[5] == source_ip:
                outgoing_packets.append({
                    'ts_relative': float(pkt[2]),
                    'pkt_len': int(pkt[7])
                })
        
        # Calculate RTT TCP (time between first two outgoing packets)
        rtt_tcp = None
        if len(outgoing_packets) >= 2:
            rtt_tcp = outgoing_packets[1]['ts_relative'] - outgoing_packets[0]['ts_relative']
        
        # Calculate RTT TLS (time between consecutive outgoing packets with pkt_len > 65)
        rtt_tls = None
        large_outgoing_packets = [pkt for pkt in outgoing_packets if pkt['pkt_len'] > 65]
        
        if len(large_outgoing_packets) >= 2:
            rtt_tls = large_outgoing_packets[1]['ts_relative'] - large_outgoing_packets[0]['ts_relative']
        
        if rtt_tcp is None or rtt_tls is None:
            return None
            
        return rtt_tls - rtt_tcp
        
    except Exception as e:
        raise ValueError(f"RTT calculation failed: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='Extract traffic analysis features for 3-way classification')
    parser.add_argument('--folder_path', type=str, required=True,
                      help='Path to the folder containing PCAP files')
    parser.add_argument('--pkt_limit', type=int, default=20,
                      help='Packet limit for analysis (default: 20)')
    parser.add_argument('--output_dir', type=str, required=True,
                      help='Directory where results will be saved')
    parser.add_argument('--json_path', type=str, default='feature_extraction/background_distributions.json',
                      help='Path to background distributions JSON file')
    parser.add_argument('--no_batching', action='store_true',
                      help='Process all files without batching')
    
    args = parser.parse_args()
    
    # Initialize feature extractor
    extractor = FeatureExtractor(args.json_path)
    
    # Get all subfolders in the input folder
    folders = [os.path.join(args.folder_path, folder) 
              for folder in os.listdir(args.folder_path) 
              if os.path.isdir(os.path.join(args.folder_path, folder))]
    
    # Process the input folder
    print(f"Processing folder: {args.folder_path}")
    if args.no_batching:
        extractor.process_files_without_batching(folders, args.output_dir)
    else:
        extractor.process_files_multithreaded(folders, args.output_dir)

if __name__ == "__main__":
    main()

