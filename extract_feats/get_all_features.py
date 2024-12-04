#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:51:20 2024

@author: mounarabhi
"""
from extract_features import get_features
from host_features import extract_features_by_conn
import pandas as pd
import csv
fnames = ["intertimestats","timestats","number_pkts","thirtypkts","stdconc","avgconc","avg_per_sec","std_per_sec","avg_order_in","avg_order_out","std_order_in",
         "std_order_out","medconc","med_per_sec","min_per_sec","max_per_sec","maxconc","perc_in","perc_out","altconc","alt_per_sec","sum_altconc","sum_alt_per_sec","sum_intertimestats",
         "sum_timestats","sum_number_pkts"]
Features_names=["max_in", "max_out","max_total","avg_in","avg_out","avg_total","std_in","std_out","std_total","75th_percentile_in","75th_percentile_out","75th_percentile_total",
                "25th_percentile_in","50th_percentile_in","75th_percentile_in","100th_percentile_in","25th_percentile_out","50th_percentile_out","75th_percentile_out",
                "100th_percentile_out","25th_percentile_tot","50th_percentile_tot","75th_percentile_tot","100th_percentile_tot", "nb_pkts_in","nb_pkts_out","nb_pkts_total",
                "nb_pkts_in_f30","nb_pkts_out_f30","nb_pkts_in_l30","nb_pkts_out_l30","std_pkt_conc_out20", "avg_pkt_conc_out20","avg_per_sec","std_per_sec","avg_order_in",
                "avg_order_out","std_order_in","std_order_out","medconc","med_per_sec","min_per_sec","max_per_sec","maxconc","perc_in","perc_out","sum_altconc",
                "sum_alt_per_sec","sum_number_pkts","sum_intertimestats"]
Features_names.extend([f"altconc_{i+1}" for i in range(20)])       # 20 altconc
Features_names.extend([f"alt_per_sec_{i+1}" for i in range(20)])   # 20 alt_per_sec
Features_names.extend([f"conc_{i+1}" for i in range(60)])          # 60 conc
features_list=[]
for number in range(33):
    print(number)
    suffix="high"
    gw=True
    file_path="proxy_conn_"+str(number)+"_"+suffix+".csv"    
    feats = {}
    
    with open(file_path, 'r') as f:
        all_pkts = list(csv.reader(f, delimiter=','))
        curr_conn = ''
        conn_count = 0
        for idx, pkt in enumerate(all_pkts):
            if idx == 0:
                continue  # Skip the header row
            conn_name = pkt[0]
            if conn_name != curr_conn:
                if conn_count != 0:
                    features = get_features(conn_pkts, curr_conn,limit=0)
                    if features:
                        # print(features)
                        full_conn_name = curr_conn
                        print(full_conn_name)
                        feats[full_conn_name] = features
                conn_pkts = [pkt]
                curr_conn = conn_name
                conn_count += 1
            else:
                conn_pkts.append(pkt)    
    
    features_host = extract_features_by_conn(file_path,gw)
    features_150_df = pd.DataFrame(list(feats.items()), columns=['conn', '150_features'])
    features_150_expanded = features_150_df['150_features'].apply(pd.Series)
    features_150_expanded.columns=Features_names
    features_150_final = pd.concat([features_150_df['conn'], features_150_expanded], axis=1)

    concatenated_features = pd.merge(features_host,features_150_final, on='conn', how='inner')
    concatenated_features['number']=number
    features_list.append(concatenated_features)
    
final_features=pd.concat(features_list, axis=0, ignore_index=True)
final_features.to_csv('features_'+suffix+'gw.csv', index=False)

    

