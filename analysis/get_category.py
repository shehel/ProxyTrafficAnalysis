#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 10:35:23 2024

@author: mounarabhi
"""

import requests
import pandas as pd
import time
import json
import re
import os


def check_domain_virustotal(domain, api_key):
     """Check if a domain is suspicious, get its category, combined score, and top 3 threat types."""
     url = f'https://www.virustotal.com/api/v3/domains/{domain}'
     headers = {
         'x-apikey': api_key
     }
     response = requests.get(url, headers=headers)
     
     if response.status_code == 200:
         data = response.json()
         
         # Check if the domain is flagged as suspicious
         stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
         is_suspicious = stats.get("malicious", 0) > 0 or stats.get("suspicious", 0) > 0
         
         # Calculate combined score
         malicious_count = stats.get("malicious", 0)
         suspicious_count = stats.get("suspicious", 0)
         combined_score = malicious_count + suspicious_count
         
         threat_details = []
         last_analysis_results = data.get("data", {}).get("attributes", {}).get("last_analysis_results", {})
         for engine, result in last_analysis_results.items():
             category = result.get("category")
             if category and category not in ["undetected", "harmless"]:
                 threat_details.append(f"{engine}: {category}")
         
         top_threats = threat_details[:3]
         
         category_data = data.get("data", {}).get("attributes", {}).get("categories", {})
         
         return is_suspicious, category_data, combined_score, top_threats
     
     return False, "Unknown", 0, []

def count_suspicious_domains_with_categories(server_names, api_key, 
                                             suspicious_output_file="suspicious_domains.txt", 
                                             category_log_file="relayed_conn_categories.txt", 
                                             request_limit=500):
    """Counts and lists suspicious domains with their categories, combined scores, and threat details."""
    suspicious_domains = []
    categories = []
    request_count = 0
    
    with open(suspicious_output_file, "a") as suspicious_file, open(category_log_file, "a") as category_file:
        for domain in server_names:
            try:
                if request_count >= request_limit:
                    api_key = API_KEY2  # Rotate API key after 500 requests
                    request_count = 0  # Reset request count
                
                is_suspicious, category, combined_score, top_threats = check_domain_virustotal(domain, api_key)
                
                # Log every server name and its details
                category_file.write(f"{domain} - Category: {category}, Combined Score: {combined_score}\n")
                category_file.flush()
                
                if is_suspicious:
                    suspicious_domains.append((domain, category, combined_score, top_threats))
                    categories.append(category)
                     
                    # Log suspicious domains with additional details
                    suspicious_file.write(
                        f"{domain} - Category: {category}, Combined Score: {combined_score}, "
                        f"Top Threats: {', '.join(top_threats)}\n"
                    )
                    suspicious_file.flush()
                
                request_count += 1  # Increment request count
                
            except Exception as e:
                print(f"Error checking domain {domain}: {e}")
            
            # Pause to comply with rate limits on the free VirusTotal API tier
            time.sleep(15)  # Adjust based on your API rate limit
    
    return suspicious_domains, categories


# Define API keys
API_KEY1= 'ea2578cdd53552c512c515d141844c92918e58ecd56496a3b3cd51ff5e7fcaf0'#MOONA ACCOUNR
API_KEY2="984eae34c118ddce9a06b27f65bd5921b6d70b28658e633f95d36ecea272ae9e" #QCRI ACCOUNT

main_directory = '/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/analysis_processed_sample'
folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]
mixed_folder_paths = [path for path in folder_paths if "mixed" in path]

All_categories = []
All_suspicious = []

for folder_path in mixed_folder_paths:
    
    relayed_traffic_path = os.path.join(folder_path, "relayed_conn_labeled.csv")
   
    relayed_traffic = pd.read_csv(relayed_traffic_path)
    relayed_conn_in = relayed_traffic[(relayed_traffic['dst_ip'] == '10.0.2.16') | (relayed_traffic['dst_ip'] == '10.0.2.15')]
    relayed_conn_out = relayed_traffic[(relayed_traffic['src_ip'] == '10.0.2.16') | (relayed_traffic['src_ip'] == '10.0.2.15')]
    server_names_relayed = relayed_traffic.server_name.unique()
    print(len(server_names_relayed))
    
    # Use the first API key for the initial requests
    suspicious_domains, categories = count_suspicious_domains_with_categories(server_names_relayed, API_KEY1)
    
    All_suspicious = All_suspicious + suspicious_domains
    All_categories = All_categories + categories
    
    # Output results
    print(f"Total suspicious domains found: {len(suspicious_domains)}")
    for domain, category, community_score, top_threats in suspicious_domains:
       print(f"{domain} - Category: {category}, Community Score: {community_score}, Top Threats: {', '.join(top_threats)}")

API_KEY = 'ea2578cdd53552c512c515d141844c92918e58ecd56496a3b3cd51ff5e7fcaf0'#MOONA ACCOUNR
#API_KEY="984eae34c118ddce9a06b27f65bd5921b6d70b28658e633f95d36ecea272ae9e" #QCRI ACCOUNT

main_directory = '/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/analysis_processed_sample'
folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]
mixed_folder_paths = [path for path in folder_paths if "mixed" in path]

for folder_path in mixed_folder_paths:
    
    relayed_traffic_path = os.path.join(folder_path, "relayed_conn_labeled.csv")
   
    
    relayed_traffic = pd.read_csv(relayed_traffic_path)
    relayed_conn_in=relayed_traffic[(relayed_traffic['dst_ip'] == '10.0.2.16')| (relayed_traffic['dst_ip'] == '10.0.2.15')]
    relayed_conn_out=relayed_traffic[(relayed_traffic['src_ip'] == '10.0.2.16')| (relayed_traffic['src_ip'] == '10.0.2.15')]
    server_names_relayed=relayed_traffic.server_name.unique()
    print(len(server_names_relayed))
    
    suspicious_domains,categories = count_suspicious_domains_with_categories(server_names_relayed)
    All_suspicious=All_suspicious+suspicious_domains
    All_categories=All_categories+categories
    
    # Output results
    print(f"Total suspicious domains found: {len(suspicious_domains)}")
    for domain, category, community_score, top_threats in suspicious_domains:
       print(f"{domain} - Category: {category}, Community Score: {community_score}, Top Threats: {', '.join(top_threats)}")
 