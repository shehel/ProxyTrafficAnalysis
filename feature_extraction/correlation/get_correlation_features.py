import argparse
import pandas as pd
import numpy as np
from scipy.stats import zscore
import os
import random
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json
import cudf
import cupy as cp
from cuml.preprocessing import StandardScaler
import pdb
import multiprocessing as mp

EMPIRICAL_PACKET_LENS = None
BG_LEN_MEAN = None
BG_LEN_STD = None
BG_TG_MEAN = None
BG_TG_STD = None



def get_metrics(array_cp):
    """
    Example metric calculations, all on GPU.
    Replace with your own metric logic.
    """
    corr_count = int(array_cp.size)
    corr_sum = float(cp.sum(array_cp))
    corr_mean = float(cp.mean(array_cp))
    corr_median = float(cp.median(array_cp))
    corr_minimum = float(cp.min(array_cp))
    corr_maximum = float(cp.max(array_cp))
    corr_range = corr_maximum - corr_minimum
    corr_variance = float(cp.var(array_cp))
    corr_std_dev = float(cp.std(array_cp))
    return (
        corr_count, corr_sum, corr_mean, corr_median,
        corr_minimum, corr_maximum, corr_range,
        corr_variance, corr_std_dev
    )
    
def get_zero_metrics():
    
    return (0, 0, 0, 0,
            0, 0, 0,
            0, 0)


def get_correlation_array(gateway_df, df, pkt_limit, bin_size_seconds=0.1, bound_range=1.0):
    """
    GPU-accelerated approach using cuDF & CuPy.
    Considers all connections with >20 packets but analyzes only first 20 packets.
    """

    # 1) Convert to cuDF if needed
    if not isinstance(gateway_df, cudf.DataFrame):
        gateway_gdf = cudf.DataFrame.from_pandas(gateway_df)
    else:
        gateway_gdf = gateway_df

    if not isinstance(df, cudf.DataFrame):
        df_gdf = cudf.DataFrame.from_pandas(df)
    else:
        df_gdf = df

    # 2) Ensure numeric columns & drop NA
    gateway_gdf['ts_relative'] = gateway_gdf['ts_relative'].astype(float)
    gateway_gdf['pkt_len'] = gateway_gdf['pkt_len'].astype(float)
    gateway_gdf = gateway_gdf.dropna(subset=['ts_relative', 'pkt_len'])

    df_gdf['ts_relative'] = df_gdf['ts_relative'].astype(float)
    df_gdf['pkt_len'] = df_gdf['pkt_len'].astype(float)
    df_gdf = df_gdf.dropna(subset=['ts_relative', 'pkt_len'])

    # 3) Sort and identify valid connections
    gateway_gdf = gateway_gdf.sort_values('ts_relative')
    df_gdf = df_gdf.sort_values(['conn', 'ts_relative'])
    
    # First identify connections that have more than 20 packets
    group_sizes = df_gdf.groupby('conn').size().reset_index(name='group_count')
    valid_conns = group_sizes[group_sizes['group_count'] >= 20]['conn']
    
    # Filter to keep only valid connections
    df_gdf = df_gdf.merge(valid_conns.to_frame('conn'), on='conn')
    
    # Now for each valid connection, keep only first 20 packets for correlation
    df_gdf = df_gdf.groupby('conn').apply(lambda x: x.head(pkt_limit)).reset_index(drop=True)

    # 4) Bin entire data once
    bin_factor = 1.0 / bin_size_seconds
    gateway_gdf['time_bin'] = cp.floor(gateway_gdf['ts_relative'] * bin_factor) / bin_factor
    df_gdf['time_bin'] = cp.floor(df_gdf['ts_relative'] * bin_factor) / bin_factor

    # 5) Summation grouped by bin
    gateway_binned = gateway_gdf.groupby('time_bin')['pkt_len'].sum().reset_index()
    gateway_binned = gateway_binned.sort_values('time_bin')  # ensure ascending

    # Summation grouped by (conn, time_bin)
    df_binned = df_gdf.groupby(['conn', 'time_bin'])['pkt_len'].sum().reset_index()

    # 6) Prepare search-slice for gateway bins
    gateway_time_bins = gateway_binned['time_bin'].values  # GPU array

    # 7) Find min/max for each conn (returns a DataFrame with columns like "ts_relative_min", "ts_relative_max")
    minmax_df = df_gdf.groupby('conn')['ts_relative'].agg(['min', 'max']).reset_index()

    # 8) Build a dictionary on CPU
    # Convert the group result to Pandas or host arrays
    # If minmax_df is not huge, converting to_pandas() is fine:
    mm_pdf = minmax_df.to_pandas()  # small DataFrame
    minmax_map = {}
    for idx, row in mm_pdf.iterrows():
        conn_key = row['conn']
        tmin = row['min']
        tmax = row['max']
        minmax_map[conn_key] = (tmin, tmax)

    # 9) Unique connections
    unique_conns = df_gdf['conn'].unique()

    # 10) Process each connection in a Python loop
    results = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(process_single_connection, 
                                   (conn_val, gateway_binned, df_binned, gateway_time_bins, minmax_map)): 
                                       conn_val for conn_val in unique_conns.to_pandas()}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    # Convert final results to Pandas
    columns = [
        'conn', 'corr_count', 'corr_sum', 'corr_mean', 'corr_median',
        'corr_minimum', 'corr_maximum', 'corr_range', 'corr_variance', 'corr_std_dev'
    ]
    
    result_df = pd.DataFrame(results, columns=columns)
    return result_df

