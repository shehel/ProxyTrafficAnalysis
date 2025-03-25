import pandas as pd
import numpy as np
from scipy.stats import zscore
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json
import cudf
import cupy as cp
from cuml.preprocessing import StandardScaler
import pdb

# Add GPU management imports
from contextlib import contextmanager
import threading

# Global variables
EMPIRICAL_PACKET_LENS = None
BG_DST_MEAN = None
BG_DST_STD = None
_gpu_locks = {}
_local = threading.local()

def init_gpu_locks():
    """Initialize locks for each available GPU"""
    global _gpu_locks
    n_gpus = cp.cuda.runtime.getDeviceCount()
    _gpu_locks = {i: threading.Lock() for i in range(n_gpus)}
    return n_gpus

@contextmanager
def gpu_context(gpu_id=None):
    """Context manager for GPU selection"""
    if gpu_id is None:
        # Round-robin GPU selection
        n_gpus = len(_gpu_locks)
        if not hasattr(_local, 'last_gpu'):
            _local.last_gpu = 0
        gpu_id = _local.last_gpu
        _local.last_gpu = (_local.last_gpu + 1) % n_gpus

    with _gpu_locks[gpu_id]:
        cp.cuda.Device(gpu_id).use()
        yield

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


def get_correlation_array(gateway_df, df, pkt_limit, gpu_id=None, bin_size_seconds=0.1, bound_range=1.0):
    """
    GPU-accelerated approach using cuDF & CuPy.
    - Sorts and bins data once.
    - Uses searchsorted for gateway slices.
    - Avoids .itertuples() or .iterrows() on cuDF.

    If you have large data, consider Dask-cuDF for multi-GPU or out-of-core.
    """
    with gpu_context(gpu_id):
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

        # 3) Sort once
        gateway_gdf = gateway_gdf.sort_values('ts_relative')
        df_gdf = df_gdf.sort_values(['conn', 'ts_relative'])
        
        # Compute group sizes for each 'conn'
        group_sizes = df_gdf.groupby('conn').size().reset_index(name='group_count')
        df_gdf = df_gdf.merge(group_sizes, on='conn')
        df_gdf = df_gdf[df_gdf['group_count'] >= 20].copy()
        df_gdf.drop(columns=['group_count'], inplace=True)

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
        for conn_val in unique_conns.to_pandas():
            # Retrieve min_time, max_time
            times = minmax_map.get(conn_val)
            if not times:
                continue
            tmin, tmax = times
            if cp.isnan(tmin) or cp.isnan(tmax):
                continue

            start_time = tmin
            end_time = tmax + bound_range

            # Subset df_binned for this connection
            sub_mask = (df_binned['conn'] == conn_val)
            conn_binned = df_binned[sub_mask]
            if conn_binned.empty:
                continue

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
                continue

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
            results.append((conn_val, *metrics))

        # Convert final results to Pandas
        columns = [
            'conn', 'corr_count', 'corr_sum', 'corr_mean', 'corr_median',
            'corr_minimum', 'corr_maximum', 'corr_range', 'corr_variance', 'corr_std_dev'
        ]
        result_df = pd.DataFrame(results, columns=columns)
        return result_df


def load_empirical_samples(json_path='packet_lengths.json'):
        """Load empirical packet length samples from JSON file"""
        global EMPIRICAL_PACKET_LENS, BG_DST_MEAN, BG_DST_STD
        try:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
                EMPIRICAL_PACKET_LENS = json_data['length']['empirical_samples']
                BG_DST_MEAN = json_data['length']['mean']
                BG_DST_STD = json_data['length']['std']
                return EMPIRICAL_PACKET_LENS, BG_DST_MEAN, BG_DST_STD
                
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load empirical samples: {e}")
            return None, None, None

