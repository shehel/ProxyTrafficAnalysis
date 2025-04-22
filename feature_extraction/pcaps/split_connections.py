import json
import argparse
import dpkt
import binascii
import os
import csv

def raw_ip_to_string(ip_addr):
    ip_hex = binascii.hexlify(ip_addr)
    str_list = []
    for i in range(4):
        hex_octet_string = ip_hex[i * 2:i * 2 + 2].decode('utf-8')
        dec_octet_int = int(hex_octet_string, 16)
        str_list.append(str(dec_octet_int))
    readable_ip = ".".join(str_list)
    return readable_ip

# Add global variable
device_ip = None

def convert_to_conn_str(src_ip, src_prt, dst_ip, dst_prt):
    global device_ip
    if src_ip == device_ip:
        conn_str = f'({src_ip}, {src_prt}, {dst_ip}, {dst_prt})'
    else:
        conn_str = f'({dst_ip}, {dst_prt}, {src_ip}, {src_prt})'
    return conn_str

def get_noisy_domains():
    file_path = './noise_domains.txt'
    with open(file_path, 'r') as f:
        domain_list = f.readlines()
    domains = [domain.strip() for domain in domain_list]
    return domains

def enter_cmd_args():
    parser = argparse.ArgumentParser(description="Process log files from a given folder.")
    parser.add_argument('--folder', metavar='<folder name>', help='The folder containing the log files', required=True)
    args = parser.parse_args()
    return args

def load_conn(conn_file):
    with open(conn_file, 'r') as f:
        conn_list = json.load(f)
    return conn_list

def get_conn_name(ssl_tp, conn_list):
    conn_str = convert_to_conn_str(ssl_tp[1], ssl_tp[2], ssl_tp[3], ssl_tp[4])
    return conn_list.get(conn_str, False)

import dpkt

def is_in_range(prt):
    if prt == 443: # TLS
        return True
    
    if prt > 50000 and prt <= 55000: # File transfer
        return True
    
    if prt == 22: # SSH
        return True

def parse_pcap(pcap_file, conn_list):
    global device_ip
    proxy_conn_pkt_dict = {}
    normal_conn_pkt_dict = {}
    curr_pkt = 0
    first_ts = -1

    try:
        with open(pcap_file, 'rb') as f:
            pcaps = dpkt.pcap.Reader(f)
            for ts, pkt in pcaps:
                curr_pkt += 1
                if curr_pkt == 1:
                    first_ts = ts  # Capture the timestamp of the first packet

                try:
                    eth = dpkt.ethernet. Ethernet(pkt)
                except dpkt.dpkt.NeedData:
                    print(f"Malformed Ethernet frame at Packet #{curr_pkt}")
                    continue

                # Only process IP packets
                if eth.type != dpkt.ethernet.ETH_TYPE_IP:
                    continue

                ip = eth.data
                try:
                    # Only process TCP packets
                    if ip.p != dpkt.ip.IP_PROTO_TCP:
                        continue
                except AttributeError:
                    print(f"Bogus IP packet detected at Packet #{curr_pkt}")
                    continue

                # Extract layer-4 (TCP) data
                l4_proto = ip.data
                try:
                    src_prt = int(l4_proto.sport)
                    dst_prt = int(l4_proto.dport)
                except AttributeError:
                    print(f"Missing TCP port information at Packet #{curr_pkt}")
                    continue

                # Extract IP addresses
                src_ip = raw_ip_to_string(ip.src)
                dst_ip = raw_ip_to_string(ip.dst)
                
                # Filter for packets involving port 443 (HTTPS)
                if not is_in_range(src_prt) and not is_in_range(dst_prt):
                    continue

                # Set device_ip from the first HTTPS packet
                if device_ip is None :
                    device_ip = src_ip
                    print(f"Detected device IP: {device_ip}")

                pkt_len = ip.len

                # Prepare SSL record
                ssl_rec = [ts - first_ts, src_ip, src_prt, dst_ip, dst_prt, pkt_len]

                # Identify connection name
                conn = get_conn_name(ssl_rec, conn_list)
                if not conn:
                    continue
                
                # Determine connection type (proxy or normal)
                conn_pkt_dict = proxy_conn_pkt_dict if "proxy" in conn[0] else normal_conn_pkt_dict

                # Append packet details to the respective dictionary
                if conn[0] in conn_pkt_dict:
                    conn_pkt_dict[conn[0]].append(conn + ssl_rec)
                else:
                    conn_pkt_dict[conn[0]] = [conn + ssl_rec]

    except FileNotFoundError:
        print(f"Error: File '{pcap_file}' not found.")
    except dpkt.dpkt.UnpackError as e:
        print(f"Error unpacking pcap file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
 
    return proxy_conn_pkt_dict, normal_conn_pkt_dict

def save_conn_to_csv(proxy_conn, normal_conn, folder):
    fields = ['conn', 'server_name', 'ts_relative', 'src_ip', 'src_port', 'dst_ip', 'dst_port', 'pkt_len']
    proxy_path = os.path.join(folder, 'proxy_conn.csv')
    normal_path = os.path.join(folder, 'normal_conn.csv')

    with open(proxy_path, 'w') as proxy_f:
        writer_pro = csv.writer(proxy_f)
        writer_pro.writerow(fields)
        for key, value in proxy_conn.items():
            writer_pro.writerows(value)

    with open(normal_path, 'w') as normal_f:
        writer_nor = csv.writer(normal_f)
        writer_nor.writerow(fields)
        for key, value in normal_conn.items():
            writer_nor.writerows(value)

def main():
    args = enter_cmd_args()
    folder = args.folder

    if not os.path.isdir(folder):
        print(f"Error: Folder '{folder}' does not exist.")
        return

    conn_file = os.path.join(folder, 'conn_list.json')
    pcap_file = os.path.join(folder, 'mixed.pcap')

    if not os.path.exists(conn_file):
        print(f"Error: File 'conn_list.json' not found in folder '{folder}'.")
        return
    if not os.path.exists(pcap_file):
        print(f"Error: File 'mixed.pcap' not found in folder '{folder}'.")
        return

    conn_list = load_conn(conn_file)
    proxy_conn, normal_conn = parse_pcap(pcap_file, conn_list)
    save_conn_to_csv(proxy_conn, normal_conn, folder)

if __name__ == "__main__":
    main()
