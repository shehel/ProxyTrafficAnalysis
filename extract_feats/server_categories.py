#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: server_categories.py

Description:
This script is designed to analyze and identify suspicious domains in a dataset of relayed server traffic.
It utilizes the VirusTotal API to check domains for suspicious activity, retrieve their categories,
calculate combined scores based on malicious and suspicious indicators, and log the results.

Key Features:
1. Filters out domains matching specific patterns or keywords (e.g., common API subdomains).
2. Uses VirusTotal API to retrieve domain details, such as categories, combined scores, and top threat types.
3. Stores suspicious domain results in an output file (`suspicious_domains_medium.txt`).
4. Logs all analyzed domain categories and scores in a secondary file (`relayed_conn_categories_medium.txt`).
5. Processes a filtered list of server names extracted from relayed traffic data.

Dependencies:
- External libraries: requests, pandas, tqdm, re, json, csv
- A valid VirusTotal API key is required (set in the `API_KEY` variable).
- The input dataset should be available at the specified path (`relayed_traffic_path`).

Usage:
- Adjust the API key variable (`API_KEY`) with a valid VirusTotal key.
- Modify the input file path (`relayed_traffic_path`) if needed.
- Run the script to analyze domains and generate output files for suspicious domains and their categories.

Author:
This script was created by Mounarabhi and serves as a utility for analyzing server traffic and identifying threats.

Created on: November 10, 2024
"""

import requests
import pandas as pd
import time
import json
import re

from tqdm import tqdm
import csv


def filter_internal_apis(df, column_name):
    general_api_pattern = (
        r'(api|cdn|static|content|assets|media|services|resources|cloud|cloudfare|gateway'
        r'|ibytedtos|googleapis|gvt1|gstatic|ttwstatic|googleusercontent)\.'  # common API-related subdomains
    )
    
    def is_internal_api(domain):
        if domain and isinstance(domain, str):
            return re.search(general_api_pattern, domain) is not None
        return False    
    filtered_df = df[~df[column_name].apply(is_internal_api)]
    
    return filtered_df
def check_domain_virustotal(domain):
     """Check if a domain is suspicious, get its category, combined score, and top 3 threat types."""
     url = f'https://www.virustotal.com/api/v3/domains/{domain}'
     headers = {
         'x-apikey': API_KEY
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
         
         return is_suspicious, category, combined_score, top_threats
     
     return False, "Unknown", 0, []


def count_suspicious_domains_with_categories(server_names, 
                                          suspicious_output_file="suspicious_domains_medium.txt", 
                                          category_log_file="relayed_conn_categories_medium.txt"):
     """Counts and lists suspicious domains with their categories, combined scores, and threat details."""
     suspicious_domains = []
     categories = []

     with open(suspicious_output_file, "a", newline="") as suspicious_file, \
             open(category_log_file, "a", newline="") as category_file:

         # CSV writers
         suspicious_writer = csv.writer(suspicious_file)
         category_writer = csv.writer(category_file)

         # Write headers only if the file is empty
         if suspicious_file.tell() == 0:
             suspicious_writer.writerow(["Domain", "Category", "Combined Score", "Top Threats"])
         if category_file.tell() == 0:
             category_writer.writerow(["Domain", "Category", "Combined Score"])

         for domain in tqdm(server_names, desc="Processing Domains", unit="domain"):
             try:
                 # Simulating a function call to check the domain (replace with the actual function)
                 is_suspicious, category, combined_score, top_threats = check_domain_virustotal(domain)

                 # Log every server name, category, and combined score
                 category_writer.writerow([domain, category, combined_score])
                 category_file.flush()  # Force writing to disk

                 if is_suspicious:
                     # Log suspicious domains with additional details
                     suspicious_writer.writerow([domain, category, combined_score, ", ".join(top_threats)])
                     suspicious_file.flush()  # Force writing to disk

             except Exception as e:
                 print(f"Error checking domain {domain}: {e}")

             # Pause to comply with rate limits on the free VirusTotal API tier
             time.sleep(15)  # Adjust based on your API rate limit
     
     return suspicious_domains, categories
#############################################
All_categories=[]
All_suspicious=[]
API_KEY = 'ea2578cdd53552c512c515d141844c92918e58ecd56496a3b3cd51ff5e7fcaf0'#MOONA ACCOUNR
#API_KEY="984eae34c118ddce9a06b27f65bd5921b6d70b28658e633f95d36ecea272ae9e" #QCRI ACCOUNT

relayed_traffic_path = ("/home/temoorali/Documents/ProxyTrafficAnalysis/data/processed"
                        "/merged_relayed_conn.csv")



relayed_traffic = pd.read_csv(relayed_traffic_path)
relayed_conn_in=relayed_traffic[(relayed_traffic['dst_ip'] == '10.0.2.16')|
                                (relayed_traffic['dst_ip'] == '10.0.2.15')]
relayed_conn_out=relayed_traffic[(relayed_traffic['src_ip'] == '10.0.2.16')|
                                 (relayed_traffic['src_ip'] == '10.0.2.15')]
server_names_relayed=relayed_traffic.server_name.unique()

# Filter out domains containing specific keywords
filtered_server_names_relayed = [
    server_name for server_name in server_names_relayed
    if not any(keyword in server_name for keyword in ["google", "instagram", "earnapp", "clientsdk.lum-sdk.io"])
]

print(filtered_server_names_relayed)

suspicious_domains,categories = count_suspicious_domains_with_categories(filtered_server_names_relayed)
All_suspicious=All_suspicious+suspicious_domains
All_categories=All_categories+categories
#
# # Output results
print(f"Total suspicious domains found: {len(suspicious_domains)}")
for domain, category, community_score, top_threats in suspicious_domains:
   print(f"{domain} - Category: {category}, Community Score: {community_score}, "
         f"Top Threats: {', '.join(top_threats)}")

