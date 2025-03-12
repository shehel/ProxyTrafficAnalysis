import os
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import pdb
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
    PACKET_CHECKPOINTS = [2, 4,8,16,32,64]
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
        # set first 6 rows to be the same value 250 for ['pkt_len'] column
        try:
            # Sort and split packets
            
            conn_data = conn_data.sort_values('ts_relative')
            if len(conn_data) > 3 and conn_data.iloc[3]['pkt_len'] > 1300:
                conn_data = conn_data.drop(conn_data.index[3]).reset_index(drop=True)
                conn_data = conn_data.drop(conn_data.index[4]).reset_index(drop=True)

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
        return csv_files

    def _process_single_file(self, file_info: Tuple[str, str]) -> Dict:
        """Process a single CSV file"""
        file_path, file_type = file_info
        print (file_path)
        try:
            df = pd.read_csv(file_path)
            features = {}
            
            for conn_id, conn_data in df.groupby('conn'):
                #if 'relayed' in file_path:
                #relayed_random_padding = pd.Series(
                #    np.random.normal(loc=250, scale=125, size=len(conn_data)).clip(0, 350).round().astype(int),
                #    index=conn_data.index
                #    )
                # if 'background' in file_path:
                #     bg_random_padding = pd.Series(
                #     np.random.normal(loc=0.050, scale=0.01, size=len(conn_data)).clip(0, 0.1),
                #     index=conn_data.index
                #     )
                #     conn_data['ts_relative'] = bg_random_padding + conn_data['ts_relative']


                #conn_data['pkt_len'] = relayed_random_padding #+ conn_data['pkt_len']
                extracted_features = self.extract_features(conn_data)
                if extracted_features is not None:
                    features[f"{file_path}_{file_type}_{conn_id}"] = {
                        'features': extracted_features,
                        'type': file_type,
                        'provider': conn_data['App name'].iloc[0]
                    }
            
            return features
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return {}

    def _create_dataframes(self, features: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Create features and metadata DataFrames with enhanced metadata and labels
        
        Returns:
            Tuple containing:
            - features_df: DataFrame with features and binary label (0=background, 1=relayed)
            - metadata_df: DataFrame with connection metadata
        """
        data = []
        labels = []
        metadata = []
        
        for key, value in features.items():
            # Extract file path and connection info from key
            file_path, conn_type, conn_id = key.rsplit('_', 2)
            
            # Add features and binary label
            data.append(value['features'])
            labels.append(1 if value['type'] == 'relayed' else 0)
            
            metadata.append({
                'connection_id': key,
                'type': value['type'],
                'provider': value['provider'],
                'file_path': file_path,
                'original_conn_id': conn_id,
                'timestamp': pd.Timestamp.now(),
                'is_relayed': value['type'] == 'relayed'
            })
        
        # Create features DataFrame with label column
        features_df = pd.DataFrame(data, columns=self.feature_names)
        features_df['label'] = labels
        
        # Create metadata DataFrame
        metadata_df = pd.DataFrame(metadata)
        
        # Add derived metadata columns
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

if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    # Get input directory from command line or use default
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        if not str(input_path).startswith('data/processed/'):
            print("\nError: Input path must start with 'data/processed/'")
            sys.exit(1)
    else:
        print("\nError: Please provide input path (e.g., data/processed/dir1/train)")
        sys.exit(1)

    # Extract the relative path after 'data/processed/'
    relative_path = Path(str(input_path).replace('data/processed/', ''))
    
    # Setup input and output paths
    input_dir = Path('data/processed') / relative_path
    output_dir = Path('data/feats') / relative_path
    
    # Verify input directory exists
    if not input_dir.exists():
        print(f"\nError: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize feature extractor
    extractor = NetworkFeatureExtractor()
    
    # Process all CSV files
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
        for i, feature in enumerate(extractor.feature_names):
            f.write(f"{i+1}. {feature}\n")
        f.write(f"\n{len(extractor.feature_names)+1}. label (0=background, 1=relayed)")
    
    print(f"- {feature_ref_file}")