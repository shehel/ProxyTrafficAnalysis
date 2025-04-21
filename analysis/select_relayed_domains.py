#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 20 08:57:32 2025

@author: mrabhi
"""

import pandas as pd
import random
import requests

def is_accessible(domain):
    try:
        response = requests.get(f"http://{domain}", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False
# Load domains from unique_domains.csv
df = pd.read_csv("unique_domains.csv")
accessible_domains = []
for i in range(df.shape[0]):
    print(i)
    domain = df.iloc[i]['domain']
    if is_accessible(domain):
        accessible_domains.append(domain)

accessible_df = pd.DataFrame(accessible_domains, columns=['domain'])
        
selected_domains = set(df['domain'].sample(n=100, random_state=9))

# Load suspicious domains
with open("suspicious_domains2.txt", "r") as f:
    suspicious_data = f.readlines()

# Extract suspicious domain names from the data
suspicious_domains = set()
cleaned_lines = []
for line in suspicious_data:
    domain = line.split(" - ")[0].strip()
    suspicious_domains.add(domain)
    cleaned_lines.append(line)

# Remove selected domains if they exist in suspicious domains
filtered_domains = selected_domains - suspicious_domains

# Save the filtered list back to a new file
with open("filtered_domains.txt", "w") as f:
    for domain in filtered_domains:
        f.write(domain + "\n")

print("Filtered domain list saved to filtered_domains.txt")
