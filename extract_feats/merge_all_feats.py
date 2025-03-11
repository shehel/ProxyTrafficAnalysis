#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 19 10:41:39 2025

@author: mounarabhi
"""
import pandas as pd
relayed_fts_train_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/features_lim_relayed_train_rtt.csv'
background_fts_train_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/features_lim_background_train_rtt.csv'
relayed_fts_test_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/features_lim_relayed_test_rtt.csv'
background_fts_test_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/features_lim_background_test_rtt.csv'
relayed_feats_val_path='/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/features_lim_relayed_val_rtt.csv'
background_feats_val_path='/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/features_lim_background_val_rtt.csv'


relayed_feats_train=pd.read_csv(relayed_fts_train_path)
background_feats_train=pd.read_csv(background_fts_train_path)

relayed_feats_test=pd.read_csv(relayed_fts_test_path)
background_feats_test=pd.read_csv(background_fts_test_path)

relayed_feats_val=pd.read_csv(relayed_feats_val_path)
background_feats_val=pd.read_csv(background_feats_val_path)



relayed_corr_fts_train_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/feature_corr__relayed_train.csv'
background_corr_fts_train_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/feature_corr__background_train.csv'
relayed_corr_fts_test_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/feature_corr__relayed_test.csv'
background_corr_fts_test_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/feature_corr__background_test.csv'
relayed_corr_fts_val_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/feature_corr__relayed_val.csv'
background_corr_fts_val_path = '/Users/mounarabhi/Desktop/ProxyTrafficAnalysis/data/feats_new/feature_corr__background_val.csv'

relayed_corr_feats_train=pd.read_csv(relayed_corr_fts_train_path)
background_corr_feats_train=pd.read_csv(background_corr_fts_train_path)
relayed_corr_feats_test=pd.read_csv(relayed_corr_fts_test_path)
background_corr_feats_test=pd.read_csv(background_corr_fts_test_path)
relayed_corr_feats_val=pd.read_csv(relayed_corr_fts_val_path)
background_corr_feats_val=pd.read_csv(background_corr_fts_val_path)



relayed_feats_train['pcap_nb'] = relayed_feats_train['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
background_feats_train['pcap_nb'] = background_feats_train['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
relayed_feats_test['pcap_nb'] = relayed_feats_test['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
background_feats_test['pcap_nb'] = background_feats_test['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
relayed_feats_val['pcap_nb'] = relayed_feats_val['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
background_feats_val['pcap_nb'] = background_feats_val['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)

relayed_corr_feats_train['pcap_nb'] = relayed_corr_feats_train['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
background_corr_feats_train['pcap_nb'] = background_corr_feats_train['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
relayed_corr_feats_test['pcap_nb'] = relayed_corr_feats_test['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
background_corr_feats_test['pcap_nb'] = background_corr_feats_test['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
relayed_corr_feats_val['pcap_nb'] = relayed_corr_feats_val['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
background_corr_feats_val['pcap_nb'] = background_corr_feats_val['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)


# Merging relayed features and correlation features for train, test, and validation sets
relayed_train_merged = pd.merge(relayed_feats_train, relayed_corr_feats_train, on=['pcap_nb', 'conn'])
relayed_test_merged = pd.merge(relayed_feats_test, relayed_corr_feats_test, on=['pcap_nb', 'conn'])
relayed_val_merged = pd.merge(relayed_feats_val, relayed_corr_feats_val, on=['pcap_nb', 'conn'])

background_train_merged = pd.merge(background_feats_train, background_corr_feats_train, on=['pcap_nb', 'conn'])
background_test_merged = pd.merge(background_feats_test, background_corr_feats_test, on=['pcap_nb', 'conn'])
background_val_merged = pd.merge(background_feats_val, background_corr_feats_val, on=['pcap_nb', 'conn'])



"""

