#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 15:05:12 2024

@author: mounarabhi
"""
from extract_features import get_features
from host_features_limited import extract_features_by_conn
from rtt_tls_feature import get_rtt_feature
import csv
import pandas as pd
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings("ignore")

class FeatureExtractor:
    def __init__(self):
        self.Features_names = [
            "max_in", "max_out", "max_total", "avg_in", "avg_out", "avg_total",
            "std_in", "std_out", "std_total", "75th_percentile_in", "75th_percentile_out", "75th_percentile_total",
            "25th_percentile_in_time", "50th_percentile_in_time", "75th_percentile_in_time", "100th_percentile_in_time",
            "25th_percentile_out_time", "50th_percentile_out_time", "75th_percentile_out_time", "100th_percentile_out_time",
            "25th_percentile_total_time", "50th_percentile_total_time", "75th_percentile_total_time", "100th_percentile_total_time",
            "nb_pkts_in", "nb_pkts_out", "nb_pkts_total",
            "nb_pkts_in_f30", "nb_pkts_out_f30", "nb_pkts_in_l30", "nb_pkts_out_l30",
            "std_pkt_conc_out20", "avg_pkt_conc_out20", "avg_per_sec", "std_per_sec", "avg_order_in",
            "avg_order_out", "std_order_in", "std_order_out", "medconc", "med_per_sec", "min_per_sec",
            "max_per_sec", "maxconc", "perc_in", "perc_out", "sum_altconc", "sum_alt_per_sec",
            "sum_number_pkts", "sum_intertimestats"
        ]
        self.Features_names.extend([f"altconc_{i+1}" for i in range(20)])
        self.Features_names.extend([f"alt_per_sec_{i+1}" for i in range(20)])
        self.Features_names.extend([f"conc_{i+1}" for i in range(60)])

    def process_single_file(self, file_path: str, file_type: str, pkt_limit: int) -> Dict:
        """Process a single CSV file and extract features"""
        try:
            features = {}
            with open(file_path, 'r') as f:
                all_pkts = list(csv.reader(f, delimiter=','))
                curr_conn = ''
                conn_pkts = []

                for idx, pkt in enumerate(all_pkts):
                    if idx == 0:
                        continue

                    conn_name = pkt[0]
                    if conn_name != curr_conn:
                        if conn_pkts and len(conn_pkts) >= pkt_limit:
                            conn_features = get_features(conn_pkts[:pkt_limit], curr_conn, limit=0)
                            if conn_features:
                                features[curr_conn] = conn_features
                        conn_pkts = [pkt]
                        curr_conn = conn_name
                    else:
                        conn_pkts.append(pkt)

                # Process final connection
                if conn_pkts and len(conn_pkts) >= pkt_limit:
                    conn_features = get_features(conn_pkts[:pkt_limit], curr_conn, limit=0)
                    if conn_features:
                        features[curr_conn] = conn_features

            # Extract additional features
            features_host = extract_features_by_conn(file_path, gw=False)
            rtt_features = get_rtt_feature(os.path.dirname(file_path), file_type)

            if 'conn' in features_host.columns:
                features_k_df = pd.DataFrame(list(features.items()), columns=['conn', 'k_features'])
                features_k_expanded = features_k_df['k_features'].apply(pd.Series)
                features_k_expanded.columns = self.Features_names
                features_k_final = pd.concat([features_k_df['conn'], features_k_expanded], axis=1)

                merged_df = pd.merge(features_host, features_k_final, on='conn', how='inner')
                concatenated_features = pd.merge(merged_df, rtt_features, on='conn', how='inner')
                concatenated_features['file_path'] = file_path
                concatenated_features['type'] = file_type

                return concatenated_features

            return None

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None

    def process_csv_files(self, root_dir: str, pkt_limit: int = 50) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Process all CSV files in directory"""
        csv_files = []
        for path in Path(root_dir).rglob('*.csv'):
            if path.name == 'background_conn_labeled.csv':
                csv_files.append((str(path), 'background'))
            elif path.name == 'relayed_conn_labeled.csv':
                csv_files.append((str(path), 'relayed'))

        all_features = []
        for file_path, file_type in csv_files:
            print(f"Processing: {file_path}")
            features = self.process_single_file(file_path, file_type, pkt_limit)
            if features is not None:
                all_features.append(features)

        if not all_features:
            return pd.DataFrame(), pd.DataFrame()

        # Combine all features
        combined_features = pd.concat(all_features, ignore_index=True)

        # Create features DataFrame
        features_df = combined_features[self.Features_names].copy()
        features_df['label'] = (combined_features['type'] == 'relayed').astype(int)

        # Create metadata DataFrame
        metadata_df = pd.DataFrame({
            'connection_id': combined_features['conn'],
            'type': combined_features['type'],
            'provider': combined_features['App name'],
            'file_path': combined_features['file_path'],
            'original_conn_id': combined_features['conn'],
            'timestamp': pd.Timestamp.now(),
            'is_relayed': combined_features['type'] == 'relayed',
            'data_source': combined_features['file_path'].apply(lambda x: Path(x).parent.name),
            'analysis_date': pd.Timestamp.now().date()
        })

        return features_df, metadata_df

