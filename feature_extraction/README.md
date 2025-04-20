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
python pcaps/process_pcaps.py --input /path/to/pcap/folder --output /path/to/output/folder
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

## 2. Correlation Feature Extraction

*Coming soon*

### Prerequisites

### Usage

### Output

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
