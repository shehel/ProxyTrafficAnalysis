#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 10:07:09 2025

@author: mrabhi
"""

import requests
import pandas as pd
import time
import itertools

# Define API keys and setup rotation
API_KEYS = [
    
   
    '119d1bc7ac3bea640b784d345d60e43a1cf15e495c274edc3d3ffa04f86fc758',
    '984eae34c118ddce9a06b27f65bd5921b6d70b28658e633f95d36ecea272ae9e',
    'b8f2cf2b6da4a380a67ee47a4ba972e2240cce504900a2e31102566c599bebcc',
    'ea2578cdd53552c512c515d141844c92918e58ecd56496a3b3cd51ff5e7fcaf0',
    '984eae34c118ddce9a06b27f65bd5921b6d70b28658e633f95d36ecea272ae9e',
    'd5b8b58df8f7297f65dbbd53d2f7c9a0c1a73bf43c74ba9a16fc29a398965beb'
]
api_key_cycle = itertools.cycle(API_KEYS)

def check_domain_virustotal(domain, api_key):
    url = f'https://www.virustotal.com/api/v3/domains/{domain}'
    headers = {'x-apikey': api_key}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        is_suspicious = stats.get("malicious", 0) > 0 or stats.get("suspicious", 0) > 0
        
        combined_score = stats.get("malicious", 0) + stats.get("suspicious", 0)
        threat_details = [f"{engine}: {result.get('category')}" for engine, result in
                          data.get("data", {}).get("attributes", {}).get("last_analysis_results", {}).items()
                          if result.get("category") not in ["undetected", "harmless"]]
        
        return is_suspicious, data.get("data", {}).get("attributes", {}).get("categories", {}), combined_score, threat_details[:3]
    
    return False, "Unknown", 0, []

def load_suspicious_domains(file_path):
    try:
        with open(file_path, "r") as f:
            return set(line.strip().split(" ")[0] for line in f if line.strip())
    except FileNotFoundError:
        return set()

def process_domains(input_file="unique_domains.csv", request_limit=499,
                     suspicious_output_file="suspicious_domains2.txt",
                     category_log_file="relayed_conn_categories2.txt"):
    df = pd.read_csv(input_file)
    domains = df["domain"].dropna().unique()
    
    existing_suspicious = load_suspicious_domains(suspicious_output_file)
    request_count = 0
    current_api_key = next(api_key_cycle)
    
    with open(suspicious_output_file, "a") as suspicious_file, open(category_log_file, "a") as category_file:
        for domain in domains:
            if domain in existing_suspicious:
                print(f"Skipping {domain}, already marked suspicious.")
                continue
            
            if request_count >= request_limit:
                print("API_changed")
                current_api_key = next(api_key_cycle)
                request_count = 0  # Reset count when API key rotates
            
            try:
                is_suspicious, category, combined_score, top_threats = check_domain_virustotal(domain, current_api_key)
                category_file.write(f"{domain} - Category: {category}, Combined Score: {combined_score}\n")
                category_file.flush()
                
                if is_suspicious:
                    print(f"{domain} - Category: {category}, Combined Score: {combined_score}\n")

                    suspicious_file.write(f"{domain} - Category: {category}, Combined Score: {combined_score}, Top Threats: {', '.join(top_threats)}\n")
                    suspicious_file.flush()
                
                request_count += 1
                time.sleep(15)  # Adjust this delay as needed
            except Exception as e:
                print(f"Error checking domain {domain}: {e}")

# Run the process
df_path = "unique_domains.csv"  # Update this if needed
process_domains(df_path)
