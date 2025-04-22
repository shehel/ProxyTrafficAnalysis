import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

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
    differenced_features: List[float]

class NetworkFeatureExtractor:
    """Class to handle network feature extraction"""
    
    def __init__(self, direction="download", num_elements=4, data_type="ts_relative"):
        """
        Initialize the feature extractor with specified parameters
        
        Args:
            direction: One of "upload", "download", or "bidirectional"
            num_elements: Number of differenced elements to extract
            data_type: Type of data to extract features from ("volume" or "ts_relative")
        """
        self.direction = direction
        self.num_elements = num_elements
        self.data_type = data_type
        
        # Validate inputs
        if self.direction not in ["upload", "download", "bidirectional"]:
            raise ValueError("Direction must be 'upload', 'download', or 'bidirectional'")
            
        if self.data_type not in ["volume", "ts_relative"]:
            raise ValueError("Data type must be 'volume' or 'ts_relative'")
            
        if not isinstance(self.num_elements, int) or self.num_elements <= 0:
            raise ValueError("Number of elements must be a positive integer")
            
        self.feature_names = self._generate_feature_names()

    def _generate_feature_names(self) -> List[str]:
        """Generate descriptive column names for features"""
        names = []
        
        for i in range(self.num_elements):
            names.append(f"{self.direction}_{self.data_type}_diff_{i+1}")
            
        return names

    def extract_features(self, conn_data: pd.DataFrame) -> Optional[List[float]]:
        """Extract features from connection data"""
        try:
            # Sort by timestamp
            conn_data = conn_data.sort_values('ts_relative')
            
            # delete 4th packet if its larger than 1300
            if len(conn_data) > 3 and conn_data.iloc[3]['pkt_len'] > 1300:
                conn_data = conn_data.drop(conn_data.index[3]).reset_index(drop=True)
                conn_data = conn_data.drop(conn_data.index[4]).reset_index(drop=True)
            #pdb.set_trace()

            # Filter by direction
            src_ip = conn_data.iloc[0]['src_ip']
            if self.direction == "upload":
                # Filter packets sent by source
                direction_packets = conn_data[conn_data['src_ip'] == src_ip]
            elif self.direction == "download":
                # Filter packets received by source
                direction_packets = conn_data[conn_data['src_ip'] != src_ip]
            else:  # bidirectional
                direction_packets = conn_data
            
            # Get data series based on data_type
            if self.data_type == "volume":
                data_series = direction_packets['pkt_len']
            else:  # ts_relative
                data_series = direction_packets['ts_relative']
                
            # If we don't have enough packets, return None
            if len(data_series) < self.num_elements + 1:  # Need at least num_elements + 1 to get num_elements differences
                return None
                
            # Calculate differences
            diff_values = np.diff(data_series.values[:self.num_elements + 1])
            
            features = ConnectionFeatures(
                differenced_features=diff_values.tolist()
            )
            
            return self._concatenate_features(features)
            
        except Exception as e:
            print(f"Error in feature extraction: {e}")
            return None

    def _concatenate_features(self, features: ConnectionFeatures) -> List[float]:
        """Flatten ConnectionFeatures into a single list of features"""
        return features.differenced_features

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
        print(file_path)
        try:
            df = pd.read_csv(file_path)
            features = {}
            
            for conn_id, conn_data in df.groupby('conn'):
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
        """Create features and metadata DataFrames with enhanced metadata and labels"""
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

if __name__ == "__main__":
    import sys
    from datetime import datetime
    import argparse
    
    # Setup command line arguments
    parser = argparse.ArgumentParser(description='Extract network features')
    parser.add_argument('input_path', help='Path to input directory (must start with data/processed/)')
    parser.add_argument('--direction', choices=['upload', 'download', 'bidirectional'], 
                        default='download', help='Direction of packets to analyze')
    parser.add_argument('--num_elements', type=int, default=4, 
                        help='Number of differenced elements to extract')
    parser.add_argument('--data_type', choices=['volume', 'ts_relative'], 
                        default='ts_relative', help='Type of data to extract (volume=pkt_len)')
    parser.add_argument('--max_workers', type=int, default=1, 
                        help='Maximum number of worker threads')
    
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
    
    # Verify input directory exists
    if not input_dir.exists():
        print(f"\nError: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Print parameters
    print(f"\nParameters:")
    print(f"- Direction: {args.direction}")
    print(f"- Number of differenced elements: {args.num_elements}")
    print(f"- Data type: {args.data_type}")
    print(f"- Max workers: {args.max_workers}")
    
    # Initialize feature extractor with parameters
    extractor = NetworkFeatureExtractor(
        direction=args.direction,
        num_elements=args.num_elements,
        data_type=args.data_type
    )
    
    # Process all CSV files
    print(f"\nProcessing files from: {input_dir}")
    print(f"Saving results to: {output_dir}")
    features_df, metadata_df = extractor.process_csv_files(str(input_dir), max_workers=args.max_workers)
    
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
    features_file = output_dir / f"features_{args.direction}_{args.num_elements}_{args.data_type}.csv"
    metadata_file = output_dir / f"metadata_{args.direction}_{args.num_elements}_{args.data_type}.csv"
    
    features_df.to_csv(features_file, index=False)
    metadata_df.to_csv(metadata_file, index=False)
    
    print("\nResults saved to:")
    print(f"- {features_file}")
    print(f"- {metadata_file}")
    
    # Save feature names reference
    feature_ref_file = output_dir / f"feature_reference_{args.direction}_{args.num_elements}_{args.data_type}.txt"
    with open(feature_ref_file, 'w') as f:
        f.write("Feature Names Description\n")
        f.write("=======================\n\n")
        for i, feature in enumerate(extractor.feature_names):
            f.write(f"{i+1}. {feature}\n")
        f.write(f"\n{len(extractor.feature_names)+1}. label (0=background, 1=relayed)")
    
    print(f"- {feature_ref_file}")