def apply_bias_removal(df, 
                       pkt_limit,
                       use_empirical_sampling=False,
                       empirical_packet_lengths=None,
                       background_dst_mean=None,
                       background_dst_std=None):
    """
    Modifies 'df' in-place so that for each connection (conn):
      1) If the group has at least pkt_limit packets,
         then if the 4th packet has pkt_len > 1300,
         drop the 4th and 6th packets.
      2) If a 4th packet still exists afterward,
         resample its pkt_len (empirical or normal distribution).

    Returns a new DataFrame with the modifications.
    """
    # We'll collect the updated sub-DataFrames and concatenate at the end
    updated_groups = []

    if df.empty:
        return df

    # Group by connection
    for conn_name, group in df.groupby('conn', sort=False):
        # Only proceed if we have enough packets
        if len(group) >= pkt_limit:
            # Sort by time if needed to ensure chronological order
            group = group.sort_values(by='ts_relative', ascending=True).copy()

            # (1) If the 4th packet's length > 1300, drop 4th and "6th" (which becomes index 4 after the 4th is dropped)
            if len(group) > 3 and group.iloc[3]['pkt_len'] > 1300:
                group.drop(index=group.index[3], inplace=True)
                if len(group) > 4:
                    group.drop(index=group.index[4], inplace=True)

            # (2) Resample the (new) 4th packet's length if it exists
            if len(group) > 3:
                if use_empirical_sampling and (empirical_packet_lengths is not None):
                    new_length = np.random.choice(empirical_packet_lengths)
                else:
                    # Fallback: sample from a normal distribution
                    if background_dst_mean is None or background_dst_std is None:
                        raise ValueError("Background distribution parameters are required when empirical sampling is disabled")
                    mean_ = background_dst_mean
                    std_ = background_dst_std
                    new_length = np.random.normal(loc=mean_, scale=std_)
                    new_length = max(1, int(round(new_length)))

                # Update the 4th packet's length
                group.at[group.index[3], 'pkt_len'] = new_length

            updated_groups.append(group)
        else:
            # If not enough packets, just keep the group as-is
            updated_groups.append(group)

    if not updated_groups:
        raise ValueError(f"No valid groups found with minimum packet limit of {pkt_limit}")

    # Combine all sub-DataFrames back
    if len(updated_groups) == 0:
        print("No bias removed, as no groups found")
        return df
    
    out_df = pd.concat(updated_groups).sort_index()
    return out_df


class GPUBatchProcessor:
    def __init__(self, gpu_id, batch_size=1000):
        self.gpu_id = gpu_id
        self.batch_size = batch_size
        with gpu_context(gpu_id):
            # Pre-allocate memory for common operations
            self.scaler = StandardScaler()
            # Initialize other GPU resources as needed

    def process_connection_batch(self, connections_data):
        """Process multiple connections in a single GPU batch"""
        with gpu_context(self.gpu_id):
            results = []
            
            # Convert all data to GPU at once
            gateway_gdf = cudf.DataFrame.from_pandas(connections_data['gateway'])
            conn_gdf = cudf.DataFrame.from_pandas(connections_data['connections'])

            # Pre-sort all data
            gateway_gdf = gateway_gdf.sort_values('ts_relative')
            conn_gdf = conn_gdf.sort_values(['conn', 'ts_relative'])

            # Process in chunks to maximize GPU utilization
            unique_conns = conn_gdf['conn'].unique().values_host
            for chunk_start in range(0, len(unique_conns), self.batch_size):
                chunk_conns = unique_conns[chunk_start:chunk_start + self.batch_size]
                
                # Filter connections for this chunk
                chunk_mask = conn_gdf['conn'].isin(chunk_conns)
                chunk_data = conn_gdf[chunk_mask]

                # Bin data for all connections in chunk at once
                binned_data = self._bin_data(chunk_data, gateway_gdf)
                
                # Process correlations in parallel
                chunk_results = self._process_correlations(binned_data)
                results.extend(chunk_results)

            return results

    def _bin_data(self, conn_gdf, gateway_gdf, bin_size_seconds=0.1):
        """Bin all data at once for a chunk of connections"""
        bin_factor = 1.0 / bin_size_seconds
        
        # Bin all data at once
        gateway_gdf['time_bin'] = cp.floor(gateway_gdf['ts_relative'].values * bin_factor) / bin_factor
        conn_gdf['time_bin'] = cp.floor(conn_gdf['ts_relative'].values * bin_factor) / bin_factor

        # Group and sum in single operations
        gateway_binned = gateway_gdf.groupby('time_bin')['pkt_len'].sum().reset_index()
        conn_binned = conn_gdf.groupby(['conn', 'time_bin'])['pkt_len'].sum().reset_index()

        return {'gateway': gateway_binned, 'connections': conn_binned}

    def _process_correlations(self, binned_data):
        """Process correlations for multiple connections in parallel"""
        results = []
        gateway_binned = binned_data['gateway']
        conn_binned = binned_data['connections']

        # Process each connection's correlation in parallel using CuPy
        for conn in conn_binned['conn'].unique():
            conn_data = conn_binned[conn_binned['conn'] == conn]
            
            # Merge gateway and connection data
            merged = gateway_binned.merge(conn_data, on='time_bin', how='outer').fillna(0)
            
            # Convert to CuPy arrays for faster computation
            gw_array = cp.asarray(merged['pkt_len_x'].values)
            conn_array = cp.asarray(merged['pkt_len_y'].values)
            
            # Compute correlation metrics
            metrics = self._compute_correlation_metrics(gw_array, conn_array)
            results.append((conn, *metrics))

        return results

    def _compute_correlation_metrics(self, gw_array, conn_array):
        """Compute correlation metrics using GPU acceleration"""
        # Standardize arrays
        gw_std = self.scaler.fit_transform(gw_array.reshape(-1, 1)).ravel()
        conn_std = self.scaler.fit_transform(conn_array.reshape(-1, 1)).ravel()
        
        # Compute correlation array
        corr_array = gw_std * conn_std
        
        # Calculate metrics
        return get_metrics(corr_array)

