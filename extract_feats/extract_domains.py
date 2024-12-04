import pandas as pd
import json
import argparse

def enter_cmd_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--suffix', metavar='<input suffix of filename>', help='the suffix of filename', required=False)
	parser.add_argument('--number', metavar='<input the number of log>', help='the number of log to process', required=True)
	args = parser.parse_args()
	return args

def get_noisy_domains():
	file_path = './noise_domains.txt'
	f = open(file_path, 'r')
	domain_list = f.readlines()
	domains = [domain.strip().replace('\n','') for domain in domain_list]
	return domains

def main():
	args = enter_cmd_args()
	suffix = ''
	if args.suffix:
		suffix += '_'+args.suffix
	number = int(args.number)
	noisy_domains = get_noisy_domains()
	file_path = 'ssl_'+str(number)+suffix+'.log'
	f = open(file_path, 'r')
	df = pd.read_json(f, lines=True)
	df_dict = df.to_dict('records')
	domain_ip_dict = {}
	conn_dict = {}
	proxy_num = 1
	normal_num = 1
	for i in range(len(df_dict)):
		if df_dict[i]['established'] == False:
			continue
		server_name = df_dict[i]['server_name']
		if not server_name or pd.isnull(server_name):
			#print(df_dict[i])
			server_name = 'NA'
		if server_name in noisy_domains or 'fls.doubleclick.net' in server_name:
			continue
		ip_src = df_dict[i]['id.orig_h']
		prt_src = df_dict[i]['id.orig_p']
		ip_recv = df_dict[i]['id.resp_h']
		prt_recv = df_dict[i]['id.resp_p']
		conn_tp = '('+ip_src+', '+str(prt_src)+', '+ip_recv+', '+str(prt_recv)+')'
		if 'brdtnet.com' in server_name or ('luminatinet.com' in server_name and 'proxyjs' not in server_name):
			conn_dict[conn_tp] = ['proxy_conn_'+str(proxy_num), server_name]
			proxy_num += 1
		else:
			conn_dict[conn_tp] = ['normal_conn_'+str(normal_num), server_name]
			normal_num += 1
		if server_name in domain_ip_dict:
			if ip_recv in domain_ip_dict[server_name]:
				continue
			else:
				domain_ip_dict[server_name].append(ip_recv)
		else:
			domain_ip_dict[server_name] = [ip_recv]
	f.close()
	save_dict = {}
	for key, value in domain_ip_dict.items():
		value_str = ', '.join(value)
		save_dict[key] = value_str
	save_path = 'domain_ip_list_'+str(number)+suffix+'.json'
	conn_path = 'conn_list_'+str(number)+suffix+'.json'
	save_f = open(save_path, 'w')
	conn_f = open(conn_path, 'w')
	save_f.write(json.dumps(save_dict, indent=4))
	conn_f.write(json.dumps(conn_dict, indent=4))
	save_f.close()
	conn_f.close()

if __name__ == "__main__":
	main()
