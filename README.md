# Network Traffic Processing Pipeline

This repository contains scripts for the following steps:
1. Collect network traffic data in PCAP format using Android Emulator running an automated browser and earnapp residential proxy. For Android packet capture, we use [PCAPdroid](https://github.com/emanuele-f/PCAPdroid), a powerful open-source packet capture tool running inside the emulator.
2. Process the captured network traffic data using Zeek and Tshark to extract app information from the PCAP files. 
3. Extract relevant features from the processed data.
4. Prepare the extracted features for machine learning with AutoGluon.

## Traffic Collection

## PCAP Processing 

### Generate Logs
Retrieve App names from PCAPs using tshark:
```bash
sh extract_feats/tshark.sh data/pcaps/<traffic_type>_N_<profile>.pcap
```
Generate logs from PCAP files using Zeek:
```bash
sh extract_feats/zeek.sh data/pcaps/<traffic_type>_N_<profile>.pcap
```
- `-C`: Ignore checksum errors
- `LogAscii::use_json=T`: Output logs in JSON format

### Process Log Files
Run the renaming script to ensure consistent file naming:
```bash
python3 extract_feats/rename.py
```
**Note**: Verify that the new filenames are correct after running the script.

Extract domains and connection lists from SSL logs:
```bash
python3 extract_feats/extract_domains.py
```
**Important**: Process one log file at a time.

Split and summarize connections from the PCAP file based on the connection list:
```bash
python3 extract_feats/split_connections.py
```

### Feature Extraction
Extract features from split proxy connections and normal connections:
```bash
python3 extract_feats/extract_features.py
```
Merge extracted features into a single dataset:
```bash
python3 extract_feats/merge_feats.py
```

### Model Training
Use the processed features to train AutoGluon models.

## Prerequisites

- Zeek 7.0.3
- Python 3.x
- AutoGluon library

## Directory Structure

The pipeline expects the following directory structure:
```
.
├── analysis/                             # Analysis scripts
├── data/pcaps/                           # Raw PCAP files
│   ├── <traffic_type>_N_<profile>.pcap
├── data/processed/                       # Processed PCAP data
│   ├── <traffic_type>_N_<profile> 
├── data/feats/                           # Extracted features
├── extract_feats/                        # PCAP feature extraction scripts
│   ├── zeek.sh
│   ├── tshark.sh
│   ├── rename.py
│   ├── extract_domains.py
│   ├── split_connections.py
│   ├── extract_features.py
│   └── merge_feats.py
├── res/                                  # Static resource files 

```

