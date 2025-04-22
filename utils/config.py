import os
import yaml
from pathlib import Path

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        config_path = Path(__file__).parent.parent / 'config' / 'paths.yaml'
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get_dataset_path(self, dataset_type, include_attack=True, full_dataset=True, fifty_pcaps=True):
        base = self.config['base_paths']['content_dir']
        dataset = "ds11" if full_dataset else "ds4"
        
        if dataset_type == "corr":
            pcap_suffix = "50" if fifty_pcaps else "20"
            path_key = "attack_" if include_attack else "clean_"
            path_key += pcap_suffix
            return os.path.join(base, dataset, self.config['feature_paths']['corr']['attack'][path_key])
        
        elif dataset_type == "slt":
            base_key = "attack" if include_attack else "clean"
            return os.path.join(base, dataset, self.config['feature_paths']['slt'][base_key]['base_dir'])
        
        elif dataset_type == "k":
            base_key = "attack" if include_attack else "clean"
            return os.path.join(base, dataset, self.config['feature_paths']['k_features'][base_key]['base_dir'])
        
        return None
    
    def get_file_extension(self, full_dataset=True):
        dataset = "ds11" if full_dataset else "ds4"
        return self.config['datasets'][dataset]['extensions']
    
    def get_models_dir(self):
        return self.config['base_paths']['models_dir']
    
    def get_results_dir(self):
        return self.config['base_paths']['results_dir']
    
    def get_splits(self):
        return self.config['splits']
