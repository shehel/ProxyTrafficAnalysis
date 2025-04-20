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
folder_name = f"data/processed/{filename}"

# base path of scripts
base_path = "feature_extraction/pcaps"

# Ensure the folder exists
os.makedirs(folder_name, exist_ok=True)

# Commands to execute
commands = [
    f"cp {pcap_path} {folder_name}/mixed.pcap",
    f"zeek -C -r {folder_name}/mixed.pcap \"LogAscii::use_json=T\" local",
    # f"python {base_path}/rename_logs.py --folder {folder_name}",
    f"python {base_path}/extract_domains.py --folder {folder_name}",
    f"python {base_path}/split_connections.py --folder {folder_name}",
    f"sh {base_path}/tshark.sh {pcap_path} {folder_name}",
    f"python {base_path}/get_labeled_conn.py --folder_path {folder_name}"
    f"rm {folder_name}/mixed.pcap"
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
