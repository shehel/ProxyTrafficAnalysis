import pandas as pd
import json
import argparse
import os

def enter_cmd_args():
    parser = argparse.ArgumentParser(description="Process logs in a given folder.")
    parser.add_argument('--folder', metavar='<folder name>', help='The folder containing log files', required=True)
    args = parser.parse_args()
    return args

def get_noisy_domains():
    file_path = './noise_domains.txt'
    with open(file_path, 'r') as f:
        domain_list = f.readlines()
    domains = [domain.strip() for domain in domain_list]
    return domains

def main():
    args = enter_cmd_args()
    folder_name = args.folder

    # Verify folder existence
    if not os.path.isdir(folder_name):
        print(f"Error: The folder '{folder_name}' does not exist.")
        return

    noisy_domains = get_noisy_domains()
    file_path = os.path.join(folder_name, 'ssl.log')

    # Verify file existence
    if not os.path.exists(file_path):
        print(f"Error: File 'ssl.log' not found in folder '{folder_name}'.")
        return

    with open(file_path, 'r') as f:
        df = pd.read_json(f, lines=True)

    df_dict = df.to_dict('records')
    domain_ip_dict = {}
    conn_dict = {}
    proxy_num = 1
    normal_num = 1

    for i in range(len(df_dict)):
        if not df_dict[i].get('established', False):
            continue
        server_name = df_dict[i].get('server_name', 'NA')
        if pd.isnull(server_name):
            server_name = 'NA'
        if server_name in noisy_domains or 'fls.doubleclick.net' in server_name:
            continue
        ip_src = df_dict[i]['id.orig_h']
        prt_src = df_dict[i]['id.orig_p']
        ip_recv = df_dict[i]['id.resp_h']
        prt_recv = df_dict[i]['id.resp_p']
        conn_tp = f"({ip_src}, {prt_src}, {ip_recv}, {prt_recv})"

        if 'brdtnet.com' in server_name or ('luminatinet.com' in server_name and 'proxyjs' not in server_name):
            conn_dict[conn_tp] = [f'proxy_conn_{proxy_num}', server_name]
            proxy_num += 1
        else:
            conn_dict[conn_tp] = [f'normal_conn_{normal_num}', server_name]
            normal_num += 1

        if server_name in domain_ip_dict:
            if ip_recv not in domain_ip_dict[server_name]:
                domain_ip_dict[server_name].append(ip_recv)
        else:
            domain_ip_dict[server_name] = [ip_recv]

    # Save domain_ip_list and conn_list JSON files in the same folder
    save_path = os.path.join(folder_name, 'domain_ip_list.json')
    conn_path = os.path.join(folder_name, 'conn_list.json')

    with open(save_path, 'w') as save_f:
        save_f.write(json.dumps(domain_ip_dict, indent=4))
    with open(conn_path, 'w') as conn_f:
        conn_f.write(json.dumps(conn_dict, indent=4))

    print(f"Processed logs saved in folder: {folder_name}")

if __name__ == "__main__":
    main()
