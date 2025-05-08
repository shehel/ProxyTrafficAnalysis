# Network Traffic Processing Pipeline

This repository contains scripts for the following steps:
1. Collect network traffic data in PCAP format using Android Emulator running an automated browser and earnapp residential proxy. For Android packet capture, we use [PCAPdroid](https://github.com/emanuele-f/PCAPdroid), a powerful open-source packet capture tool running inside the emulator.
2. Process the captured network traffic data using Zeek and Tshark to extract app information from the PCAP files. 
3. Extract relevant features from the processed data.
4. Prepare the extracted features for machine learning with AutoGluon.

## Repository Overview

This repository is organized into several modules, each focused on a specific task in the network traffic analysis pipeline:

- **Feature Extraction**  
  Process raw PCAPs into CSV logs and extract detailed features.  
  See [feature_extraction/README.md](feature_extraction/README.md).

- **Emulator**  
  Automate traffic data collection using a rooted Android emulator.  
  See [emulator/README.md](emulator/README.md).

- **Classification**  
  Run experiments using AutoGluon for network traffic classification with multiple feature sets.  
  See [classification/README.md](classification/README.md).

- **Analysis**  
  Process, analyze, and visualize network traffic data, including threat detection and traffic profiling.  
  See [analysis/README.md](analysis/README.md).

## Complete Pipeline Overview

1. **Collection:**  
   Traffic is captured using an Android emulator setup.
   - See the Emulator module for details on capturing PCAP files.

2. **Processing:**  
   Captured PCAP files are processed using Zeek and Tshark.
   - Refer to the Feature Extraction module for processing scripts.

3. **Feature Extraction:**  
   Extract features from processed PCAP logs including statistical metrics.
   - Detailed documentation is in the Feature Extraction module.

4. **Classification:**  
   Train and evaluate AutoGluon models on the extracted features.
   - Configuration and experiment details are in the Classification module.

5. **Analysis:**  
   Analyze connection patterns, threat metrics, and DNS logs.
   - For a comprehensive explanation, see the Analysis module.

## Prerequisites

- Zeek 7.0.3
- Python 3.x
- AutoGluon library

## Directory Structure

```
├── analysis/                    # Traffic analysis and visualization scripts
├── classification/             # AutoGluon classification experiments
│   ├── config/                 # Experiment configurations
│   └── models/                 # Trained model outputs
├── data/                       # Data directory
│   ├── pcaps/                 # Raw PCAP files
│   ├── processed/             # Processed PCAP data
│   └── features/              # Extracted feature sets
├── emulator/                   # Android emulator automation scripts
│   ├── scripts/               # Helper scripts for emulator
│   └── logs/                  # Emulator session logs
├── feature_extraction/         # Feature extraction pipeline
│   ├── correlation/           # Correlation feature scripts
│   └── traffic_analysis/      # Traffic analysis features
└── res/                       # Static resource files
```