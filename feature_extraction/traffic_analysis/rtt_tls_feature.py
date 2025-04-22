#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 14:59:44 2025

@author: mounarabhi
"""
import dpkt
import os
import socket
import pandas as pd


def is_client_hello(data):
    """Detect ClientHello in TLS handshake."""
    try:
        if len(data) < 43:
            return False
        if data[0] != 0x16:  # Handshake protocol
            return False
        if data[1:3] not in [b'\x03\x00', b'\x03\x01', b'\x03\x02', b'\x03\x03', b'\x03\x04']:
            return False
        if data[5] != 0x01:  # Handshake type: ClientHello
            return False
        return True
    except Exception:
        return False


def is_server_hello(data):
    """Detect ServerHello in TLS handshake."""
    try:
        if len(data) < 43:
            return False
        if data[0] != 0x16:  # Handshake protocol
            return False
        if data[1:3] not in [b'\x03\x00', b'\x03\x01', b'\x03\x02', b'\x03\x03', b'\x03\x04']:
            return False
        if data[5] != 0x02:  # Handshake type: ServerHello
            return False
        return True
    except Exception:
        return False

def get_rtt_feature(folder_name, prefix):

    conn_file = os.path.join(folder_name, f"{prefix}_conn_labeled.csv")
    conn_df = pd.read_csv(conn_file)
    pairs = set(zip(conn_df['src_ip'], conn_df['dst_ip']))  # Only these pairs will be considered

    # Storage for packets
    syn_packets = []
    server_hello_packets = []

    # Process PCAP file
    base_pcap = "../ProxyData/local_pcaps"
    last_part = os.path.basename(folder_name)
    pcap_file = os.path.join(base_pcap, f"{last_part}.pcap")

    with open(pcap_file, 'rb') as f:
        pcap = dpkt.pcap.Reader(f)
        for timestamp, buf in pcap:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
                ip = eth.data
                if not isinstance(ip, dpkt.ip.IP):
                    continue

                tcp = ip.data
                if not isinstance(tcp, dpkt.tcp.TCP):
                    continue

                src_ip = socket.inet_ntoa(ip.src)
                dst_ip = socket.inet_ntoa(ip.dst)

                # Check if the packet belongs to the specified pairs
                if (src_ip, dst_ip) not in pairs and (dst_ip, src_ip) not in pairs:
                    continue  # Skip packets not related to the connections in the CSV

                # Check for SYN flag
                if tcp.flags & 0x02:  # SYN
                    syn_packets.append({
                        'timestamp': timestamp,
                        'src_ip': src_ip,
                        'dst_ip': dst_ip,
                        'src_port': tcp.sport,
                        'dst_port': tcp.dport
                    })

                # Check for TLS ServerHello
                if len(tcp.data) > 0 and is_server_hello(tcp.data):
                    server_hello_packets.append({
                        'timestamp': timestamp,
                        'src_ip': src_ip,
                        'dst_ip': dst_ip,
                        'src_port': tcp.sport,
                        'dst_port': tcp.dport
                    })
            except Exception as e:
                print(f"Error processing packet: {e}")
                continue

    # Calculate RTTs
    rtt_data = []
    for syn in syn_packets:
        matching_server_hello = [
            hello for hello in server_hello_packets
            if (hello['src_ip'] == syn['dst_ip'] and
                hello['dst_ip'] == syn['src_ip'] and
                hello['src_port'] == syn['dst_port'] and
                hello['dst_port'] == syn['src_port'] and
                hello['timestamp'] > syn['timestamp'])
        ]

        if matching_server_hello:
            server_hello = min(matching_server_hello, key=lambda x: x['timestamp'])
            rtt = server_hello['timestamp'] - syn['timestamp']
            rtt_data.append({
                'src_ip': syn['src_ip'],
                'dst_ip': syn['dst_ip'],
                'src_port': syn['src_port'],
                'dst_port': syn['dst_port'],
                'rtt': rtt,
                'syn_time': syn['timestamp'],
                'server_hello_time': server_hello['timestamp']
            })

    # Create DataFrame and save results
    df_rtt = pd.DataFrame(rtt_data)
    df_rtt = pd.merge(
        df_rtt,
        conn_df[['src_ip', 'dst_ip', 'src_port', 'dst_port', 'conn']],
        on=['src_ip', 'dst_ip', 'src_port', 'dst_port'],
        how='left'
    )
    df_rtt = df_rtt.groupby(['src_ip', 'dst_ip', 'src_port', 'dst_port']).agg({
    'rtt': 'first' , # Example: Calculate the mean RTT for each connection
    'conn': 'first'
}).reset_index()
    df_rtt=df_rtt.drop(columns=['src_ip'])
    df_rtt=df_rtt.drop(columns=['dst_ip'])
    df_rtt=df_rtt.drop(columns=['src_port'])
    df_rtt=df_rtt.drop(columns=['dst_port'])

    return df_rtt

