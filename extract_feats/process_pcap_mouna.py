import os
import subprocess
from datetime import datetime
import argparse

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

# Get current date and time for folder name
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
folder_name = f"processed/folder_{current_datetime}"

# Ensure the folder exists
os.makedirs(folder_name, exist_ok=True)

# Commands to execute
commands = [
    f"cp {pcap_path} {folder_name}/mixed.pcap",
    f"zeek -C -r {folder_name}/mixed.pcap LogAscii::use_json=T",
    f"python3 extract_feats/rename_logs.py --folder {folder_name}",
    f"python3 extract_feats//extract_domains.py --folder {folder_name}",
    f"python3 extract_feats/split_connections.py --folder {folder_name}",
    f"sh extract_feats/tshark.sh {pcap_path} {folder_name}", 
    f"python3 extract_feats/get_labeled_conn.py --folder_path {folder_name}",
]

# Execute commands in sequence
for command in commands:
    try:
        print(f"Running: {command}")
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {command}")
        print(e)
        break
