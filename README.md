# Network Traffic Processing Pipeline

This repository contains scripts for the following steps:
1. Collect network traffic data in PCAP format using Android Emulator running an automated browser and earnapp residential proxy. For Android packet capture, we use [PCAPdroid](https://github.com/emanuele-f/PCAPdroid), a powerful open-source packet capture tool running inside the emulator.
2. Process the captured network traffic data using Zeek and Tshark to extract app information from the PCAP files. 
3. Extract relevant features from the processed data.
4. Prepare the extracted features for machine learning with AutoGluon.

## Traffic Collection

## PCAP Processing 

### Quick Start
1. `extract_feats/process_pcaps.py` to process all PCAPs in a specified directory.
2. `extract_feats/get_all_features_lim_lbl.py` to extract features from the processed PCAPs.
3. [Optional] `extract_feats/get_correlation_feature_multithread.py` to extract correlation features from the processed PCAPs.
4. [Optional]`extract_feats/merge_all_feats.py` to merge the correalation features with the rest of the features in 2.
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
Run the below scrip to get connections split between proxy (gateway) and normal (background + relay):
```bash
python3 extract_feats/process_pcap.py --pcap_path {PCAP_PATH}
```

### Get labeled traffic 
```bash
extract_feats/get_labeled_conn.py --number n --suffix profile
```

n: the total number of pcaps
profile: low/medium/high


### Feature Extraction
Extract features from split proxy connections and normal connections:

```bash
python3 extract_feats/get_all_features_lim_lbl.py --prefix p --number n --suffix profile --limit x
```
p: the prefix either background or relayed
profile: low/medium/high
n: the total number of files used
limit: packet limit to be used for the features extraction ( 50 in our case)

### Model Training
Use the processed features to train AutoGluon models.

## Prerequisites

- Zeek 7.0.3
- Python 3.x
- AutoGluon library

## Directory Structure

The pipeline expects the following directory structure:
```
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