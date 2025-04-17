# Extract traffic type and profile from input file path
traffic_type_profile=$(basename "$1" .pcap)
echo $traffic_type_profile
# Create output directory
output_dir="data/processed/${traffic_type_profile}"
mkdir -p "$output_dir"

# Run zeek and output files to the target directory
cd "$output_dir" && zeek -C -r "../../pcaps/${traffic_type_profile}.pcap" LogAscii::use_json=T
