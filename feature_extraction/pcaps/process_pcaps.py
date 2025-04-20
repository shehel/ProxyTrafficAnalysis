import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

base_path = "./"
pcap_folder = "data/external_pcaps/vnat"
processed_folder = os.path.join(base_path, "processed_vnat/")
extract_feats_folder = os.path.join(base_path, "extract_feats")

if not os.path.exists(pcap_folder):
    print(f"Error: PCAP folder '{pcap_folder}' does not exist.")
    exit(1)

os.makedirs(processed_folder, exist_ok=True)

def process_pcap(file_info):
    """Function to process a single PCAP file."""
    root, file = file_info
    pcap_path = os.path.join(root, file)
    pcap_name = os.path.splitext(file)[0]
    
    # Create a folder named after the PCAP file in the processed directory
    output_folder = os.path.join(processed_folder, pcap_name)
    if os.path.exists(output_folder):
       print(f"Skipping: Output folder '{output_folder}' already exists for PCAP '{file}'.")
    else:
        os.makedirs(output_folder, exist_ok=True)
    
        # Check if source file exists
        if not os.path.exists(pcap_path):
            print(f"Error: Source file '{pcap_path}' does not exist.")
            return
    
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

pcap_files = []
for root, _, files in os.walk(pcap_folder):
    for file in files:
        if file.endswith(".pcap"):
            pcap_files.append((root, file))
with ThreadPoolExecutor(max_workers=7) as executor:
    executor.map(process_pcap, pcap_files)

print("Processing completed.")