#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  4 10:13:04 2024

@author: mounarabhi
"""
import pandas as pd
import argparse
import os

def enter_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder_path', metavar='folder with files', help='input the folder path with '
                                    'csv files, output files will also be saved there', required=True)
    args = parser.parse_args()
    return args

def main():
    args = enter_cmd_args()
    folder_path = str(args.folder_path)


    #nrml_file_path='./data/processed/mixed_'+str(i)+'_'+suffix+'/normal_conn_'+str(i)+'_'+suffix+'.csv'
    nrml_file_path=f'{folder_path}/normal_conn.csv'
    tshark_file_path=f'{folder_path}/tshark_output.csv'

    print(nrml_file_path)
    print(tshark_file_path)
    nrml_conn=pd.read_csv(nrml_file_path)
    traffic_wireshark=pd.read_csv(tshark_file_path)
    print(traffic_wireshark.head())
    #tcp_protcol=['TCP','TLSv1.3','TLSv1.2']
    #tcp_traffic_wireshark = traffic_wireshark[traffic_wireshark['Protocol'].isin(tcp_protcol)]
    unique_combinations = (
        traffic_wireshark
        .groupby(['src_ip', 'src_port', 'dst_ip', 'dst_port'])['App name']
        .apply(lambda x: ', '.join(set(x)))
        .reset_index()
    )


    nrml_conn_with_app_name = nrml_conn.merge(
        unique_combinations,
        on=['src_ip', 'src_port', 'dst_ip', 'dst_port'],
        how='left'
    )

    nrml_file_path_labeled=f'{folder_path}/normal_conn_labeled.csv'
    nrml_conn_with_app_name.to_csv(nrml_file_path_labeled,index=False)
    relayed_traffic=nrml_conn_with_app_name[nrml_conn_with_app_name['App name']=='EarnApp']
    background_traffic=nrml_conn_with_app_name[ nrml_conn_with_app_name['App name']!='EarnApp']
    relayed_file_path=f'{folder_path}/relayed_conn_labeled.csv'
    background_file_path=f'{folder_path}/background_conn_labeled.csv'
    relayed_traffic.to_csv(relayed_file_path,index=False)
    background_traffic.to_csv(background_file_path,index=False)




if __name__ == "__main__":
    main()
    