def main():
    import sys
    
    # Get input directory from command line or use default
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        if not str(input_path).startswith('data/processed/'):
            print("\nError: Input path must start with 'data/processed/'")
            sys.exit(1)
    else:
        print("\nError: Please provide input path (e.g., data/processed/dir1/train)")
        sys.exit(1)

    # Setup paths
    relative_path = Path(str(input_path).replace('data/processed/', ''))
    input_dir = Path('data/processed') / relative_path
    output_dir = Path('data/feats_ours') / relative_path

    # Verify input directory exists
    if not input_dir.exists():
        print(f"\nError: Input directory not found: {input_dir}")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize feature extractor and process files
    extractor = FeatureExtractor()
    print(f"\nProcessing files from: {input_dir}")
    print(f"Saving results to: {output_dir}")
    features_df, metadata_df = extractor.process_csv_files(str(input_dir))

    # Print summary statistics
    total_connections = len(features_df)
    if total_connections == 0:
        print("\nNo connections found in the input directory!")
        sys.exit(1)

    background_count = sum(features_df['label'] == 0)
    relayed_count = sum(features_df['label'] == 1)

    print("\nNetwork Traffic Analysis Summary")
    print("================================")
    print(f"Input Directory: {input_dir}")
    print(f"Output Directory: {output_dir}")
    print(f"\nTotal Connections Analyzed: {total_connections:,}")
    print(f"Background Connections: {background_count:,} ({background_count/total_connections*100:.1f}%)")
    print(f"Relayed Connections: {relayed_count:,} ({relayed_count/total_connections*100:.1f}%)")

    print("\nData Sources:", len(metadata_df['data_source'].unique()))
    print("Unique Providers:", len(metadata_df['provider'].unique()))

    print("\nTop 5 Providers by Connection Count:")
    print(metadata_df['provider'].value_counts().head().to_string())

    print("\nConnections by Data Source:")
    print(metadata_df['data_source'].value_counts().to_string())

    print("\nFeature DataFrame Shape:", features_df.shape)
    print("Metadata DataFrame Shape:", metadata_df.shape)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    features_file = output_dir / "features.csv"
    metadata_file = output_dir / "metadata.csv"

    features_df.to_csv(features_file, index=False)
    metadata_df.to_csv(metadata_file, index=False)

    print("\nResults saved to:")
    print(f"- {features_file}")
    print(f"- {metadata_file}")

    # Save feature names reference
    feature_ref_file = output_dir / "feature_reference.txt"
    with open(feature_ref_file, 'w') as f:
        f.write("Feature Names Description\n")
        f.write("=======================\n\n")
        for i, feature in enumerate(extractor.Features_names):
            f.write(f"{i+1}. {feature}\n")
        f.write(f"\n{len(extractor.Features_names)+1}. label (0=background, 1=relayed)")

    print(f"- {feature_ref_file}")

if __name__ == "__main__":
    main()