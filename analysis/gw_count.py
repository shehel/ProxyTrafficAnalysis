import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Define the main directory
main_directory = "/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/analysis_processed_sample"

# Get all subdirectories
folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]

# Filter only "mixed" folders
mixed_folder_paths = [path for path in folder_paths if "mixed" in path]

# Function to calculate duration, volume, and start time per connection
def calculate_duration_and_volume(df):
    df['ts_relative'] = pd.to_numeric(df['ts_relative'], errors='coerce')
    df['pkt_len'] = pd.to_numeric(df['pkt_len'], errors='coerce')

    # Compute duration, volume, and start time per connection
    stats = df.groupby('conn').agg(
        duration=('ts_relative', lambda x: x.max() - x.min()),
        volume=('pkt_len', 'sum'),
        start_time=('ts_relative', 'min')  # Earliest timestamp per connection
    ).reset_index()

    df = df.merge(stats, on='conn', how='left')
    return df

# Collect all counts of gateway starts within 0.1s
all_counts = []

# Process each PCAP directory
for folder_path in mixed_folder_paths:
    gateway_path = os.path.join(folder_path, "proxy_conn.csv")
    
    if os.path.exists(gateway_path):
        gateway_df = pd.read_csv(gateway_path)

        # Compute duration, volume, and start time
        gateway_df = calculate_duration_and_volume(gateway_df)

        # Extract unique start times for gateways
        start_times = gateway_df.groupby('server_name')['start_time'].min().sort_values().values

        if len(start_times) < 2:
            print("skipped")
            continue  # Skip if there's not enough data

        # Count how many start within 0.1s of each other
        count_per_folder = []
        count = 1  # Start with 1 (current gateway)
        
        for i in range(1, len(start_times)):
            if start_times[i] - start_times[i - 1] <= 0.1:
                count += 1  # Increase count for concurrent starts
            else:
                count_per_folder.append(count)  # Store count
                count = 1  # Reset count for the next group

        # Add the last counted group
        if count > 1:
            count_per_folder.append(count)

        # Collect all counts from this folder
        all_counts.extend(count_per_folder)

# Compute CDF
all_counts = np.array(all_counts)
all_counts_sorted = np.sort(all_counts)
cdf = np.arange(1, len(all_counts_sorted) + 1) / len(all_counts_sorted)

# Plot CDF
plt.figure(figsize=(10, 5))
plt.plot(all_counts_sorted, cdf, marker='o', linestyle='-', color='blue')

plt.xlabel('Number of Gateway Starts Within 0.1s')
plt.ylabel('CDF')
plt.title('CDF of Gateway Connection Start Clusters (0.1s window)')
plt.grid(True)

# Show plot
plt.show()
