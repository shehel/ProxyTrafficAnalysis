# Feature Extraction Pipeline

This module handles the multi-stage feature extraction process for proxy traffic analysis.

## 1. PCAP to CSV Extraction

The first stage processes raw PCAP files to extract basic CSV features using Zeek and tshark.

### Prerequisites

- Zeek
- tshark
- Python ≥ 3.9

### Usage

For processing multiple PCAPs:
```bash
python pcaps/process_pcaps.py --input /path/to/pcaps/folder --output /path/to/output/folder
```

For a single PCAP:
```bash
python pcaps/process_single_pcap.py --pcap_path /path/to/file.pcap
```

### Output Structure

Each processed PCAP creates a directory containing:
- `conn.log` - Zeek connection logs
- `dns.log` - Zeek DNS logs
- `http.log` - Zeek HTTP logs
- `ssl.log` - Zeek SSL/TLS logs
- `domains.csv` - Extracted domain information
- `features.csv` - Basic traffic features
- `background_labeled_connections.csv` - Background connection data
- `relayed_labeled_connections.csv` - Relayed connection data


The `background_labeled_connections.csv` and `relayed_labeled_connections.csv` are then used in later sections.

## 2. Correlation Feature Extraction

This stage analyzes the correlation between gateway traffic and individual connections, computing various statistical metrics using GPU acceleration.

### Prerequisites

- Python ≥ 3.9
- CUDA-capable GPU
- Required Python packages:
  - cuDF
  - CuPy
  - cuML
  - pandas
  - numpy
  - scipy

### Usage

Process correlation features from processed PCAP data:
```bash
python correlation/get_correlation_features.py --folder_path /path/to/processed/pcaps --output_dir /path/to/output --pkt_limit 50
```

Parameters:
- `--folder_path`: Directory containing processed PCAP folders
- `--output_dir`: Where to save correlation features
- `--pkt_limit`: Maximum number of packets to analyze per connection (default: 50)

### Output

The script generates batch files for both background and relayed traffic:
- `background_corr_batch_*.csv`
- `relayed_corr_batch_*.csv`

Each CSV contains the following correlation metrics:
- Count
- Sum
- Mean
- Median
- Minimum
- Maximum
- Range
- Variance
- Standard Deviation

## 3. Traffic Analysis Features

This stage extracts detailed traffic analysis features from processed connections, including statistical metrics, packet timing, and behavioral patterns.

There are two scripts available:

1. Basic Feature Extraction (get_all_features.py):
   ```bash
   python traffic_analysis/get_all_features.py --folder_path /path/to/pcaps \
   --pkt_limit 50 \
   --output_dir /path/to/output
   ```
   Parameters:
   - `--folder_path`: Path to the folder containing PCAP files (required).
   - `--pkt_limit`: Maximum number of packets to analyze per connection (default: 50).
   - `--output_dir`: Directory where results will be saved (required).

2. Advanced 3-Way Classification Feature Extraction (get_all_features_lim_subset_3way.py):
   ```bash
   python traffic_analysis/get_all_features_lim_subset_3way.py --folder_path /path/to/pcaps \
   --pkt_limit 20 \
   --output_dir /path/to/output \
   --json_path feature_extraction/background_distributions.json \
   [--no_batching]
   ```
   Parameters:
   - `--folder_path`: Path to the folder containing PCAP files (required).
   - `--pkt_limit`: Maximum number of packets to analyze per connection (default: 20).
   - `--output_dir`: Directory where results will be saved (required).
   - `--json_path`: Path to the background distributions JSON file (default: feature_extraction/background_distributions.json).
   - `--no_batching`: Optional flag to process all files without batching.

## 4. SLT (Shining Light into the Tunnel) Features

*Coming soon*

### Prerequisites

### Usage

### Output
