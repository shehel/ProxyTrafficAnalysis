#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 13:56:53 2024

@author: mounarabhi
"""
import json

import pandas as pd
import re
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')  

def filter_internal_apis(df, column_name):
    general_api_pattern = (
        r'(googleapis|gstatic|googleusercontent)\.'  # common API-related subdomains
    )
    
    def is_internal_api(domain):
        if domain and isinstance(domain, str):
            return re.search(general_api_pattern, domain) is not None
        return False    
    filtered_df = df[~df[column_name].apply(is_internal_api)]
    
    return filtered_df
suffixes=["low"]
for j in range(25,26):

  for suffix in suffixes:
    print(j,suffix)
    dns_log_path = "/Users/mounarabhi/Library/CloudStorage/OneDrive-HamadbinKhalifaUniversity/Extracted_traffic_mouna/dns/dns_"+str(j)+"_"+suffix+".log"
    nrml_connection=pd.read_csv("/Users/mounarabhi/Library/CloudStorage/OneDrive-HamadbinKhalifaUniversity/Extracted_traffic_mouna/normal_conn_"+str(j)+"_"+suffix+".csv")
    proxy_connection=pd.read_csv("/Users/mounarabhi/Library/CloudStorage/OneDrive-HamadbinKhalifaUniversity/Extracted_traffic_mouna/proxy_conn_"+str(j)+"_"+suffix+".csv")
    alexa_list_path = '/Users/mounarabhi/Library/CloudStorage/OneDrive-HamadbinKhalifaUniversity/Hao traffic/Alexa_list'
    proxy_conn_out=proxy_connection[(proxy_connection['src_ip'] == '10.0.2.16')|( proxy_connection['src_ip'] == '10.0.2.15')]
    proxy_conn_in=proxy_connection[(proxy_connection['dst_ip'] == '10.0.2.16')|( proxy_connection['dst_ip'] == '10.0.2.15')]
    queries = []
    
    # Open the dns.log file and parse each line as JSON
    with open(dns_log_path, 'r') as file:
        for line in file:
            # Convert the JSON string in each line to a dictionary
            try:
                data = json.loads(line.strip())
                # Append the query to the list if it exists
                if "query" in data:
                    queries.append(data["query"])
            except json.JSONDecodeError:
                print("Error decoding JSON for line:", line)
                continue
    
    # Convert the list of queries to a DataFrame for further analysis
    queries_df = pd.DataFrame(queries, columns=["query"])
    #queries_df_f=filter_internal_apis(queries_df, 'query')
    # Get unique domains requested
    unique_domains_dns = queries_df["query"].unique()
    
    
    #filtered_nrml_conn=filter_internal_apis(nrml_connection, 'server_name')
    filtered_nrml_conn=nrml_connection
    all_nrml_traffic=filtered_nrml_conn[(filtered_nrml_conn['ts_relative'] >= proxy_connection.ts_relative.iloc[0]) & (filtered_nrml_conn['ts_relative'] <= proxy_connection.ts_relative.iloc[-1])]
    
    server_names=all_nrml_traffic.server_name.unique()
    unique_domains_set = set(unique_domains_dns)
    server_names_set = set(server_names)
    
    missing_from_dns = server_names_set - unique_domains_set
    missing_from_dns_list = list(missing_from_dns)
    print("Domains missing from DNS logs (potential relayed domains):", missing_from_dns_list)
    
    
    
    relayed_traffic = all_nrml_traffic[all_nrml_traffic['server_name'].isin(missing_from_dns_list)]
    relayed_conn_in=relayed_traffic[(relayed_traffic['dst_ip'] == '10.0.2.16')| (relayed_traffic['dst_ip'] == '10.0.2.15')]
    relayed_conn_out=relayed_traffic[(relayed_traffic['src_ip'] == '10.0.2.16')| (relayed_traffic['src_ip'] == '10.0.2.15')]
    
    interval_size = 1  # Adjust this value if needed for larger intervals
    unique_proxy_conns = proxy_connection['conn'].unique()
    
    proxy_conn_in['time_interval'] = (proxy_conn_in['ts_relative'] // interval_size).astype(int)
    proxy_conn_out['time_interval'] = (proxy_conn_out['ts_relative'] // interval_size).astype(int)
    relayed_conn_in['time_interval'] = (relayed_conn_in['ts_relative'] // interval_size).astype(int)
    relayed_conn_out['time_interval'] = (relayed_conn_out['ts_relative'] // interval_size).astype(int)
     
     # Group by time intervals and sum the traffic volumes
    volume_proxy_conn_in = proxy_conn_in.groupby('time_interval')['pkt_len'].sum().reset_index()
    volume_proxy_conn_out = proxy_conn_out.groupby('time_interval')['pkt_len'].sum().reset_index()
    volume_relayed_conn_in = relayed_conn_in.groupby('time_interval')['pkt_len'].sum().reset_index()
    volume_relayed_conn_out = relayed_conn_out.groupby('time_interval')['pkt_len'].sum().reset_index()
     
     # Convert packet lengths to MB
    volume_proxy_conn_in['traffic_volume'] = volume_proxy_conn_in['pkt_len'] / 1024 / 1024
    volume_proxy_conn_out['traffic_volume'] = volume_proxy_conn_out['pkt_len'] / 1024 / 1024
    volume_relayed_conn_in['traffic_volume'] = volume_relayed_conn_in['pkt_len'] / 1024 / 1024
    volume_relayed_conn_out['traffic_volume'] = volume_relayed_conn_out['pkt_len'] / 1024 / 1024
    
    volume_proxy_conn_in['cumulative_traffic'] = volume_proxy_conn_in['traffic_volume'].cumsum()
    volume_proxy_conn_out['cumulative_traffic'] = volume_proxy_conn_out['traffic_volume'].cumsum()
    volume_relayed_conn_in['cumulative_traffic'] = volume_relayed_conn_in['traffic_volume'].cumsum()
    volume_relayed_conn_out['cumulative_traffic'] = volume_relayed_conn_out['traffic_volume'].cumsum()
    
    plt.plot(volume_proxy_conn_in['time_interval'], volume_proxy_conn_in['cumulative_traffic'], 'b--', label="Proxy_in")
    plt.plot(volume_proxy_conn_out['time_interval'], volume_proxy_conn_out['cumulative_traffic'],'r--',label="Proxy_out")
    plt.plot(volume_relayed_conn_in['time_interval'], volume_relayed_conn_in['cumulative_traffic'], 'y.', label="nrml-in")
    plt.plot(volume_relayed_conn_out['time_interval'], volume_relayed_conn_out['cumulative_traffic'], 'g.', label="nrml-out")
    plt.xlabel('Time (s)')
    plt.ylabel('Traffic Volume (MB)')
    plt.title('Instance '+str(j)+'_Cumulative Traffic Volume Over Time')
    plt.legend()
    plt.show()
    pr=True
    
    for i in range(len(unique_proxy_conns)):
        proxy_conn_i = proxy_connection[proxy_connection['conn'] == unique_proxy_conns[i]]
        proxy_conn_i_in = proxy_conn_in[proxy_conn_in['conn'] == unique_proxy_conns[i]]
        proxy_conn_i_out = proxy_conn_out[proxy_conn_out['conn'] == unique_proxy_conns[i]]
    
        # Filter relayed connections within the proxy time range
        relayed_conn_in_i = relayed_conn_in[(relayed_conn_in['ts_relative'] >= proxy_conn_i.ts_relative.iloc[0]) &
                                            (relayed_conn_in['ts_relative'] <= proxy_conn_i.ts_relative.iloc[-1])]
        grouped_relayed_in_i=relayed_conn_in_i.groupby("server_name")
        relayed_conn_out_i = relayed_conn_out[(relayed_conn_out['ts_relative'] >= proxy_conn_i.ts_relative.iloc[0]) &
                                              (relayed_conn_out['ts_relative'] <= proxy_conn_i.ts_relative.iloc[-1])]
        proxy_conn_i_in['time_interval'] = (proxy_conn_i_in['ts_relative'] // interval_size).astype(int)
        proxy_conn_i_out['time_interval'] = (proxy_conn_i_out['ts_relative'] // interval_size).astype(int)
        relayed_conn_in_i['time_interval'] = (relayed_conn_in_i['ts_relative'] // interval_size).astype(int)
        relayed_conn_out_i['time_interval'] = (relayed_conn_out_i['ts_relative'] // interval_size).astype(int)
        
        # Group by time intervals and sum the traffic volumes
        volume_proxy_conn_i_in = proxy_conn_i_in.groupby('time_interval')['pkt_len'].sum().reset_index()
        volume_proxy_conn_i_out = proxy_conn_i_out.groupby('time_interval')['pkt_len'].sum().reset_index()
        volume_relayed_conn_i_in = relayed_conn_in_i.groupby('time_interval')['pkt_len'].sum().reset_index()
        volume_relayed_conn_i_out = relayed_conn_out_i.groupby('time_interval')['pkt_len'].sum().reset_index()
        
        # Convert packet lengths to MB
        volume_proxy_conn_i_in['traffic_volume'] = volume_proxy_conn_i_in['pkt_len'] / 1024 / 1024
        volume_proxy_conn_i_out['traffic_volume'] = volume_proxy_conn_i_out['pkt_len'] / 1024 / 1024
        volume_relayed_conn_i_in['traffic_volume'] = volume_relayed_conn_i_in['pkt_len'] / 1024 / 1024
        volume_relayed_conn_i_out['traffic_volume'] = volume_relayed_conn_i_out['pkt_len'] / 1024 / 1024
        
        # Calculate cumulative traffic over time for each dataset
        volume_proxy_conn_i_in['cumulative_traffic'] = volume_proxy_conn_i_in['traffic_volume'].cumsum()
        volume_proxy_conn_i_out['cumulative_traffic'] = volume_proxy_conn_i_out['traffic_volume'].cumsum()
        volume_relayed_conn_i_in['cumulative_traffic'] = volume_relayed_conn_i_in['traffic_volume'].cumsum()
        volume_relayed_conn_i_out['cumulative_traffic'] = volume_relayed_conn_i_out['traffic_volume'].cumsum()
        """
        num_colors = len(grouped_relayed_in_i)  # Number of unique server_name_in groups
        colors = plt.cm.tab20(np.linspace(0, 1, num_colors))  # Generate unique colors
        for k,(server_name_in, group_in) in enumerate(grouped_relayed_in_i):
            # Sort by time to calculate cumulative packet length
            group_in = group_in.sort_values(by='time_interval')
            
            # Calculate cumulative packet length
            group_in['cumulative_traffic'] = group_in['pkt_len'].cumsum()/ 1024 / 1024
            # Calculate the total traffic for this server
            total_traffic = group_in['pkt_len'].sum() / 1024 / 1024  # Convert to MB
            if(pr):
                print(f"Total Traffic for {server_name_in}: {total_traffic:.3f} MB")
                print(group_in.src_ip.unique())
            # Plot cumulative traffic over time
            plt.plot(group_in['time_interval'], group_in['cumulative_traffic'], 'o', color=colors[k], label=server_name_in)
        pr=False
        plt.plot(volume_proxy_conn_i_out['time_interval'], volume_proxy_conn_i_out['cumulative_traffic'],'r--',label="Proxy_out")
    
        plt.xlabel('Time Interval')
        plt.ylabel('Cumulative Traffic (pkt_len)')
        plt.title('Instance '+str(j)+"_conn "+str(i+1)+'_Cumulative Traffic Volume Over Time')
        plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    
        plt.show()
        """
        """
        # Plot cumulative traffic volume over time
        plt.plot(volume_proxy_conn_i_in['time_interval'], volume_proxy_conn_i_in['cumulative_traffic'], 'b--', label="Proxy_in")
        plt.plot(volume_proxy_conn_i_out['time_interval'], volume_proxy_conn_i_out['cumulative_traffic'],'r--',label="Proxy_out")
        plt.plot(volume_relayed_conn_i_in['time_interval'], volume_relayed_conn_i_in['cumulative_traffic'], 'y.', label="nrml-in")
        plt.plot(volume_relayed_conn_i_out['time_interval'], volume_relayed_conn_i_out['cumulative_traffic'], 'g.', label="nrml-out")
        plt.xlabel('Time (s)')
        plt.ylabel('Traffic Volume (MB)')
        plt.title('Instance '+str(j)+"_conn "+str(i+1)+'_Cumulative Traffic Volume Over Time')
        plt.legend()
        plt.show()
        
        # Print the total traffic volumes for debugging
        total_traffic_proxy_conn_in = volume_proxy_conn_i_in['traffic_volume'].sum()
        total_traffic_proxy_conn_out = volume_proxy_conn_i_out['traffic_volume'].sum()
        total_traffic_relayed_conn_in = volume_relayed_conn_i_in['traffic_volume'].sum()
        total_traffic_relayed_conn_out = volume_relayed_conn_i_out['traffic_volume'].sum()
    
        print(f"Total Traffic for proxy_conn_{i+1}_in: {total_traffic_proxy_conn_in:.3f} MB")
        print(f"Total Traffic for proxy_conn_{i+1}_out: {total_traffic_proxy_conn_out:.3f} MB")
        print(f"Total Traffic for nrml_in_{i+1}_in: {total_traffic_relayed_conn_in:.3f} MB")
        print(f"Total Traffic for nrml_out_{i+1}_out: {total_traffic_relayed_conn_out: .3f} MB")
    
    
    
        start_1=proxy_conn_out[proxy_conn_out['conn'] == unique_proxy_conns[i]].ts_relative.iloc[0]
        end_1=proxy_conn_out[proxy_conn_out['conn'] == unique_proxy_conns[i]].ts_relative.iloc[-1]
        
        print(f"start/end proxy conn{i+1}: {start_1:.3f},{end_1:.3f}")
        """
    
    sum_relayed_in=relayed_conn_in.pkt_len.sum()/1024/1024
    sum_relayed_out=relayed_conn_out.pkt_len.sum()/1024/1024
    sum_proxy_in=proxy_conn_in.pkt_len.sum()/1024/1024
    sum_proxy_out=proxy_conn_out.pkt_len.sum()/1024/1024
    print(f"Sum traffic proxy in (MB): {sum_proxy_in:.3f}",)
    print(f"Sum traffic proxy out (MB): {sum_proxy_out:.3f}")
    print(f"Sum traffic nrml in (MB): {sum_relayed_in: .3f}")
    print(f"Sum traffic nrml out (MB): {sum_relayed_out: .3f}")