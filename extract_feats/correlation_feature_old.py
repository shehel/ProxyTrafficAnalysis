import pandas as pd
import numpy as np
from scipy.stats import zscore
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import cudf
import cupy as cp
from cuml.preprocessing import StandardScaler

def get_metrics(data):
    if data.size == 0:
        return [0] * 9
    elif data.size == 1:
        value = data[0]
        return [1, value, value, value, value, value, 0, 0, 0]
    else:
        count = data.size
        total_sum = np.sum(data)
        mean = np.mean(data)
        median = np.median(data)
        minimum = np.min(data)
        maximum = np.max(data)
        data_range = maximum - minimum
        variance = np.var(data, ddof=1)
        std_dev = np.std(data, ddof=1)
        return [count, total_sum, mean, median, minimum, maximum, data_range, variance, std_dev]

def get_correlation_array(gateway_df, df, bin_size_seconds=0.1):
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

        for col in ['ts_relative', 'pkt_len']:
            gateway_conn_df[col] = pd.to_numeric(gateway_conn_df[col], errors='coerce')
            conn_df[col] = pd.to_numeric(conn_df[col], errors='coerce')

        gateway_conn_df.dropna(subset=['ts_relative', 'pkt_len'], inplace=True)
        conn_df.dropna(subset=['ts_relative', 'pkt_len'], inplace=True)

        gateway_conn_df.sort_values('ts_relative', inplace=True)
        conn_df.sort_values('ts_relative', inplace=True)

        gateway_conn_df['time_bin'] = (gateway_conn_df['ts_relative'] // bin_size_seconds) * bin_size_seconds
        conn_df['time_bin'] = (conn_df['ts_relative'] // bin_size_seconds) * bin_size_seconds

        gateway_sums = gateway_conn_df.groupby('time_bin')['pkt_len'].sum()
        relay_sums = conn_df.groupby('time_bin')['pkt_len'].sum()

        all_bins = pd.Index(sorted(set(gateway_sums.index).union(set(relay_sums.index))))
        gateway_sums = gateway_sums.reindex(all_bins, fill_value=0)
        relay_sums = relay_sums.reindex(all_bins, fill_value=0)

        gateway_normalized = np.nan_to_num(zscore(gateway_sums))
        relay_normalized = np.nan_to_num(zscore(relay_sums))

        corr_array = np.multiply(relay_normalized, gateway_normalized)
        metrics = get_metrics(corr_array)
        z_scores.append((conn, *metrics))

    return pd.DataFrame(z_scores, columns=['conn', 'corr_count', 'corr_sum', 'corr_mean', 'corr_median', 'corr_minimum', 'corr_maximum', 'corr_range', 'corr_variance', 'corr_std_dev'])


def process_connection(folder_name, prefix, pkt_limit):
    all_data = []
    gateway_file_path = os.path.join(folder_name, "proxy_conn.csv")
    file_path = os.path.join(folder_name, f'{prefix}_conn_labeled.csv')

    if not os.path.exists(file_path) or not os.path.exists(gateway_file_path):
        return all_data

    df = pd.read_csv(file_path)
    gateway_df = pd.read_csv(gateway_file_path)
    correlation_df = get_correlation_array(gateway_df, df)
    correlation_df['pcap_nb'] = folder_name
    all_data.extend(correlation_df.to_dict('records'))

    return all_data

def get_correlation_array_multithread(folder_paths, set_name, pkt_limit):
    prefixes = ["relayed"]
    for prefix in tqdm(prefixes, desc="Processing prefixes"):
        all_data = []
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_connection, path, prefix, pkt_limit): path for path in folder_paths}
            for future in tqdm(as_completed(futures),
                               total=len(futures),
                               desc=f"Processing {prefix} connections"):
                result = future.result()
                all_data.extend(result)
                
        all_data_df = pd.DataFrame(all_data)
        all_data_df.to_csv(f'content/subset_features_03_18/{set_name}/corr_feature_old_50.csv', index=False)
    return all_data_df

def main():
    pkt_limit = 50
    train_path = "data/subset_03_18/train"
    test_path = "data/subset_03_18/test"
    val_path = "data/subset_03_18/val"
    
    train_folders = [os.path.join(train_path, folder) 
                    for folder in os.listdir(train_path) 
                    if os.path.isdir(os.path.join(train_path, folder))]
    
    test_folders = [os.path.join(test_path, folder) 
                    for folder in os.listdir(test_path) 
                    if os.path.isdir(os.path.join(test_path, folder))][:3]
    print(test_folders)
    
    val_folders = [os.path.join(val_path, folder) 
                    for folder in os.listdir(val_path) 
                    if os.path.isdir(os.path.join(val_path, folder))]
    

    test_df = get_correlation_array_multithread(test_folders, "test", pkt_limit)
    # val_df = get_correlation_array_multithread(val_folders, "val", pkt_limit)
    # train_df = get_correlation_array_multithread(train_folders, "train", pkt_limit)

    # all_data_df = pd.concat([train_df, test_df, val_df], ignore_index=True)
    # print(all_data_df)

if __name__ == "__main__":
    main()


