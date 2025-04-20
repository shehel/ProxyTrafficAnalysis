import os
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import pdb
import json
import pdb
import random
import numpy as np

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
    PACKET_CHECKPOINTS = [2, 4,8, 16,20]
    REQUIRED_LENGTH = 6
    MAX_PACKETS = 20
    MAX_EMPIRICAL_SAMPLES = 50000
    RANDOM_SEED = 42  # Add constant for random seed
    
    def __init__(self, adversarial_attack: bool = False, distributions_path: str = None, 
                 use_empirical_sampling: bool = False):
        # Set random seeds
        random.seed(self.RANDOM_SEED)
        np.random.seed(self.RANDOM_SEED)
        
        self.feature_names = self._generate_feature_names()
        self.adversarial_attack = adversarial_attack
        self.background_timing_distribution = None
        self.background_length_distribution = None
        self.empirical_packet_lengths = None
        self.use_empirical_sampling = use_empirical_sampling
        
        # Load distributions if path is provided
        if distributions_path:
            self.load_background_distributions(distributions_path)
            
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
        # set first 6 rows to be the same value 250 for ['pkt_len'] column
        try:
            # Sort and split packets
            
            
            # skip the first 4 elements
            #conn_data = conn_data.iloc[8:]
            #conn_data.loc[conn_data.index[:3], 'ts_relative'] = conn_data.loc[conn_data.index[0], 'ts_relative']   
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
            
            # if conn_data['conn'].iloc[0]=='normal_conn_13012':
            #     pdb.set_trace()
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
        
    def fit_and_save_background_distributions(self, root_dir: str, output_path: str) -> None:
        """
        Fit timing and packet length distributions from all background traffic in training files
        and save the parameters to disk.
        """
        # Find all CSV files
        csv_files = self._find_csv_files(root_dir)
        
        # Filter for training background files
        training_files = []
        for path, file_type in csv_files:
            if 'train' in path and file_type == 'background':
                training_files.append((path, file_type))
        
        if not training_files:
            print("No training files found for fitting background distributions")
            return
        
        # Collect timing and length data from all training files
        timing_diffs = []
        packet_lengths = []
        
        print(f"Fitting distributions on {len(training_files)} training files")
        for file_path, _ in training_files:
            try:
                df = pd.read_csv(file_path)
                
                # Process each connection
                for _, conn_data in df.groupby('conn'):
                    conn_data = conn_data.sort_values('ts_relative')
                    
                    # Apply the same preprocessing as in _process_single_file
                    if len(conn_data) > 3 and conn_data.iloc[3]['pkt_len'] > 1300:
                        conn_data = conn_data.drop(conn_data.index[3]).reset_index(drop=True)
                        conn_data = conn_data.drop(conn_data.index[4]).reset_index(drop=True)
                        
                    if len(conn_data) >= 4:
                        # Calculate time difference between 3rd and 4th packet
                        timing_diff = conn_data.iloc[3]['ts_relative'] - conn_data.iloc[2]['ts_relative']
                        # Get packet length of 4th packet
                        packet_length = conn_data.iloc[3]['pkt_len']
                        
                        timing_diffs.append(timing_diff)
                        packet_lengths.append(packet_length)
            except Exception as e:
                print(f"Error processing {file_path} for distribution fitting: {e}")
        
        if not timing_diffs or not packet_lengths:
            print("No valid data found for fitting background distributions")
            return
        
        # Fit timing distribution
        timing_diffs = np.array(timing_diffs)
        timing_diffs = timing_diffs[timing_diffs > 0]
        timing_distribution = {
            'mean': float(np.mean(np.log(timing_diffs))),
            'std': float(np.std(np.log(timing_diffs)))
        }
        
        # Store empirical packet lengths (limited to MAX_EMPIRICAL_SAMPLES)
        packet_lengths = np.array(packet_lengths)
        packet_lengths = packet_lengths[packet_lengths > 0]
        if len(packet_lengths) > self.MAX_EMPIRICAL_SAMPLES:
            np.random.shuffle(packet_lengths)
            packet_lengths = packet_lengths[:self.MAX_EMPIRICAL_SAMPLES]
        
        # Fit normal distribution for packet lengths as fallback
        length_distribution = {
            'mean': float(np.mean(packet_lengths)),
            'std': float(np.std(packet_lengths)),
            'empirical_samples': packet_lengths.tolist()
        }
        
        # Save distributions to disk
        distributions = {
            'timing': timing_distribution,
            'length': length_distribution
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(distributions, f)
        
        print(f"Saved background distributions to {output_path}")
        print(f"Timing: μ={np.exp(timing_distribution['mean']):.3f}ms, "
              f"Length: μ={length_distribution['mean']:.0f}bytes")
        
        # Set the distributions for current use
        self.background_timing_distribution = timing_distribution
        self.background_length_distribution = length_distribution
        
    def load_background_distributions(self, file_path: str) -> bool:
        """Load background distributions from a saved file."""
        try:
            with open(file_path, 'r') as f:
                distributions = json.load(f)
                
            self.background_timing_distribution = distributions['timing']
            self.background_length_distribution = distributions['length']
            
            # Load empirical samples if available
            if 'empirical_samples' in distributions['length']:
                self.empirical_packet_lengths = np.array(distributions['length']['empirical_samples'])
            
            print(f"Loaded background distributions from {file_path}")
            print(f"Timing: μ={np.exp(self.background_timing_distribution['mean']):.3f}ms")
            if self.empirical_packet_lengths is not None:
                print(f"Length: {len(self.empirical_packet_lengths)} empirical samples available")
            print(f"Length: μ={self.background_length_distribution['mean']:.0f}bytes")
            return True
        except Exception as e:
            print(f"Error loading background distributions: {e}")
            return False
        
    def process_csv_files(self, root_dir: str, max_workers: int = 1) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Process all CSV files in directory"""
        csv_files = self._find_csv_files(root_dir)
        all_features = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self._process_single_file, file_info): file_info 
                for file_info in csv_files
            }
            
            for future in future_to_file:
                file_features = future.result()
                if file_features:
                    all_features.update(file_features)
        
        return self._create_dataframes(all_features)
        
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
        """Process a single CSV file"""
        file_path, file_type = file_info
        print(file_path)
        try:
            df = pd.read_csv(file_path)
            features = {}
            
            # Preprocess each connection before any other operations
            processed_connections = {}
            connection_rtts = {}  # New dict to store RTTs
            
            for conn_id, conn_data in df.groupby('conn'):
                # Sort and drop packets
                conn_data = conn_data.sort_values('ts_relative')
                
                # Calculate RTT before any packet dropping
                                
                if len(conn_data) > 3 and conn_data.iloc[3]['pkt_len'] > 1300:
                    conn_data = conn_data.drop(conn_data.index[3]).reset_index(drop=True)
                    conn_data = conn_data.drop(conn_data.index[4]).reset_index(drop=True)
                processed_connections[conn_id] = conn_data
            
            # Reconstruct DataFrame with processed connections
            df = pd.concat(processed_connections.values())
            
            # No longer fitting distribution per file
            
            for conn_id, conn_data in processed_connections.items():
                # Apply adversarial attack for relayed connections if distributions are available
                if self.adversarial_attack and file_type == 'relayed' and self.background_timing_distribution:
                    #print ("applying timing attack", file_path)
                    conn_data = self._apply_timing_attack(conn_data)
                
                extracted_features = self.extract_features(conn_data)
                rtt = get_rtt(conn_data)

                if extracted_features is not None:
                    features[f"{file_path}_{file_type}_{conn_id}"] = {
                        'features': extracted_features,
                        'type': file_type,
                        'provider': 'null',#conn_data['App name'].iloc[0],
                        'rtt': rtt # Add RTT to features dict
                    }
            
            return features
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return {}
            
    def _create_dataframes(self, features: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Create features and metadata DataFrames with enhanced metadata and labels"""
        data = []
        labels = []
        metadata = []
        conn_ids = []
        pcaps = []
        rtts = []  # New list for RTT values
        
        for key, value in features.items():
            # Extract file path and connection info from key
            file_path, conn_type, conn_id = key.rsplit('_', 2)
            pcap = Path(file_path).parts[-2]
            
            # Add features and binary label
            data.append(value['features'])
            labels.append(1 if value['type'] == 'relayed' else 0)
            conn_ids.append('normal_conn_'+conn_id)
            pcaps.append(pcap)
            rtts.append(value['rtt'])  # Use pre-calculated RTT
            
            metadata.append({
                'connection_id': key,
                'type': value['type'],
                'provider': 'null',#value['provider'],
                'file_path': file_path,
                'original_conn_id': conn_id,
                'timestamp': pd.Timestamp.now(),
                'is_relayed': value['type'] == 'relayed'
            })
        
        # Create features DataFrame with label column and new columns
        features_df = pd.DataFrame(data, columns=self.feature_names)
        features_df['label'] = labels
        features_df['conn'] = conn_ids
        features_df['pcap'] = pcaps
        features_df['rtt'] = rtts
        
        # Create metadata DataFrame
        metadata_df = pd.DataFrame(metadata)
        metadata_df['data_source'] = metadata_df['file_path'].apply(lambda x: Path(x).parent.name)
        metadata_df['analysis_date'] = pd.Timestamp.now().date()
        
        return features_df, metadata_df
        
    def _concatenate_features(self, features: ConnectionFeatures) -> List[float]:
        """Flatten ConnectionFeatures into a single list of features.
        
        Args:
            features: ConnectionFeatures object containing all extracted features
            
        Returns:
            List of float values representing all features concatenated in order
        """
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
        
    def _apply_timing_attack(self, conn_data: pd.DataFrame) -> pd.DataFrame:
        """Apply timing and packet length attack to relayed connection data"""
        conn_data = conn_data.sort_values('ts_relative').reset_index(drop=True)
        
        if len(conn_data) < 4 or not self.background_timing_distribution:
            return conn_data
            
        # Generate new timing difference from background distribution
        new_timing = np.random.lognormal(
            mean=self.background_timing_distribution['mean'],
            sigma=self.background_timing_distribution['std']
        )
        
        # Calculate current timing difference
        old_timing = conn_data.iloc[3]['ts_relative'] - conn_data.iloc[2]['ts_relative']
        
        # Calculate and apply timing adjustment
        timing_adjustment = old_timing - new_timing
        conn_data.loc[3:, 'ts_relative'] = conn_data.loc[3:, 'ts_relative'] - timing_adjustment
        
        # Generate new packet length using empirical sampling if available and enabled
        if self.use_empirical_sampling and self.empirical_packet_lengths is not None:
            new_length = np.random.choice(self.empirical_packet_lengths)
        else:
            # Fall back to normal distribution sampling
            new_length = np.random.normal(
                loc=self.background_length_distribution['mean'],
                scale=self.background_length_distribution['std']
            )
            new_length = max(1, int(round(new_length)))
        
        conn_data.at[3, 'pkt_len'] = new_length
        return conn_data

def get_rtt(conn_data: pd.DataFrame) -> float:
    """
    Calculate RTT as time difference between first large packet (>1000 bytes) and first packet
    
    Args:
        conn_data: DataFrame containing connection data with 'ts_relative' and 'pkt_len' columns
        
    Returns:
        float: RTT in milliseconds, or 0 if no large packet found
    """
    try:
        # Get first packet timestamp
        first_ts = conn_data.iloc[0]['ts_relative']
        
        # Find first packet > 1000 bytes
        large_packet = conn_data[conn_data['pkt_len'] > 1000].iloc[0]
        
        # Calculate RTT
        rtt = large_packet['ts_relative'] - first_ts
        return float(rtt)
    except (IndexError, KeyError):
        return 0.0

if __name__ == "__main__":
    import sys
    import argparse
    from datetime import datetime
    
    # Add these lines before creating the NetworkFeatureExtractor
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    parser = argparse.ArgumentParser(description='Extract network traffic features')
    parser.add_argument('input_path', help='Input path (must start with data/processed/)')
    parser.add_argument('--adversarial', action='store_true', help='Enable adversarial timing attack')
    parser.add_argument('--empirical-sampling', action='store_true', 
                       help='Use empirical sampling for packet lengths')
    parser.add_argument('--fit-distributions', action='store_true', 
                       help='Fit background distributions on training data and save to disk')
    parser.add_argument('--load-distributions', type=str, default='',
                       help='Load background distributions from file')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker threads')
    parser.add_argument('--output-prefix', type=str, default='features_clean_v4',
                       help='Prefix for output files (default: features_clean_v4)')
    args = parser.parse_args()
    
    input_path = Path(args.input_path)
    if not str(input_path).startswith('data/processed/'):
        print("\nError: Input path must start with 'data/processed/'")
        sys.exit(1)
    # Extract the relative path after 'data/processed/'
    relative_path = Path(str(input_path).replace('data/processed/', ''))
    
    # Setup input and output paths
    input_dir = Path('data/processed') / relative_path
    output_dir = Path('data/feats') / relative_path
    
    if not input_dir.exists():
        print(f"\nError: Input directory not found: {input_dir}")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize feature extractor with adversarial flag and empirical sampling option
    extractor = NetworkFeatureExtractor(
        adversarial_attack=args.adversarial,
        use_empirical_sampling=args.empirical_sampling
    )
    
    # Handle fitting or loading distributions based on command-line arguments
    if args.fit_distributions:
        dist_output_path = output_dir / "background_distributions.json"
        print(f"\nFitting background distributions on training data...")
        extractor.fit_and_save_background_distributions(str(input_dir), str(dist_output_path))
    elif args.load_distributions:
        if not extractor.load_background_distributions(args.load_distributions):
            print("Failed to load distributions, exiting.")
            sys.exit(1)
    
    # Process all CSV files
    print(f"\nProcessing files from: {input_path}")
    print(f"Saving results to: {output_dir}")
    features_df, metadata_df = extractor.process_csv_files(str(input_dir), max_workers=args.workers)

    # Print summary statistics
    total_connections = len(features_df)
    if total_connections == 0:
        print("\nNo connections found in the input directory!")
        sys.exit(1)
        
    background_count = sum(features_df['label'] == 0)
    relayed_count = sum(features_df['label'] == 1)
    
    print("\nNetwork Traffic Analysis Summary")
    print("================================")
    print(f"Input Directory: {input_path}")
    print(f"Output Directory: {output_dir}")
    print(f"\nTotal Connections Analyzed: {total_connections:,}")
    print(f"Background Connections: {background_count:,} ({background_count/total_connections*100:.1f}%)")
    print(f"Relayed Connections: {relayed_count:,} ({relayed_count/total_connections*100:.1f}%)")
    
    print("\nData Sources:", len(metadata_df['data_source'].unique()))
    
    print("\nConnections by Data Source:")
    print(metadata_df['data_source'].value_counts().to_string())
    
    print("\nFeature DataFrame Shape:", features_df.shape)
    print("Metadata DataFrame Shape:", metadata_df.shape)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    features_file = output_dir / f"{args.output_prefix}.parquet"
    metadata_file = output_dir / f"{args.output_prefix}_metadata.parquet"
    feature_ref_file = output_dir / f"{args.output_prefix}_reference.txt"

    features_df.to_parquet(features_file, index=False)
    metadata_df.to_parquet(metadata_file, index=False)

    print("\nResults saved to:")
    print(f"- {features_file}")
    print(f"- {metadata_file}")

    # Save feature names reference
    with open(feature_ref_file, 'w') as f:
        f.write("Feature Names Description\n")
        f.write("=======================\n\n")
        for i, feature in enumerate(extractor.feature_names):
            f.write(f"{i+1}. {feature}\n")
        f.write(f"\n{len(extractor.feature_names)+1}. label (0=background, 1=relayed)")

    print(f"- {feature_ref_file}")