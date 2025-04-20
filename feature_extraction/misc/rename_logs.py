import os
import shutil
import argparse

# Set up argument parsing
parser = argparse.ArgumentParser(description="Organize log files into a numbered folder.")
parser.add_argument("--folder", type=str, required=True, help="The name used for folder to save results in")
args = parser.parse_args()

# Get the number from the command-line argument
folder = args.folder

# Create a folder named 'traffic_{number}'
folder_name = f"{folder}"
os.makedirs(folder_name, exist_ok=True)

# List of files to be moved
files = [
    'conn.log',
    'dns.log',
    'http.log',
    'dhcp.log',
    'ntp.log',
    'packet_filter.log',
    'ssl.log',
    'x509.log',
    'files.log'
]

# Move each file into the folder
for file in files:
    if os.path.exists(file):  # Check if the file exists before moving
        shutil.move(file, os.path.join(folder_name, file))

print(f"Files have been moved to folder: {folder_name}")