def process_connection(folder_name, prefix, pkt_limit, processor):
    """Process a single connection using the GPU batch processor"""
    gateway_file = os.path.join(folder_name, "proxy_conn.csv")
    conn_file = os.path.join(folder_name, f'{prefix}_conn_labeled.csv')

    if not os.path.exists(gateway_file) or not os.path.exists(conn_file):
        return []

    # Load and preprocess data
    df = pd.read_csv(conn_file)
    gateway_df = pd.read_csv(gateway_file)
    unbiased_df = apply_bias_removal(df, pkt_limit, True, EMPIRICAL_PACKET_LENS, BG_DST_MEAN, BG_DST_STD)

    # Process data in GPU batch
    connections_data = {
        'gateway': gateway_df,
        'connections': unbiased_df
    }
    results = processor.process_connection_batch(connections_data)
    
    # Convert results to DataFrame
    result_df = pd.DataFrame(results, columns=[
        'conn', 'corr_count', 'corr_sum', 'corr_mean', 'corr_median',
        'corr_minimum', 'corr_maximum', 'corr_range', 'corr_variance', 'corr_std_dev'
    ])
    result_df['pcap_nb'] = folder_name
    
    return result_df.to_dict('records')

def process_batch(folder_paths, prefix, pkt_limit, gpu_id):
    """Process a batch of folders using a single GPU"""
    processor = GPUBatchProcessor(gpu_id, batch_size=1000)
    batch_results = []
    
    for path in folder_paths:
        results = process_connection(path, prefix, pkt_limit, processor)
        if results:
            df = pd.DataFrame(results)
            df['label'] = 1 if prefix == "relayed" else 0
            batch_results.append(df)
    
    return batch_results

def save_batch(data_dfs, prefix, set_name, batch_num):
    """Save a batch of data to CSV"""
    if not data_dfs:
        return
    
    batch_df = pd.concat(data_dfs)
    output_dir = f'data/subset_03_18/{set_name}'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f'{prefix}_corr_batch_{batch_num}.csv')
    batch_df.to_csv(output_file, index=False)
    print(f"Saved {prefix} batch {batch_num} with {len(batch_df)} rows")

def process_batch(folder_paths, prefix, pkt_limit, n_gpus):
    """Process a batch of folders using multiple GPUs"""
    batch_results = []
    
    with ThreadPoolExecutor(max_workers=n_gpus) as executor:
        # Distribute work across GPUs
        futures = {}
        for i, path in enumerate(folder_paths):
            gpu_id = i % n_gpus
            futures[executor.submit(process_connection, path, prefix, pkt_limit, gpu_id)] = path
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                df = pd.DataFrame(result)
                df['label'] = 1 if prefix == "relayed" else 0
                batch_results.append(df)
    
    return batch_results

def get_correlation_array_multithread(folder_paths, set_name, pkt_limit):
    prefixes = ["relayed", "background"]
    BATCH_SIZE = 20  # Number of folders to process before saving
    n_gpus = init_gpu_locks()  # Initialize GPU locks and get GPU count
    
    for prefix in prefixes:
        batch_number = 0
        total_batches = (len(folder_paths) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\nProcessing {prefix} data using {n_gpus} GPUs:")
        with tqdm(total=total_batches, desc=f"{prefix} batches") as batch_pbar:
            for i in range(0, len(folder_paths), BATCH_SIZE):
                batch_folders = folder_paths[i:i + BATCH_SIZE]
                batch_results = process_batch(batch_folders, prefix, pkt_limit, n_gpus)
                
                if batch_results:
                    save_batch(batch_results, prefix, set_name, batch_number)
                    batch_number += 1
                
                del batch_results
                batch_pbar.update(1)

def main():
    pkt_limit = 20
    
    train_path = "content/full_unbiased_features/train"
    test_path = "content/full_unbiased_features/test"
    val_path = "content/full_unbiased_features/val"
    
    train_folders = [os.path.join(train_path, folder) 
                    for folder in os.listdir(train_path) 
                    if os.path.isdir(os.path.join(train_path, folder))]
    
    test_folders = [os.path.join(test_path, folder) 
                    for folder in os.listdir(test_path) 
                    if os.path.isdir(os.path.join(test_path, folder))]
    print(test_folders)
    val_folders = [os.path.join(val_path, folder) 
                    for folder in os.listdir(val_path) 
                    if os.path.isdir(os.path.join(val_path, folder))]
    

    # Get distribution info from json file
    load_empirical_samples('background_distributions.json')
    
    print("Processing test set...")
    get_correlation_array_multithread(test_folders, "test", pkt_limit)
    print("Processing validation set...")
    get_correlation_array_multithread(val_folders, "val", pkt_limit)
    print("Processing training set...")
    get_correlation_array_multithread(train_folders, "train", pkt_limit)


if __name__ == "__main__":
    main()