# Concatenating all relayed and background features for train, test, and validation sets
all_relayed_feats = pd.concat([relayed_feats_train, relayed_feats_test, relayed_feats_val], axis=0)
all_relayed_corr_feats = pd.concat([relayed_corr_feats_train, relayed_corr_feats_test, relayed_corr_feats_val], axis=0)

all_background_feats = pd.concat([background_feats_train, background_feats_test, background_feats_val], axis=0)
all_background_corr_feats = pd.concat([background_corr_feats_train, background_corr_feats_test, background_corr_feats_val], axis=0)


all_relayed_feats['pcap_nb'] = all_relayed_feats['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
all_relayed_corr_feats['pcap_nb'] = all_relayed_corr_feats['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)

all_background_feats['pcap_nb'] = all_background_feats['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)
all_background_corr_feats['pcap_nb'] = all_background_corr_feats['pcap_nb'].str.extract(r'(mixed_\d{2}_[^/]+)', expand=False)

# Merging all relayed features with correlation features
all_relayed_merged = pd.merge(all_relayed_feats, all_relayed_corr_feats, on=['pcap_nb', 'conn'])

# Merging all background features with correlation features
all_background_merged = pd.merge(all_background_feats, all_background_corr_feats, on=['pcap_nb', 'conn'])

# Verifying the merged datasets
print("All Relayed Merged Shape:", all_relayed_merged.shape)
print("All Background Merged Shape:", all_background_merged.shape)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Assuming all_relayed_merged and all_background_merged DataFrames are already created
# and 'max_corr' is the column of interest

# Set the plot style
sns.set(style="whitegrid")

# Create the plot
plt.figure(figsize=(12, 6))

# Plot the distribution of max_corr for relayed connections
sns.kdeplot(
    all_relayed_merged['max_corr'], 
    label='Relayed Connections', 
    color='blue', 
    fill=True, 
    alpha=0.5
)

# Plot the distribution of max_corr for background connections
sns.kdeplot(
    all_background_merged['max_corr'], 
    label='Background Connections', 
    color='orange', 
    fill=True, 
    alpha=0.5
)

# Add labels and title
plt.title('Distribution of Max Correlation (max_corr)', fontsize=16)
plt.xlabel('Max Correlation', fontsize=14)
plt.ylabel('Density', fontsize=14)
plt.legend(fontsize=12)

# Show the plot
plt.show()

from sklearn.model_selection import train_test_split

# Split all_relayed into train (60%), test (20%), and validation (20%)
all_relayed_train, all_relayed_temp = train_test_split(all_relayed_merged, test_size=0.4, random_state=42)
all_relayed_test, all_relayed_val = train_test_split(all_relayed_temp, test_size=0.5, random_state=42)

# Split all_background into train (60%), test (20%), and validation (20%)
all_background_train, all_background_temp = train_test_split(all_background_merged, test_size=0.4, random_state=42)
all_background_test, all_background_val = train_test_split(all_background_temp, test_size=0.5, random_state=42)

# Verify the splits by checking the shapes
print("All Relayed Train Shape:", all_relayed_train.shape)
print("All Relayed Test Shape:", all_relayed_test.shape)
print("All Relayed Validation Shape:", all_relayed_val.shape)

print("All Background Train Shape:", all_background_train.shape)
print("All Background Test Shape:", all_background_test.shape)
print("All Background Validation Shape:", all_background_val.shape)
"""
# Save the relayed features
all_relayed_train.to_csv('all_relayed_train.csv', index=False)
all_relayed_test.to_csv('all_relayed_test.csv', index=False)
all_relayed_val.to_csv('all_relayed_val.csv', index=False)

# Save the background features
all_background_train.to_csv('all_background_train.csv', index=False)
all_background_test.to_csv('all_background_test.csv', index=False)
all_background_val.to_csv('all_background_val.csv', index=False)

# Confirm that the files have been saved
print("Relayed and Background feature files saved as CSV.")
