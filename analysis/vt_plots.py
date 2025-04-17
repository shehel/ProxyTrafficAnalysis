#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 11:35:24 2025

@author: mrabhi
"""

import numpy as np
import matplotlib.pyplot as plt

# Read the file
with open("relayed_conn_categories2.txt", "r") as file:
    lines = file.readlines()

# Extract domains and combined scores
domains = []
scores = []

for line in lines:
    parts = line.split(" - ")
    if len(parts) > 1 and "Combined Score: " in parts[1]:
        domain = parts[0]
        try:
            combined_score = int(parts[1].split("Combined Score: ")[1].split(",")[0])
            domains.append(domain)
            scores.append(combined_score)
        except (IndexError, ValueError) as e:
            print(f"Skipping line due to error: {line} - {e}")


# Print the number of domains
num_domains = len(domains)
print(f"Number of domains: {num_domains}")

# Compute the CDF
scores_sorted = np.sort(scores)
cdf = np.arange(1, len(scores_sorted) + 1) / len(scores_sorted)

# Plot the CDF
plt.figure(figsize=(8, 5))
plt.scatter(scores_sorted, cdf, marker="o", linestyle="-", color="k")
plt.xlabel("Community Score", fontsize=15)
plt.xticks(np.arange(0,18,1 ))
plt.ylabel("CDF", fontsize=15)
#plt.title("CDF of com Scores")
plt.grid()
plt.savefig('vt_cdf.pdf', format='pdf')
plt.show()
