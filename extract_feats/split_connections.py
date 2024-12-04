import pandas
import json
import argparse
import dpkt
import binascii
import sys
import csv

'''
def raw_mac_to_string(mac_addr):
	mac_hex = binascii.hexlify(mac_addr)
	str_list = list()
	for i in range(6):
		str_list.append(mac_hex[i*2:i*2+2].decode('utf-8'))
		readable_mac = ":".join(str_list)
	return readable_mac
'''

def raw_ip_to_string(ip_addr):
	ip_hex = binascii.hexlify(ip_addr)
	str_list = list()
	for i in range(4):
		hex_octet_string = ip_hex[i*2:i*2+2].decode('utf-8')
		dec_octet_int = int(hex_octet_string,16)
		str_list.append(str(dec_octet_int))
		readable_ip = ".".join(str_list)
	return readable_ip

def convert_to_conn_str(src_ip, src_prt, dst_ip, dst_prt):
	if src_ip == "10.0.2.16" or src_ip == '10.0.2.15':
		conn_str = '('+src_ip+', '+str(src_prt)+', '+dst_ip+', '+str(dst_prt)+')'
	else:
		conn_str = '('+dst_ip+', '+str(dst_prt)+', '+src_ip+', '+str(src_prt)+')'
	return conn_str

def get_noisy_domains():
	file_path = './noise_domains.txt'
	f = open(file_path, 'r')
	domain_list = f.readlines()
	domains = [domain.strip().replace('\n','') for domain in domain_list]
	return domains

def enter_cmd_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--suffix', metavar='<input suffix of filename>', help='the suffix of filename', required=False)
	parser.add_argument('--number', metavar='<input the number of log>', help='the number of log to process', required=True)
	args = parser.parse_args()
	return args

def load_conn(conn_file):
	f = open(conn_file, 'r')
	conn_list = json.load(f)
	return conn_list

def get_conn_name(ssl_tp, conn_list):
	conn_str = convert_to_conn_str(ssl_tp[1], ssl_tp[2], ssl_tp[3], ssl_tp[4])
	try:
		conn_name = conn_list[conn_str]
		#print('conn_name:', conn_name)
	except:
		#print("this packt doesn't belong to a valid connection")
		return False
	return conn_name

def parse_pcap(pcap_file, conn_list):
	proxy_conn_pkt_dict = {}
	normal_conn_pkt_dict = {}
	curr_pkt = 0
	first_ts = -1
	last_ts = -1
	pcaps = dpkt.pcap.Reader(open(pcap_file, 'rb'))
	for ts, pkt in pcaps:
		curr_pkt += 1
		if curr_pkt == 1:
			first_ts = ts
		try:
			eth = dpkt.ethernet.Ethernet(pkt)
		except dpkt.dpkt.NeedData:
			print('Error happened at Packet #:', curr_pkt)
			continue
		if eth.type != dpkt.ethernet.ETH_TYPE_IP:
			continue
		ip = eth.data
		if ip.p != dpkt.ip.IP_PROTO_TCP:
			continue
		else:
			l4_proto = ip.data
			src_prt = int(l4_proto.sport)
			dst_prt = int(l4_proto.dport)
		if src_prt != 443 and dst_prt != 443:
			continue
		src_ip = raw_ip_to_string(ip.src)
		dst_ip = raw_ip_to_string(ip.dst)
		pkt_len = ip.len
		ssl_rec = [ts-first_ts, src_ip, src_prt, dst_ip, dst_prt, pkt_len]
		conn = get_conn_name(ssl_rec, conn_list)
		if not conn:
			continue
		#conn[0]: connecton_name; conn[1]: server_name
		if "proxy" in conn[0]:
			conn_pkt_dict = proxy_conn_pkt_dict
		else:
			conn_pkt_dict = normal_conn_pkt_dict
		#print("Conn:", conn)
		#print("SSL record:", ssl_rec)
		if conn[0] in conn_pkt_dict:
			conn_pkt_dict[conn[0]].append(conn+ssl_rec)
		else:
			conn_pkt_dict[conn[0]] = [conn+ssl_rec]
	return proxy_conn_pkt_dict, normal_conn_pkt_dict
			
def save_conn_to_csv(proxy_conn, normal_conn, suffix, number):
	fields = ['conn', 'server_name', 'ts_relative', 'src_ip', 'src_port', 'dst_ip', 'dst_port', 'pkt_len']
	proxy_path = 'proxy_conn_'+str(number)+suffix+'.csv'
	normal_path = 'normal_conn_'+str(number)+suffix+'.csv'
	proxy_f = open(proxy_path, 'w')
	writer_pro = csv.writer(proxy_f, delimiter=',')
	normal_f = open(normal_path, 'w')
	writer_nor = csv.writer(normal_f, delimiter=',')
	writer_pro.writerow(fields)
	writer_nor.writerow(fields)
	for key, value in proxy_conn.items():
		writer_pro.writerows(value)
	for key, value in normal_conn.items():
		writer_nor.writerows(value)
	proxy_f.close()
	normal_f.close()


def main():
	#parse proxy conn and normal conn from PCAP files
	args = enter_cmd_args()
	suffix = ''
	if args.suffix:
		suffix += '_'+args.suffix
	number = int(args.number)
	conn_file = 'conn_list_'+str(number)+suffix+'.json'
	pcap_file = './mixed_'+str(number)+suffix+'.pcap'
	conn_list = load_conn(conn_file)
	proxy_conn, normal_conn = parse_pcap(pcap_file, conn_list)
	save_conn_to_csv(proxy_conn, normal_conn, suffix, number)

if __name__ == "__main__":
	main()
