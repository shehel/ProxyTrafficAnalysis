#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 10:47:59 2025

@author: mounarabhi
"""
import pandas as pd
import numpy as np
from scipy.signal import correlate
from scipy.stats import zscore
import os
import random
from concurrent.futures import ThreadPoolExecutor

def process_connection(folder_name, prefix, pkt_limit):
    all_data = []
    gateway_file_path = folder_name + "/proxy_conn.csv"
    if prefix == "relayed":
        file_path = folder_name + '/relayed_conn_labeled.csv'
    elif prefix == "background":
        file_path = folder_name + '/background_conn_labeled.csv'

    if not os.path.exists(file_path) or not os.path.exists(gateway_file_path):
        return all_data  # Skip if files are missing

    df = pd.read_csv(file_path)
    gateway_df = pd.read_csv(gateway_file_path)
    df = df[df['dst_ip'] == '10.0.2.16']
    gateway_df = gateway_df[gateway_df['src_ip'] == '10.0.2.16']
    connections = df['conn'].unique()
    z_scores = []

    for conn in connections:
        conn_df = df[df['conn'] == conn].copy()
        BOUND_RANGE = 1
        conn_ts_start = conn_df['ts_relative'].min()
        conn_ts_end = conn_df['ts_relative'].max() + BOUND_RANGE

        gateway_conn_df = gateway_df[
            (gateway_df['ts_relative'] >= conn_ts_start) & (gateway_df['ts_relative'] <= conn_ts_end)
        ].copy()

        gateway_conn_df['ts_relative'] = pd.to_numeric(gateway_conn_df['ts_relative'], errors='coerce')
        gateway_conn_df['pkt_len'] = pd.to_numeric(gateway_conn_df['pkt_len'], errors='coerce')

        conn_df['ts_relative'] = pd.to_numeric(conn_df['ts_relative'], errors='coerce')
        conn_df['pkt_len'] = pd.to_numeric(conn_df['pkt_len'], errors='coerce')

        gateway_conn_df.dropna(subset=['ts_relative', 'pkt_len'], inplace=True)
        conn_df.dropna(subset=['ts_relative', 'pkt_len'], inplace=True)

        gateway_conn_df.sort_values('ts_relative', inplace=True)
        conn_df.sort_values('ts_relative', inplace=True)

        gateway_conn_df.reset_index(drop=True, inplace=True)
        conn_df.reset_index(drop=True, inplace=True)

        bin_size_seconds = 1
        gateway_conn_df['time_bin'] = (gateway_conn_df['ts_relative'] // bin_size_seconds) * bin_size_seconds
        conn_df['time_bin'] = (conn_df['ts_relative'] // bin_size_seconds) * bin_size_seconds

        gateway_sums = gateway_conn_df.groupby('time_bin')['pkt_len'].sum()
        relay_sums = conn_df.groupby('time_bin')['pkt_len'].sum()

        all_bins = pd.Index(sorted(set(gateway_sums.index).union(set(relay_sums.index))))
        gateway_sums = gateway_sums.reindex(all_bins, fill_value=0)
        relay_sums = relay_sums.reindex(all_bins, fill_value=0)

        gateway_normalized = zscore(gateway_sums)
        relay_normalized = zscore(relay_sums)

        gateway_normalized = np.nan_to_num(gateway_normalized)
        relay_normalized = np.nan_to_num(relay_normalized)

        xcorr = correlate(relay_normalized, gateway_normalized, mode='full')
        lags = np.arange(-len(gateway_normalized) + 1, len(gateway_normalized))
        xcorr_normalized = xcorr / len(gateway_normalized)

        max_corr_index = np.argmax(xcorr_normalized)
        max_corr_value = xcorr_normalized[max_corr_index]

        z_scores.append((conn, max_corr_value))

    # Append data to the all_data list
    for conn, max_corr in z_scores:
        all_data.append({'conn': conn, 'max_corr': max_corr, 'pcap_nb': folder_name})
    return all_data

def get_correlation_array_multithread(folder_paths, set_name, pkt_limit):
    prefixes = ["background","relayed"]
    for prefix in prefixes:
        all_data = []
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_connection, folder_name, prefix, pkt_limit) for folder_name in folder_paths]
            for future in futures:
                all_data.extend(future.result())
        all_data_df = pd.DataFrame(all_data)
        all_data_df.to_csv(f'/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/feature_corr__{prefix}_{set_name}.csv', index=False)
    return all_data_df

def main():
    pkt_limit = 50
    main_directory = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/processed_new'
    folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]
    mixed_folder_paths = [path for path in folder_paths if "mixed" in path]
    random.seed(9)
    random.shuffle(mixed_folder_paths)

    num_folders = len(mixed_folder_paths)
    train_folders = mixed_folder_paths[:int(0.6 * num_folders)]
    test_folders = mixed_folder_paths[int(0.6 * num_folders):int(0.8 * num_folders)]
    val_folders = mixed_folder_paths[int(0.8 * num_folders):]

    test_df = get_correlation_array_multithread(test_folders, "test", pkt_limit)
    val_df = get_correlation_array_multithread(val_folders, "val", pkt_limit)
    train_df = get_correlation_array_multithread(train_folders, "train", pkt_limit)

    # Combine all data into one DataFrame if needed
    all_data_df = pd.concat([train_df, test_df, val_df], ignore_index=True)
    print(all_data_df)

if __name__ == "__main__":
    main()
