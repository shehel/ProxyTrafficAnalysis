import os
import subprocess
from datetime import datetime
import argparse
import re

# Argument parsing
parser = argparse.ArgumentParser(description="Process PCAP files with Zeek and custom scripts.")
parser.add_argument("--pcap_path", type=str, required=True, help="Path to the PCAP file to process.")
args = parser.parse_args()

# Get the pcap path from the argument
pcap_path = args.pcap_path

# Check if the provided pcap path exists
if not os.path.exists(pcap_path):
    print(f"Error: PCAP file '{pcap_path}' does not exist.")
    exit(1)


# Get orig name of file 
filename = os.path.basename(pcap_path)[:-5]
output_folder = f"data/processed/{filename}"

# base path of scripts
extract_feats_folder = "feature_extraction/pcaps"

# Ensure the folder exists
os.makedirs(output_folder, exist_ok=True)

# Commands to execute
commands = [
    f"cp {pcap_path} {output_folder}/mixed.pcap",
    f"cd {output_folder} && zeek -C -r mixed.pcap 'LogAscii::use_json=T' local",
    f"python3 {os.path.join(extract_feats_folder, 'extract_domains.py')} --folder {output_folder}",
    f"python3 {os.path.join(extract_feats_folder, 'split_connections.py')} --folder {output_folder}",
    f"sh {os.path.join(extract_feats_folder, 'tshark.sh')} {pcap_path} {output_folder}", 
    f"python3 {os.path.join(extract_feats_folder, 'get_labeled_conn.py')} --folder_path {output_folder}",
    f"rm {output_folder}/mixed.pcap",
]

for command in commands:
    try:
        print(f"Running: {command}")
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {command}")
        print(e)
        break
