import argparse
import os
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import pdb
from datetime import datetime

@dataclass
class PacketFeatures:
    """Data class to store packet features"""
    mean: float
    max: float
    min: float
    std: float

@dataclass
class ConnectionFeatures:
    """Data class to store connection features"""
    upstream_ratio: List[float]
    upload_packet: List[PacketFeatures]
    download_packet: List[PacketFeatures]
    inter_packet: List[PacketFeatures]
    bytes_per_second: Dict[str, List[float]]
    packets_per_second: Dict[str, List[float]]
    size_features: Dict[str, List[PacketFeatures]]

class NetworkFeatureExtractor:
    """Class to handle network feature extraction"""
    PACKET_CHECKPOINTS = [2, 4, 8, 16, 32, 64]
    REQUIRED_LENGTH = 6
    MAX_PACKETS = 64

    def __init__(self):
        self.feature_names = self._generate_feature_names()

    def _generate_feature_names(self) -> List[str]:
        """Generate descriptive column names for features"""
        names = []
        
        # Upstream ratio features with percentage indicator
        names.extend([f'upstream_ratio_at_{i}pkt_%' for i in self.PACKET_CHECKPOINTS])
        
        # Timing features in milliseconds
        for direction in ['upload', 'download', 'bidirectional']:
            for i in self.PACKET_CHECKPOINTS:
                names.extend([
                    f'{direction}_timing_{i}pkt_mean_ms',
                    f'{direction}_timing_{i}pkt_max_ms',
                    f'{direction}_timing_{i}pkt_min_ms',
                    f'{direction}_timing_{i}pkt_std_ms'
                ])
        
        # Throughput features
        for direction in ['upload', 'download', 'bidirectional']:
            names.extend([f'{direction}_throughput_{i}pkt_bytes_per_sec' 
                         for i in self.PACKET_CHECKPOINTS])
            names.extend([f'{direction}_packet_rate_{i}pkt_per_sec' 
                         for i in self.PACKET_CHECKPOINTS])
        
        # Packet size features in bytes
        for direction in ['upload', 'download', 'bidirectional']:
            for i in self.PACKET_CHECKPOINTS:
                names.extend([
                    f'{direction}_size_{i}pkt_mean_bytes',
                    f'{direction}_size_{i}pkt_max_bytes',
                    f'{direction}_size_{i}pkt_min_bytes',
                    f'{direction}_size_{i}pkt_std_bytes'
                ])
        
        return names

    def extract_features(self, conn_data: pd.DataFrame) -> Optional[List[float]]:
        """Extract features from connection data"""
        try:
            # Sort and remove outliers at row 3 and 4 if bigger than 1300
            conn_data = conn_data.sort_values('ts_relative')
            if len(conn_data) > 3 and conn_data.iloc[3]['pkt_len'] > 1300:
                conn_data = conn_data.drop(conn_data.index[3]).reset_index(drop=True)
                conn_data = conn_data.drop(conn_data.index[4]).reset_index(drop=True)

            # Identify upload vs. download
            src_ip = conn_data.iloc[0]['src_ip']
            upload_mask = conn_data['src_ip'] == src_ip
            upload_packets = conn_data[upload_mask].head(self.MAX_PACKETS)
            download_packets = conn_data[~upload_mask].head(self.MAX_PACKETS)
            
            # Calculate base metrics
            metrics = {
                'upload': self._calculate_packet_metrics(upload_packets),
                'download': self._calculate_packet_metrics(download_packets),
                'inter': self._calculate_packet_metrics(conn_data.head(self.MAX_PACKETS))
            }
            
            # Calculate features
            features = ConnectionFeatures(
                upstream_ratio=self._calculate_upstream_ratio(metrics),
                upload_packet=self._calculate_timing_features(metrics['upload']),
                download_packet=self._calculate_timing_features(metrics['download']),
                inter_packet=self._calculate_timing_features(metrics['inter']),
                bytes_per_second=self._calculate_throughput(metrics),
                packets_per_second=self._calculate_packet_rate(metrics),
                size_features=self._calculate_size_features(metrics)
            )
            
            return self._concatenate_features(features)
            
        except Exception as e:
            print(f"Error in feature extraction: {e}")
            return None

    def _calculate_packet_metrics(self, packets: pd.DataFrame) -> Dict:
        """Calculate basic packet metrics"""
        if packets.empty:
            return {'ts': [], 'bytes': [], 'total_bytes': []}
            
        ts = packets['ts_relative'].tolist()
        bytes_data = packets['pkt_len'].tolist()
        
        return {
            'ts': ts,
            'bytes': bytes_data,
            'total_bytes': np.cumsum(bytes_data).tolist()
        }
        
    def _calculate_throughput(self, metrics: Dict) -> Dict[str, List[float]]:
        """Calculate bytes per second for each packet checkpoint"""
        throughput = {
            'upload': [],
            'download': [],
            'inter': []
        }
        
        for direction in throughput.keys():
            direction_metrics = metrics[direction]
            ts = direction_metrics['ts']
            total_bytes = direction_metrics['total_bytes']
            
            for checkpoint in self.PACKET_CHECKPOINTS:
                if checkpoint > len(ts) or checkpoint > len(total_bytes):
                    throughput[direction].append(0)
                else:
                    # Calculate throughput as total_bytes / time_elapsed
                    elapsed_time = ts[checkpoint-1] - ts[0]
                    if elapsed_time > 0:
                        throughput[direction].append(total_bytes[checkpoint-1] / elapsed_time)
                    else:
                        throughput[direction].append(0)
                        
        return throughput
        
    def _calculate_packet_rate(self, metrics: Dict) -> Dict[str, List[float]]:
        """Calculate packets per second for each checkpoint"""
        packet_rates = {
            'upload': [],
            'download': [],
            'inter': []
        }
        
        for direction in packet_rates.keys():
            ts = metrics[direction]['ts']
            
            for checkpoint in self.PACKET_CHECKPOINTS:
                if checkpoint > len(ts):
                    packet_rates[direction].append(0)
                else:
                    # Calculate packet rate as num_packets / time_elapsed
                    elapsed_time = ts[checkpoint-1] - ts[0]
                    if elapsed_time > 0:
                        packet_rates[direction].append(checkpoint / elapsed_time)
                    else:
                        packet_rates[direction].append(0)
                        
        return packet_rates
        
    def _calculate_size_features(self, metrics: Dict) -> Dict[str, List[PacketFeatures]]:
        """Calculate packet size statistics for each checkpoint"""
        size_features = {
            'upload': [],
            'download': [],
            'inter': []
        }
        
        for direction in size_features.keys():
            bytes_data = metrics[direction]['bytes']
            
            for checkpoint in self.PACKET_CHECKPOINTS:
                if checkpoint > len(bytes_data):
                    size_features[direction].append(PacketFeatures(0, 0, 0, 0))
                else:
                    checkpoint_bytes = bytes_data[:checkpoint]
                    size_features[direction].append(PacketFeatures(
                        mean=float(np.mean(checkpoint_bytes)),
                        max=float(np.max(checkpoint_bytes)),
                        min=float(np.min(checkpoint_bytes)),
                        std=float(np.std(checkpoint_bytes))
                    ))
                    
        return size_features

    def _calculate_upstream_ratio(self, metrics: Dict) -> List[float]:
        """Calculate upstream ratio at checkpoints"""
        ratios = []
        for checkpoint in self.PACKET_CHECKPOINTS:
            up_bytes = sum(metrics['upload']['bytes'][:checkpoint])
            down_bytes = sum(metrics['download']['bytes'][:checkpoint])
            total = up_bytes + down_bytes
            ratios.append(up_bytes / total if total > 0 else 0)
        return self._pad_list(ratios)

    def _calculate_timing_features(self, metrics: Dict) -> List[PacketFeatures]:
        """Calculate timing features at checkpoints"""
        features = []
        ts = metrics['ts']
        
        for checkpoint in self.PACKET_CHECKPOINTS:
            if len(ts) >= checkpoint:
                deltas = np.diff(ts[:checkpoint])
                features.append(PacketFeatures(
                    mean=float(np.mean(deltas)),
                    max=float(np.max(deltas)),
                    min=float(np.min(deltas)),
                    std=float(np.std(deltas))
                ))
            else:
                features.append(PacketFeatures(0, 0, 0, 0))
                
        return features

    def _pad_list(self, lst: List, default_value: float = 0) -> List:
        """Pad list to required length"""
        if len(lst) < self.REQUIRED_LENGTH:
            return lst + [default_value] * (self.REQUIRED_LENGTH - len(lst))
        return lst

    def _concatenate_features(self, features: ConnectionFeatures) -> List[float]:
        """Flatten ConnectionFeatures into a single list of features."""
        concatenated = []
        
        # Add upstream ratio features
        concatenated.extend(features.upstream_ratio)
        
        # Add timing features for upload, download, and inter-packet
        for packet_features in features.upload_packet:
            concatenated.extend([packet_features.mean, packet_features.max, 
                                 packet_features.min, packet_features.std])
        
        for packet_features in features.download_packet:
            concatenated.extend([packet_features.mean, packet_features.max, 
                                 packet_features.min, packet_features.std])
        
        for packet_features in features.inter_packet:
            concatenated.extend([packet_features.mean, packet_features.max, 
                                 packet_features.min, packet_features.std])
        
        # Add throughput features
        for direction in ['upload', 'download', 'inter']:
            concatenated.extend(features.bytes_per_second[direction])
        
        # Add packet rate features
        for direction in ['upload', 'download', 'inter']:
            concatenated.extend(features.packets_per_second[direction])
        
        # Add size features
        for direction in ['upload', 'download', 'inter']:
            for packet_features in features.size_features[direction]:
                concatenated.extend([packet_features.mean, packet_features.max,
                                     packet_features.min, packet_features.std])
        
        return concatenated

    def _find_csv_files(self, root_dir: str) -> List[Tuple[str, str]]:
        """Find all relevant CSV files"""
        csv_files = []
        for path in Path(root_dir).rglob('*.csv'):
            if path.name == 'background_conn_labeled.csv':
                csv_files.append((str(path), 'background'))
            elif path.name == 'relayed_conn_labeled.csv':
                csv_files.append((str(path), 'relayed'))
            elif path.name == 'normal_conn.csv':
                csv_files.append((str(path), 'background'))
        return csv_files

    def _process_single_file(self, file_info: Tuple[str, str]) -> Dict:
        """Process a single CSV file into a dictionary of extracted features."""
        file_path, file_type = file_info
        print(file_path)
        try:
            df = pd.read_csv(file_path)
            features_dict = {}
            
            for conn_id, conn_data in df.groupby('conn'):
                extracted_features = self.extract_features(conn_data)
                if extracted_features is not None:
                    features_dict[f"{file_path}_{file_type}_{conn_id}"] = {
                        'features': extracted_features,
                        'type': file_type,
                    }
            
            return features_dict
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return {}

    def _create_dataframes(self, features: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Convert the per-connection 'features' dictionary into two DataFrames:
          1) features_df (actual numerical features + 'label'),
          2) metadata_df (connection metadata).
        """
        data = []
        labels = []
        metadata = []
        
        for key, value in features.items():
            # e.g. key => file_path_fileType_connID
            file_path, conn_type, conn_id = key.rsplit('_', 2)
            
            # Add features and binary label
            data.append(value['features'])
            labels.append(1 if value['type'] == 'relayed' else 0)
            
            metadata.append({
                'connection_id': key,
                'type': value['type'],
                'file_path': file_path,
                'original_conn_id': conn_id,
                'timestamp': pd.Timestamp.now(),
                'is_relayed': value['type'] == 'relayed'
            })
        
        # Create features DataFrame with label
        features_df = pd.DataFrame(data, columns=self.feature_names)
        features_df['label'] = labels
        
        # Create metadata DataFrame
        metadata_df = pd.DataFrame(metadata)
        metadata_df['data_source'] = metadata_df['file_path'].apply(lambda x: Path(x).parent.name)
        metadata_df['analysis_date'] = pd.Timestamp.now().date()
        
        return features_df, metadata_df

    def process_csv_files_in_chunks(self, root_dir: str, output_dir: Path, max_workers: int = 1) -> None:
        """
        Process CSV files in the given root directory using a thread pool, but
        write out features every 10 files so that we do not accumulate everything
        in memory. Also keep partial counts for summary.
        """
        csv_files = self._find_csv_files(root_dir)
        
        # Prepare output CSVs for writing
        features_file = output_dir / "features.parquet"
        metadata_file = output_dir / "metadata.parquet"
        
        # If they already exist, remove them for a fresh run (optional)
        if features_file.exists():
            features_file.unlink()
        if metadata_file.exists():
            metadata_file.unlink()
        
        # We'll keep running totals for summary
        total_connections = 0
        background_count = 0
        relayed_count = 0
        data_source_counts = {}
        
        # Used to track chunks of files
        partial_features_list = []
        processed_files_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self._process_single_file, file_info): file_info
                for file_info in csv_files
            }
            
            for future in as_completed(future_to_file):
                file_features_dict = future.result()
                partial_features_list.append(file_features_dict)
                processed_files_count += 1

                # If we've processed 10 files, flush them to disk
                if processed_files_count % 10 == 0:
                    # Convert chunk of features to dataframes and append to CSV
                    (partial_total_connections, partial_background_count, partial_relayed_count) = self._flush_partial_data(
                        partial_features_list,
                        features_file,
                        metadata_file,
                        data_source_counts
                    )
                    
                    # Update total
                    total_connections += partial_total_connections
                    background_count += partial_background_count
                    relayed_count += partial_relayed_count
                    
                    # After flushing, clear them from memory
                    partial_features_list = []
                    
        
            # Flush any leftover partial results if fewer than 10 remain
            if partial_features_list:
                (partial_total_connections, partial_background_count, partial_relayed_count) = self._flush_partial_data(
                    partial_features_list,
                    features_file,
                    metadata_file,
                    data_source_counts
                )
            
                total_connections += partial_total_connections
                background_count += partial_background_count
                relayed_count += partial_relayed_count    
                partial_features_list = []

        # Print summary
        print("\nNetwork Traffic Analysis Summary")
        print("================================")
        print(f"Input Directory: {root_dir}")
        print(f"Output Directory: {output_dir}")
        print(f"\nTotal Connections Analyzed: {total_connections:,}")
        print(f"Background Connections: {background_count:,} "
              f"({(background_count / total_connections * 100) if total_connections else 0:.1f}%)")
        print(f"Relayed Connections: {relayed_count:,} "
              f"({(relayed_count / total_connections * 100) if total_connections else 0:.1f}%)")

        unique_data_sources = list(data_source_counts.keys())
        print("\nData Sources:", len(unique_data_sources))
        
        print("\nConnections by Data Source:")
        for ds in unique_data_sources:
            ds_count = data_source_counts[ds]['total']
            print(f"{ds}: {ds_count} connections")
        
        print(f"\nFeatures File: {features_file}")
        print(f"Metadata File: {metadata_file}")
        
        # Optionally, also write the feature reference text (just once).
        feature_ref_file = output_dir / "feature_reference.txt"
        with open(feature_ref_file, 'w') as f:
            f.write("Feature Names Description\n")
            f.write("=======================\n\n")
            for i, feature in enumerate(self.feature_names):
                f.write(f"{i+1}. {feature}\n")
            f.write(f"\n{len(self.feature_names)+1}. label (0=background, 1=relayed)\n")
        print(f"Feature reference saved to: {feature_ref_file}")

    def _flush_partial_data(
        self, 
        partial_features_list: List[Dict], 
        features_file: Path, 
        metadata_file: Path, 
        data_source_counts: Dict
    ) -> None:
        """
        Merge all dictionaries in partial_features_list, convert to DataFrames,
        and append them to the features.csv and metadata.csv. Update data_source_counts
        and counters (total_connections, background_count, relayed_count).
        """
        # Flatten out all dictionary entries from each file
        merged_features = {}
        for fdict in partial_features_list:
            merged_features.update(fdict)
        
        if not merged_features:
            return
        
        # Create the DataFrames
        features_df, metadata_df = self._create_dataframes(merged_features)
        
        # Update data_source_counts
        for ds in metadata_df['data_source'].unique():
            ds_subset = metadata_df[metadata_df['data_source'] == ds]
            ds_count = len(ds_subset)
            if ds not in data_source_counts:
                data_source_counts[ds] = {'total': 0}
            data_source_counts[ds]['total'] += ds_count
        
        # Append to disk (writing header only if file doesn't exist)
        features_df.to_parquet(
            features_file,
            engine='fastparquet',
            compression='snappy',
            append=features_file.exists()  # False if file doesn't exist (new file), True otherwise
        )
        
        metadata_df["analysis_date"] = metadata_df["analysis_date"].astype(str)
        metadata_df.to_parquet(
            metadata_file,
            engine='fastparquet',
            compression='snappy',
            append=metadata_file.exists()
        )

        # Return updated counters
        total_connections = len(features_df)
        background_count = (features_df['label'] == 0).sum()
        relayed_count = (features_df['label'] == 1).sum()
        return (total_connections, background_count, relayed_count)


if __name__ == "__main__":
    import sys
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract network traffic features')
    parser.add_argument('input_path', type=str, help='Input directory containing CSV files')
    parser.add_argument('output_path', type=str, help='Output directory for features')
    
    args = parser.parse_args()
    
    # Convert paths to Path objects
    input_path = Path(args.input_path)
    output_dir = Path(args.output_path)

    # Verify input directory exists
    if not input_path.exists():
        print(f"\nError: Input directory not found: {input_path}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize feature extractor
    extractor = NetworkFeatureExtractor()
    
    # Process all CSV files in chunks, saving partial results every 10 files
    extractor.process_csv_files_in_chunks(str(input_path), output_dir, max_workers=1)
