#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 14:05:01 2025

@author: mounarabhi
"""
import os
import pandas as pd

main_directory = '/home/mrabhi/Downloads/ProxyTrafficAnalysis-main/data/processed_new'

folder_paths = [os.path.join(main_directory, folder) for folder in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, folder))]
mixed_folder_paths = [path for path in folder_paths if "mixed" in path]
sum_pckts=0
nb_relayed=0
nb_bg=0
nb_gw=0
i=0
for folder_name in mixed_folder_paths:
    i+=1
    print(i)
    relayed_path =folder_name+'/relayed_conn_labeled.csv'
    bg_path=folder_name+'/background_conn_labeled.csv'
    gw_path=folder_name+'/proxy_conn.csv'
    relayed_df = pd.read_csv(relayed_path)
    bg_df = pd.read_csv(bg_path)
    gw_df = pd.read_csv(gw_path)
    nb_relayed+= len(relayed_df.groupby('conn'))
    nb_gw+=len(gw_df.groupby('conn'))
    nb_bg+=len(bg_df.groupby('conn'))
    pcap_size_bytes = relayed_df['pkt_len'].sum()
    sum_pckts+=pcap_size_bytes
    

    
total_size_gb = sum_pckts / (1024 ** 3)
print(total_size_gb)