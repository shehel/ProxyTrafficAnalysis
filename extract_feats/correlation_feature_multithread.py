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


def get_correlation_array(gateway_df, df, pkt_limit, bin_size_seconds=0.1, bound_range=1.0):
    """
    GPU-accelerated approach using cuDF & CuPy.
    - Sorts and bins data once.
    - Uses searchsorted for gateway slices.
    - Avoids .itertuples() or .iterrows() on cuDF.

    If you have large data, consider Dask-cuDF for multi-GPU or out-of-core.
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


def process_connection(folder_name, prefix, pkt_limit):
    all_data = []
    gateway_file_path = os.path.join(folder_name, "proxy_conn.csv")
    file_path = os.path.join(folder_name, f'{prefix}_conn_labeled.csv')

    if not os.path.exists(file_path) or not os.path.exists(gateway_file_path):
        return all_data

    df = pd.read_csv(file_path)
    gateway_df = pd.read_csv(gateway_file_path)
    correlation_df = get_correlation_array(gateway_df, df, pkt_limit)
    correlation_df['pcap_nb'] = folder_name
    all_data.extend(correlation_df.to_dict('records'))

    return all_data

def get_correlation_array_multithread(folder_paths, set_name, pkt_limit):
    prefixes = ["relayed", "background"]
    background_dfs = []
    relayed_dfs = []
    for prefix in tqdm(prefixes, desc="Processing prefixes"):
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_connection, path, prefix, pkt_limit): path for path in folder_paths}
            for future in tqdm(as_completed(futures),
                               total=len(futures),
                               desc=f"Processing {prefix} connections"):
                result = future.result()
                
                if prefix == "background":
                    background_df = pd.DataFrame(result)
                    background_df['label'] = 0
                    background_dfs.append(background_df)
                else:
                    relayed_df = pd.DataFrame(result)
                    relayed_df['label'] = 1
                    relayed_dfs.append(relayed_df)
                
    background_combined = pd.concat(background_dfs)
    relayed_combined = pd.concat(relayed_dfs)
    all_data_df = pd.concat([background_combined, relayed_combined])
    all_data_df.to_csv(f'content/subset_features_03_18/{set_name}/corr_feature_50.csv', index=False)
    
    return all_data_df

def main():
    pkt_limit = 20
    train_path = "data/subset_03_18/train"
    test_path = "data/subset_03_18/test"
    val_path = "data/subset_03_18/val"
    
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
    

    test_df = get_correlation_array_multithread(test_folders, "test", pkt_limit)
    val_df = get_correlation_array_multithread(val_folders, "val", pkt_limit)
    train_df = get_correlation_array_multithread(train_folders, "train", pkt_limit)

    # all_data_df = pd.concat([train_df, test_df, val_df], ignore_index=True)
    # print(all_data_df)

if __name__ == "__main__":
    main()


