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

*Coming soon*

### Prerequisites

### Usage

### Output

## 4. SLT (Shining Light into the Tunnel) Features

*Coming soon*

### Prerequisites

### Usage

### Output
