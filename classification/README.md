# Classification Experiments with AutoGluon

This directory contains scripts for running classification experiments using AutoGluon on network traffic data.

## Overview

The main script `autogluon_experiments.py` performs binary classification experiments using different feature combinations:
- Correlation features
- K-Fingerprinting features
- SLT (Sequence Length Time) features
- Various combinations of the above

## Configuration

The experiments are configured using two YAML files in the `config` directory:

### paths.yaml
Contains all the dataset and model paths:
- Base paths for content, models, and results
- Dataset paths (ds4 and ds11)
- Feature paths for different feature types (correlation, SLT, k-features)
- Split paths (train/test/val)

### experiment_config.yaml
Defines the experiment configurations:
- Experiment number (determines feature combination)
- Number of PCaps to use (20 or 50)
- Description of the experiment

## Experiment Types

The script supports four different experiment settings (controlled by `experiment_number`):
- `0`: K-Fingerprinting + Correlation features
- `1`: Correlation features only
- `2`: K-Fingerprinting features only
- `3`: SLT features only

## Usage

1. Ensure your data paths are correctly set in `config/paths.yaml`
2. Configure your experiments in `config/experiment_config.yaml`
3. Run the experiments:
```bash
python -m classification.autogluon_experiments
```

## Output

The script creates a timestamped results directory containing:
- Separate folders for each experiment configuration
- Test, train, and validation data results CSV files
- Model performance results
- Feature importance rankings
- Confusion matrix data
- Prediction probabilities
- Misclassified samples
- A summary CSV file comparing all experiments

Results are saved in the directory specified by `results_dir` in `paths.yaml` with a timestamp appended.

## Example Results Structure
```
experiment_results_20230815_143022/
├── 20_pcaps_setting/
│   ├── test_data.csv
│   ├── train_data.csv
│   ├── val_data.csv
│   ├── results.csv
│   ├── feature_importance.csv
│   └── full_results.pkl
├── 50_pcaps_setting/
│   └── ...
└── experiments_summary.csv
```

## Performance Metrics

For each experiment, the script reports:
- F1 Score
- Precision
- Recall
- False Positive Rate (FPR)
- False Negative Rate (FNR)
- AUC Score
- Best performing model type

## Requirements

- AutoGluon
- Pandas
- Scikit-learn
- PyYAML
- Matplotlib