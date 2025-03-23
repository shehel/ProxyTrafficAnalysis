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
import numpy as np
import json

warnings.filterwarnings("ignore")

# Define magic numbers for bg 4th pkt len distribution
BG_DST_MEAN = -8.30798020107403
BG_DST_STD = 0.9981827236487635

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

        # Add new instance variables
        self.use_empirical_sampling = True
        self.empirical_packet_lengths = None
        self.background_length_distribution = {
            'mean': BG_DST_MEAN,
            'std': BG_DST_STD
        }
        
        # Load empirical samples
        self.load_empirical_samples()
    
    def load_empirical_samples(self, json_path='packet_lengths.json'):
        """Load empirical packet length samples from JSON file"""
        try:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
                self.empirical_packet_lengths = json_data['empirical_samples']
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load empirical samples: {e}")
            self.use_empirical_sampling = False

    def process_single_file(self, file_path: str, file_type: str, pkt_limit: int) -> Dict:
        """Process a single CSV file and extract features"""
        try:
            features = {}
            with open(file_path, 'r') as f:
                all_pkts = list(csv.reader(f, delimiter=','))
                curr_conn = ''
                conn_pkts = []

                for idx, pkt in enumerate(all_pkts):
                    # If the first row is a header, skip it
                    if idx == 0:
                        continue

                    conn_name = pkt[0]

                    # If we detect a new connection, process the old one first
                    if conn_name != curr_conn:
                        # If we had a previous connection with enough packets
                        if conn_pkts and len(conn_pkts) >= pkt_limit:
                            # Apply the same drop & randomization logic:
                            # 1) If 4th packet is > 1300, drop 4th and 6th
                            if len(conn_pkts) > 3 and int(conn_pkts[3][7]) > 1300:
                                # Remove the packet at index 3
                                conn_pkts.pop(3)
                                # Now check if index 4 still exists
                                if len(conn_pkts) > 4:
                                    conn_pkts.pop(4)

                            # 2) Sample new length for the (new) 4th packet
                            if len(conn_pkts) > 3:
                                if self.use_empirical_sampling and self.empirical_packet_lengths is not None:
                                    new_length = np.random.choice(self.empirical_packet_lengths)
                                else:
                                    # Fall back to normal distribution sampling
                                    new_length = np.random.normal(
                                        loc=self.background_length_distribution['mean'],
                                        scale=self.background_length_distribution['std']
                                    )
                                    new_length = max(1, int(round(new_length)))
                                conn_pkts[3][7] = str(new_length)

                            # Now compute features
                            conn_features = get_features(conn_pkts[:pkt_limit], curr_conn, limit=0)
                            if conn_features:
                                features[curr_conn] = conn_features

                        # Start a new conn_pkts list for the new connection
                        conn_pkts = [pkt]
                        curr_conn = conn_name
                    else:
                        # Same connection, just append
                        conn_pkts.append(pkt)

                # Process final connection
                if conn_pkts and len(conn_pkts) >= pkt_limit:
                    # Same drop & randomization logic as above
                    if len(conn_pkts) > 3 and int(conn_pkts[3][7]) > 1300:
                        conn_pkts.pop(3)
                        if len(conn_pkts) > 4:
                            conn_pkts.pop(4)
                    if len(conn_pkts) > 3:
                        if self.use_empirical_sampling and self.empirical_packet_lengths is not None:
                            new_length = np.random.choice(self.empirical_packet_lengths)
                        else:
                            # Fall back to normal distribution sampling
                            new_length = np.random.normal(
                                loc=self.background_length_distribution['mean'],
                                scale=self.background_length_distribution['std']
                            )
                            new_length = max(1, int(round(new_length)))
                        conn_pkts[3][3] = str(new_length)

                    # Get features and save them
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
    
    # Get input file path from command line
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        if not input_path.exists():
            print(f"\nError: Input file not found: {input_path}")
            sys.exit(1)
        if not input_path.suffix == '.csv':
            print("\nError: Input file must be a CSV file")
            sys.exit(1)
    else:
        print("\nError: Please provide input CSV file path")
        sys.exit(1)

    # Determine file type from filename
    file_type = 'relayed' if 'relayed' in input_path.name else 'background'
    
    # Setup output path in same directory as input
    output_folder_path = Path("content/subset_features_03_18/val")
    output_path = output_folder_path / f"{input_path.parent.name}_{file_type}.csv"

    # Initialize feature extractor and process file
    extractor = FeatureExtractor()
    print(f"\nProcessing file: {input_path}")
    print(f"Saving results to: {output_path}")
    
    # Process single file
    features = extractor.process_single_file(str(input_path), file_type, pkt_limit=20)
    
    if features is None or len(features) == 0:
        print("\nNo features could be extracted from the input file!")
        sys.exit(1)

    # Create features DataFrame
    features_df = features[extractor.Features_names].copy()
    features_df['label'] = (features['type'] == 'relayed').astype(int)

    # Save results
    features_df.to_csv(output_path, index=False)

    print("\nFeature extraction complete")
    print(f"Features shape: {features_df.shape}")
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()