def process_single_connection(args):
    """
    Process a single connection for correlation analysis
    """
    conn_val, gateway_binned, df_binned, gateway_time_bins, minmax_map = args
    
    # Retrieve min_time, max_time
    times = minmax_map.get(conn_val)
    if not times:
        return None
    tmin, tmax = times
    if cp.isnan(tmin) or cp.isnan(tmax):
        return None

    start_time = tmin
    end_time = tmax + 1.0  # bound_range hardcoded to 1.0

    # Subset df_binned for this connection
    sub_mask = (df_binned['conn'] == conn_val)
    conn_binned = df_binned[sub_mask]
    if conn_binned.empty:
        return None

    # Slice gateway bins using searchsorted
    # Make them 1D CuPy arrays, same dtype as gateway_time_bins
    start_time_cp = cp.asarray([start_time], dtype=gateway_time_bins.dtype)
    end_time_cp = cp.asarray([end_time], dtype=gateway_time_bins.dtype)

    left_idx_arr = cp.searchsorted(gateway_time_bins, start_time_cp, side='left')
    right_idx_arr = cp.searchsorted(gateway_time_bins, end_time_cp, side='right')

    # left_idx_arr and right_idx_arr are 1D Cupy arrays. Extract the int index:
    left_idx = int(left_idx_arr[0].item())
    right_idx = int(right_idx_arr[0].item())

    gateway_sub = gateway_binned.iloc[left_idx:right_idx]
    if gateway_sub.empty:
        return get_zero_metrics()

    # Rename columns for clarity
    gateway_sub = gateway_sub.rename(columns={'pkt_len': 'gw_len'})
    conn_binned = conn_binned.rename(columns={'pkt_len': 'rl_len'})

    # Merge on time_bin
    merged = gateway_sub.merge(conn_binned, on='time_bin', how='outer').fillna({'gw_len':0, 'rl_len':0})

    # Convert to CuPy arrays
    gw_vals = merged['gw_len'].values
    rl_vals = merged['rl_len'].values

    # Compute z-scores on GPU
    gw_mean, gw_std = cp.mean(gw_vals), cp.std(gw_vals) + 1e-9
    rl_mean, rl_std = cp.mean(rl_vals), cp.std(rl_vals) + 1e-9

    gw_z = (gw_vals - gw_mean) / gw_std
    rl_z = (rl_vals - rl_mean) / rl_std

    # Element-wise correlation array
    corr_array = gw_z * rl_z

    # Get metrics
    metrics = get_metrics(corr_array)
    return (conn_val, *metrics)


