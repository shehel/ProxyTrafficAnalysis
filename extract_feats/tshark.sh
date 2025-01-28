#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <pcap_file> <output_dir>"
    exit 1
fi

pcap_file="$1"
output_dir="$2"

if [ ! -f "$pcap_file" ]; then
    echo "Error: File '$pcap_file' not found"
    exit 1
fi

# Ensure output directory exists
mkdir -p "$output_dir"

# Extract traffic type and profile from input file path
traffic_type_profile=$(basename "$pcap_file" .pcap)
output_file="$output_dir/tshark_output.csv"

tshark -X lua_script:./res/pcapdroid.lua -r "$pcap_file" -T fields \
-e _ws.col.Time \
-e pcapdroid.appname \
-e ip.dst \
-e _ws.col.Protocol \
-e frame.len \
-e ip.src \
-e tcp.srcport -e udp.srcport \
-e ip.dst \
-e tcp.dstport -e udp.dstport \
-E header=y \
-E separator=, \
-E quote=n \
-E occurrence=f | \
awk -F',' 'NR==1 {print "Time,App name,Destination,Protocol,Length,src_ip,src_port,dst_ip,dst_port"}
NR>1 {
    if ($7 != "") port=$7;
    else if ($8 != "") port=$8;
    else port="";

    if ($10 != "") dport=$10;
    else if ($11 != "") dport=$11;
    else dport="";

    print $1","$2","$3","$4","$5","$6","port","$9","dport
}' > "$output_file"

echo "Output saved to $output_file"
