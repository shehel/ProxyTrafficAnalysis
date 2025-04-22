# Analysis Folder Documentation

This folder contains scripts and supporting files that process, analyze, and visualize network traffic data collected from proxy, gateway, and relayed connection logs, as well as DNS logs. Below is a one-sentence description of each file:

- **Ecosystem_plots.py**: Computes and plots ecosystem-level metrics—such as connection durations, traffic volumes, and simultaneous connection counts—from gateway and relayed connection logs.
- **vt_plots.py**: Reads VirusTotal category logs for relayed connection domains, computes a cumulative distribution function (CDF) for community scores, and visualizes the results.
- **vt_analysis.py**: Processes domains from a CSV file by using the VirusTotal API to identify suspicious domains, logging their categories, combined scores, and threat details.
- **traffic_sum.py**: Aggregates packet length data across relayed, background, and gateway connection logs to compute the overall traffic volume.
- **suspicious_domains3.txt**: Contains a list of suspicious domains with their associated categories, combined scores, and identified threat details (version 3).
- **suspicious_domains.txt**: Lists the initially identified suspicious domains along with their category information and threat details.
- **server_count_relayed.py**: Counts the occurrences of server names in relayed connection data (grouped by connection) to summarize server usage statistics.
- **select_relayed_domains.py**: Filters and selects accessible domains from a larger set by checking their reachability and excluding domains already flagged as suspicious.
- **relayed_conn.py**: Processes relayed connection logs to compute connection durations, volumes, and server statistics, and then generates visualizations (e.g., CDF plots).
- **relayed_conn_categories3.txt**: Provides categorization and combined-score information for domains seen in relayed connections (version 3).
- **relayed_conn_categories.txt**: Documents the categorization details and combined scores of domains identified in relayed connection logs.
- **relayed_conn_analysis.py**: Aggregates and analyzes relayed connection data to extract domain occurrence counts and highlights the top repeated domains.
- **gw_count.py**: Analyzes gateway connection logs to determine clusters of simultaneous connection starts and generates a CDF plot based on these clusters.
- **GW_analysis.py**: Performs an in-depth analysis of gateway connection behavior—including simultaneous gateway openings, connection durations, and duplicate IP occurrences—with several visualizations.
- **get_category.py**: Retrieves domain categorization and threat details via the VirusTotal API, appending suspicious domain findings to log files.
- **filtered_domains.txt**: Contains a list of domains that have been filtered from the selected domain sample due to suspicious characteristics.
- **filter_relayed_df.py**: Filters and deduplicates relayed connection logs based on a predefined list of domains and saves the resulting dataset as a CSV.
- **dns_rejections.csv**: Stores DNS query logs with rejected responses (indicated by specific response codes) for downstream DNS analysis.
- **dns_rejection.py**: Processes DNS log files to extract, quantify, and plot rejected DNS queries, comparing total requests to rejection counts and rcode distributions.
- **dns_analysis.py**: Integrates DNS log analysis with proxy and normal connection data to identify domains missing from DNS logs (suggesting relayed domains) and visualizes cumulative traffic volumes.

## Overall Workflow

These files work together to form a complete analysis pipeline for network traffic:
- **Data Ingestion and Preprocessing**: Scripts like `filter_relayed_df.py`, `server_count_relayed.py`, and `dns_analysis.py` read various CSV and log files, filter and deduplicate connection data, and extract key metrics.
- **Domain Analysis & Threat Detection**: Files such as `vt_analysis.py`, `vt_plots.py`, and `get_category.py` integrate with the VirusTotal API to provide threat assessments for domains encountered during the network traffic analysis.
- **Traffic and Connection Profiling**: Scripts including `Ecosystem_plots.py`, `relayed_conn.py`, `gw_count.py`, and `GW_analysis.py` compute statistics like connection duration, traffic volume, and simultaneous connection counts, subsequently visualizing this information.
- **DNS and Rejection Analysis**: `dns_rejection.py` and `dns_analysis.py` analyze DNS logs to correlate domain queries with network connections, highlighting discrepancies that may indicate relayed traffic.
- **Domain Filtering and Selection**: Supporting files (`select_relayed_domains.py` and `filtered_domains.txt`) ensure that only relevant and accessible domains are analyzed, improving overall analysis accuracy.

Together, these components provide a comprehensive view of network traffic behavior, helping to identify suspicious activity and characterize various aspects of proxy and gateway communications.