def load_empirical_samples(json_path='packet_lengths.json'):
        """Load empirical packet length samples from JSON file"""
        global EMPIRICAL_PACKET_LENS, BG_LEN_MEAN, BG_LEN_STD, BG_TG_MEAN, BG_TG_STD
        try:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
                EMPIRICAL_PACKET_LENS = json_data['length']['empirical_samples']
                BG_LEN_MEAN = json_data['length']['mean']
                BG_LEN_STD = json_data['length']['std']
                BG_TG_MEAN = json_data['timing']['mean']
                BG_TG_STD = json_data['timing']['std']
                return EMPIRICAL_PACKET_LENS, BG_LEN_MEAN, BG_LEN_STD
                
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load empirical samples: {e}")
            return None, None, None

def apply_bias_removal(group, use_empirical_sampling=True):
    """
    Handles the bias removal steps:
    1) If the group has at least `pkt_limit` packets and 4th packet has pkt_len > 1300,
       drop the 4th and 6th packets.
    2) If a 4th packet still exists afterward, resample its pkt_len.
    """
    if len(group) > 3 and group.iloc[3]['pkt_len'] > 1300:
        group.drop(index=group.index[3], inplace=True)
        if len(group) > 4:
            group.drop(index=group.index[4], inplace=True)

    if len(group) > 3:
        if use_empirical_sampling and (EMPIRICAL_PACKET_LENS is not None):
            new_length = np.random.choice(EMPIRICAL_PACKET_LENS)
        else:
            if BG_LEN_MEAN is None or BG_LEN_STD is None:
                raise ValueError("Background distribution parameters are required when empirical sampling is disabled")
            mean_ = BG_LEN_MEAN
            std_ = BG_LEN_STD
            new_length = np.random.normal(loc=mean_, scale=std_)
            new_length = max(1, int(round(new_length)))

        group.at[group.index[3], 'pkt_len'] = new_length

    return group

def apply_attack(group):
    """
    Applies timing attack modification to the group
    """
    if len(group) > 3:
        new_timing = np.random.lognormal(
            mean=BG_TG_MEAN,
            sigma=BG_TG_STD
        )
        
        old_timing = group.iloc[3]['ts_relative'] - group.iloc[2]['ts_relative']
        timing_adjustment = old_timing - new_timing
        fourth_packet_idx = group.index[3]
        
        mask = group.index >= fourth_packet_idx
        group.loc[mask, 'ts_relative'] = group.loc[mask, 'ts_relative'] - timing_adjustment

    return group

def apply_changes(df, pkt_limit):
    """
    Main function that applies both bias removal and timing attack modifications
    """
    updated_groups = []

    if df.empty:
        return df

    for conn_name, group in df.groupby('conn', sort=False):
        if len(group) >= 20:
            group = group.sort_values(by='ts_relative', ascending=True).copy()
            
            # Apply bias removal
            group = apply_bias_removal(group, True)
            
            # Apply timing attack
            # group = apply_attack(group)
            
            updated_groups.append(group)
        else:
            updated_groups.append(group)

    if not updated_groups:
        raise ValueError(f"No valid groups found with minimum packet limit of {pkt_limit}")

    if len(updated_groups) == 0:
        print("No changes applied, as no groups found")
        return df
    
    out_df = pd.concat(updated_groups).sort_index()
    return out_df

def init_worker(config_data):
    global EMPIRICAL_PACKET_LENS, BG_LEN_MEAN, BG_LEN_STD, BG_TG_MEAN, BG_TG_STD
    (EMPIRICAL_PACKET_LENS, BG_LEN_MEAN, BG_LEN_STD, BG_TG_MEAN, BG_TG_STD) = config_data

