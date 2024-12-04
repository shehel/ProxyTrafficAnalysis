import os

print("Enter the suffix number added to filename:")
number = int(input())
suffix = input().strip().replace('\n', '')
suffix = '_'+suffix
os.rename('conn.log', 'conn_'+str(number)+suffix+'.log')
os.rename('dns.log', 'dns_'+str(number)+suffix+'.log')
os.rename('http.log', 'http_'+str(number)+suffix+'.log')
os.rename('dhcp.log', 'dhcp_'+str(number)+suffix+'.log')
os.rename('files.log', 'files_'+str(number)+suffix+'.log')
os.rename('ntp.log', 'ntp_'+str(number)+suffix+'.log')
os.rename('packet_filter.log', 'packet_filter_'+str(number)+suffix+'.log')
os.rename('ssl.log', 'ssl_'+str(number)+suffix+'.log')
os.rename('x509.log', 'x509_'+str(number)+suffix+'.log')

print("Rename completed")
