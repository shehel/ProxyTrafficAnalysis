#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  1 10:21:46 2024

@author: mounarabhi
"""
import pandas as pd
import json
import matplotlib.pyplot as plt

suffixes = ["low", "high", "medium"]
all_requests = []  # List to store all DNS queries across files
all_rejected_queries = []  # List to store rejected queries across files

for i in range(30):
    for suffix in suffixes:
        dns_log_file = f"/Users/mounarabhi/Library/CloudStorage/OneDrive-HamadbinKhalifaUniversity/Extracted_traffic_mouna/dns/dns_{i}_{suffix}.log"
        
        records = []
        try:
            with open(dns_log_file, 'r') as file:
                for line in file:
                    # Parse each line as JSON
                    try:
                        record = json.loads(line.strip())
                        records.append(record)
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse line: {line.strip()} - Error: {e}")
            
            # Convert to DataFrame
            dns_data = pd.DataFrame(records)
            
            # Append all requests
            all_requests.append(dns_data)
            
            # Filter rows where 'rejected' is True and 'rcode' > 0
            rejected_queries = dns_data[(dns_data['rejected'] == True) & (dns_data['rcode'] > 0)]
            
            # Append filtered rejections
            all_rejected_queries.append(rejected_queries)
        
        except FileNotFoundError:
            print(f"File not found: {dns_log_file}")
        except Exception as e:
            print(f"Error processing file {dns_log_file}: {e}")

# Combine all requests and rejections into DataFrames
all_requests_df = pd.concat(all_requests, ignore_index=True)
all_rejected_df = pd.concat(all_rejected_queries, ignore_index=True)

# Calculate total requests and total rejections
total_requests = len(all_requests_df)
total_rejections = len(all_rejected_df)

# Calculate proportion of rejections
proportion_rejections = total_rejections / total_requests

# Plot the total requests vs. rejections
plt.figure(figsize=(8, 6))
labels = ['Total Requests', 'Rejections']
values = [total_requests, total_rejections]
colors = ['skyblue', 'salmon']

plt.bar(labels, values, color=colors)
plt.title("Total DNS Requests vs. Rejections (Filtered by RCODE > 0)")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig("dns_requests_vs_rejections.png")
plt.show()

# Print summary
print(f"Total Requests: {total_requests}")
print(f"Total Rejections (RCODE > 0): {total_rejections}")
print(f"Proportion of Rejections: {proportion_rejections:.2%}")


rcode_counts = all_rejected_df['rcode'].value_counts()

rcode_2_and_3 = rcode_counts[rcode_counts.index.isin([2, 3])]

plt.figure(figsize=(8, 6))
rcode_2_and_3.plot(kind='bar', color=['skyblue', 'salmon'])
plt.title("Count of Rejections by RCODE (2 and 3)")
plt.xlabel("RCODE")
plt.ylabel("Count")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("rejections_by_rcode_2_and_3.png")
plt.show()

# Print the counts for rcode 2 and 3
print("Rejection counts for RCODE 2 and 3:")
print(rcode_2_and_3)