def process_connection(folder_name, prefix, pkt_limit):
    all_data = []
    gateway_file_path = os.path.join(folder_name, "proxy_conn.csv")
    file_path = os.path.join(folder_name, f'{prefix}_conn_labeled.csv')

    if not os.path.exists(file_path) or not os.path.exists(gateway_file_path):
        return all_data

    df = pd.read_csv(file_path)
    unbiased_df = apply_changes(df, pkt_limit)
    gateway_df = pd.read_csv(gateway_file_path)
    correlation_df = get_correlation_array(gateway_df, unbiased_df, pkt_limit)
    correlation_df['pcap_nb'] = folder_name
    all_data.extend(correlation_df.to_dict('records'))

    return all_data

def save_batch(data_dfs, prefix, batch_num, output_dir):
    """Save a batch of data to CSV"""
    if not data_dfs:
        return
    
    batch_df = pd.concat(data_dfs)
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f'{prefix}_corr_batch_{batch_num}.csv')
    batch_df.to_csv(output_file, index=False)
    print(f"Saved {prefix} batch {batch_num} with {len(batch_df)} rows")

def process_batch(folder_paths, prefix, pkt_limit):
    """Process a batch of folders and return their combined results"""
    batch_results = []
    
    num_workers = min(20, os.cpu_count() if os.cpu_count() else 4) 
    print(f"Number of workers: {num_workers}")
    
    # Pass the global variables to be initialized in new process
    config = (EMPIRICAL_PACKET_LENS, BG_LEN_MEAN, BG_LEN_STD, BG_TG_MEAN, BG_TG_STD)
    with ProcessPoolExecutor(initializer=init_worker, initargs=(config, ), max_workers=num_workers) as executor:
        futures = {executor.submit(process_connection, path, prefix, pkt_limit): path 
                  for path in folder_paths}
        
        for future in tqdm(as_completed(futures), desc=f"Processing {len(futures)} PCAPs", total=len(futures)):
            result = future.result()
            if result:
                df = pd.DataFrame(result)
                df['label'] = 1 if prefix == "relayed" else 0
                batch_results.append(df)
    
    exit(0)
    return batch_results

def get_correlation_array_multithread(folder_paths, output_dir, pkt_limit):
    prefixes = ["relayed", "background"]
    BATCH_SIZE = 20  # Number of folders to process before saving
    
    for prefix in prefixes:
        batch_number = 0
        total_batches = (len(folder_paths) + BATCH_SIZE - 1) // BATCH_SIZE  # ceil division
        
        print(f"\nProcessing {prefix} data:")
        with tqdm(total=total_batches, desc=f"{prefix} batches") as batch_pbar:
            for i in range(0, len(folder_paths), BATCH_SIZE):
                batch_folders = folder_paths[i:i + BATCH_SIZE]
                
                batch_results = process_batch(batch_folders, prefix, pkt_limit)
                
                if batch_results:
                    save_batch(batch_results, prefix, batch_number, output_dir)
                    batch_number += 1
                
                del batch_results
                batch_pbar.update(1)

def main():
    try:
        mp.set_start_method('spawn', force=True)
        print("Set multiprocessing method to spawn")
    except:
        print("Multiprocessing method already set or could not be forced")
        pass

    parser = argparse.ArgumentParser(description='Process PCAP files for correlation analysis')
    parser.add_argument('--folder_path', type=str, required=True,
                      help='Path to the folder containing PCAP files')
    parser.add_argument('--pkt_limit', type=int, default=50,
                      help='Packet limit for analysis (default: 50)')
    parser.add_argument('--output_dir', type=str, required=True,
                      help='Directory where results will be saved')
    
    args = parser.parse_args()
    
    # Get all subfolders in the input folder
    folders = [os.path.join(args.folder_path, folder) 
              for folder in os.listdir(args.folder_path) 
              if os.path.isdir(os.path.join(args.folder_path, folder))]
    
    # Get distribution info from json file
    load_empirical_samples('background_distributions.json')
    
    print(f"Processing folder: {args.folder_path}")
    get_correlation_array_multithread(folders, args.output_dir, args.pkt_limit)

if __name__ == "__main__":
    main()


