import os
import matplotlib
import pandas as pd
matplotlib.use('Agg')
from autogluon.tabular import TabularPredictor as task
from sklearn.metrics import classification_report
from sklearn.metrics import multilabel_confusion_matrix as ML_matrix
from sklearn.metrics import precision_recall_fscore_support as score_multi
from sklearn.metrics import roc_auc_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report

import os
import pickle
from datetime import datetime
import pandas as pd

def get_full_df(path):
    bg_dfs = []
    rl_dfs = []
    for file in os.listdir(path):
        if "corr" in file and "background" in file:
            bg_dfs.append(pd.read_csv(os.path.join(path, file)))
        elif "corr" in file and "relay" in file:
            rl_dfs.append(pd.read_csv(os.path.join(path, file)))
    
    bg_df = pd.concat(bg_dfs, ignore_index=True)
    rl_df = pd.concat(rl_dfs, ignore_index=True)
    
    bg_df['label'] = 0
    rl_df['label'] = 1
    
    return pd.concat([bg_df, rl_df])


def get_corr_features(include_attack=True, full_dataset=True, fifty_pcaps=True):
    if full_dataset:
        dataset_path = "ds11"
    else:
        dataset_path = "ds4"
        
    if fifty_pcaps:
        pcap_path = "50"
    else:
        pcap_path = "20"
        
        
    if include_attack:
        test_path = f"../content/{dataset_path}/corr_attack_{pcap_path}/test"
        train_path = f"../content/{dataset_path}/corr_attack_{pcap_path}/train"
        val_path = f"../content/{dataset_path}/corr_attack_{pcap_path}/val"
    else:
        test_path = f"../content/{dataset_path}/corr_clean_{pcap_path}/test"
        train_path = f"../content/{dataset_path}/corr_clean_{pcap_path}/train"
        val_path = f"../content/{dataset_path}/corr_clean_{pcap_path}/val"
        
    
    train_corr_df = get_full_df(train_path)
    test_corr_df = get_full_df(test_path)
    val_corr_df = get_full_df(val_path)
    
    train_corr_df['pcap_nb'] = train_corr_df['pcap_nb'].map((lambda x: x.split("/")[-1]))
    test_corr_df['pcap_nb'] = test_corr_df['pcap_nb'].map((lambda x: x.split("/")[-1]))
    val_corr_df['pcap_nb'] = val_corr_df['pcap_nb'].map((lambda x: x.split("/")[-1]))
    
    return train_corr_df, test_corr_df, val_corr_df

def get_slt_features(include_attack=True, full_dataset=True):
    if full_dataset:
        dataset_path = "ds11"
    else:
        dataset_path = "ds4"
    
    if include_attack:
        train_wrtt_df = pd.read_parquet(f"../content/{dataset_path}/ds4_wrtt/train/ds4_wrtt.parquet")
        test_wrtt_df = pd.read_parquet(f"../content/{dataset_path}/ds4_wrtt/test/ds4_wrtt.parquet")
        val_wrtt_df = pd.read_parquet(f"../content/{dataset_path}/ds4_wrtt/val/ds4_wrtt.parquet")
    else:
        train_wrtt_df = pd.read_parquet(f"../content/{dataset_path}/ds4_wrtt_clean/train/ds4_wrtt_clean.parquet")
        test_wrtt_df = pd.read_parquet(f"../content/{dataset_path}/ds4_wrtt_clean/test/ds4_wrtt_clean.parquet")
        val_wrtt_df = pd.read_parquet(f"../content/{dataset_path}/ds4_wrtt_clean/val/ds4_wrtt_clean.parquet")

    # Rename to match others
    train_wrtt_df.rename(columns={'pcap': 'pcap_nb'}, inplace=True)
    test_wrtt_df.rename(columns={'pcap': 'pcap_nb'}, inplace=True)
    val_wrtt_df.rename(columns={'pcap': 'pcap_nb'}, inplace=True)

    # Remove uncessary rtt feature
    train_wrtt_df.drop(columns=['rtt'], inplace=True)
    test_wrtt_df.drop(columns=['rtt'], inplace=True)
    val_wrtt_df.drop(columns=['rtt'], inplace=True)
    
    return train_wrtt_df, test_wrtt_df, val_wrtt_df

def get_pd(file_path):
    if "parquet" in file_path:
        return pd.read_parquet(file_path)
    else:
        return pd.read_csv(file_path)

def get_k_features(include_attack=True, full_dataset=True):
    if full_dataset:
        dataset_path = "ds11"
        extension = "parquet"
    else:
        dataset_path = "ds4"
        extension = "csv"
        
    if include_attack:
        train_df = get_pd(f"../content/{dataset_path}/ds11v2rq1_3way_20pkts_attackv3/train/k_features_d11v2_3way_20pktsv2.{extension}")
        test_df = get_pd(f"../content/{dataset_path}/ds11v2rq1_3way_20pkts_attackv3/test/k_features_d11v2_3way_20pktsv2.{extension}")
        val_df = get_pd(f"../content/{dataset_path}/ds11v2rq1_3way_20pkts_attackv3/val/k_features_d11v2_3way_20pktsv2.{extension}")
        
        train_df['label'] = train_df['label'].replace({1: 0})
        val_df['label'] = val_df['label'].replace({1: 0})
        test_df['label'] = test_df['label'].replace({1: 0})

        train_df['label'] = train_df['label'].replace({2: 1})
        val_df['label'] = val_df['label'].replace({2: 1})
        test_df['label'] = test_df['label'].replace({2: 1})
    else:
        train_df = get_pd(f"../content/{dataset_path}/ds11v2rq1_3way_20pkts_cleanv3/train/k_features_d11v2_3way_20pktsv2.{extension}")
        test_df = get_pd(f"../content/{dataset_path}/ds11v2rq1_3way_20pkts_cleanv3/test/k_features_d11v2_3way_20pktsv2.{extension}")
        val_df = get_pd(f"../content/{dataset_path}/ds11v2rq1_3way_20pkts_cleanv3/val/k_features_d11v2_3way_20pktsv2.{extension}")
        
        train_df['label'] = train_df['label'].replace({1: 0})
        val_df['label'] = val_df['label'].replace({1: 0})
        test_df['label'] = test_df['label'].replace({1: 0})

        train_df['label'] = train_df['label'].replace({2: 1})
        val_df['label'] = val_df['label'].replace({2: 1})
        test_df['label'] = test_df['label'].replace({2: 1})
    
    # Rename to match others
    train_df.rename(columns={'pcap': 'pcap_nb'}, inplace=True)
    test_df.rename(columns={'pcap': 'pcap_nb'}, inplace=True)
    val_df.rename(columns={'pcap': 'pcap_nb'}, inplace=True)
    
    return train_df, test_df, val_df

def get_dataset(dataset_name, include_attack = True, full_dataset = True, fifty_pcaps = True):
    """Return features based on name, include attack to be implemented """
    if dataset_name == "slt":
        return get_slt_features(include_attack)
    if dataset_name == "corr":
        return get_corr_features(include_attack, full_dataset, fifty_pcaps)
    if dataset_name == "k":
        return get_k_features(include_attack)

# Use to decide which experiment to run
def run_experiment_setting(include_attack, experiment_number, full_dataset, fifty_pcaps):
    # K-Fingerprinting + Corr features
    if experiment_number == 0:
        train_corr_df, test_corr_df, val_corr_df = get_dataset("corr", False, full_dataset, fifty_pcaps)
        train_k_df, test_k_df, val_k_df = get_dataset("k", True)
        
        train_df = pd.merge(train_k_df, train_corr_df.drop(columns=['label']), on=['pcap_nb', 'conn'])
        test_df = pd.merge(test_k_df, test_corr_df.drop(columns=['label']), on=['pcap_nb', 'conn'])
        val_df = pd.merge(val_k_df, val_corr_df.drop(columns=['label']), on=['pcap_nb', 'conn'])
        
    elif experiment_number == 1:
        # Corr only
        train_df, test_df, val_df = get_dataset("corr", include_attack=include_attack, full_dataset=full_dataset, fifty_pcaps=fifty_pcaps)
        
    elif experiment_number == 2:
        # K Fingerprinting Only
        train_df, test_df, val_df = get_dataset("k", include_attack)

    elif experiment_number == 3:
        # Arxiv Only
        train_df, test_df, val_df = get_dataset("slt", include_attack)
        
        train_df = train_df.filter(regex="^(?:(?=.*(?:_2pkt|_4pkt|_8pkt|label|conn|pcap_nb)).+|(?=.*_16pkt)(?=.*bidirectional).+)$")
        val_df = val_df.filter(regex="^(?:(?=.*(?:_2pkt|_4pkt|_8pkt|label|conn|pcap_nb)).+|(?=.*_16pkt)(?=.*bidirectional).+)$")
        test_df = test_df.filter(regex="^(?:(?=.*(?:_2pkt|_4pkt|_8pkt|label|conn|pcap_nb)).+|(?=.*_16pkt)(?=.*bidirectional).+)$")
        
        
        
    test_df = test_df.drop(columns=['conn', 'pcap_nb'], axis=1)
    train_df = train_df.drop(columns=['conn', 'pcap_nb'], axis=1)
    val_df = val_df.drop(columns=['conn', 'pcap_nb'], axis=1)
        
    return test_df, train_df, val_df

ag_args_fit = {'num_gpus': 1}  # Allocate 1 GPU
    
def train_main(data_df, val_df, target_col, presets='medium_quality'):
	agdir = os.getcwd()+'/AGmodels/'
	if not os.path.exists(agdir):
		os.system("mkdir "+agdir)

	if presets == 'medium_quality':
		predictor = task(label=target_col, path=agdir, eval_metric='f1').fit(train_data=data_df, tuning_data=val_df, verbosity=3, ag_args_fit=ag_args_fit, presets='medium_quality')
	else:
		all_data = pd.concat([data_df, val_df])
		predictor = task(label=target_col, path=agdir, eval_metric='f1').fit(train_data=all_data, verbosity=3, ag_args_fit=ag_args_fit, presets='best_quality')
     
	return predictor


def test_main(xtest, ytest, pred, testdf, traindf, calcftimpo=False):
	modelperf = pred.leaderboard(testdf, silent= True)
	print("[*]Model performance breakdown on Test data:")
	print(modelperf)
	ypred = pred.predict(xtest)
	ypredproba = pred.predict_proba(xtest)
	perf = pred.evaluate_predictions(y_true=ytest, y_pred=ypred, auxiliary_metrics= True)
	print("[*]Predictions: ", ypred)
	print("[*]Confidence in predictions:\n")
	print(pd.DataFrame(ypredproba, columns=pred.class_labels))
	# Each model score
	print("Perf: ", perf)
	print(classification_report(ytest, ypred, output_dict=True))

	print("Getting confusion matrix.....")
	cmatrix = confusion_matrix(ytest, ypred).ravel().tolist()
	print(cmatrix)
	auc_score = roc_auc_score(ytest, ypredproba.iloc[:, 1])
	print("AUC score for best model: ", auc_score)

	if calcftimpo:
		ftimpo = None
		ftimpo = pred.feature_importance(traindf)
		print("Feature Importance on test data: ", ftimpo)
	else:
		ftimpo = None
	bestmodel = pred.model_best
	# Find mistakes
	misclassified = xtest[ypred != ytest].copy()
	misclassified['true_label'] = ytest[ypred != ytest]
	misclassified['predicted_label'] = ypred[ypred != ytest]
	return modelperf, ftimpo, cmatrix, ypredproba, bestmodel, perf, auc_score, misclassified

def main():
    # Create timestamp and results directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_results_dir = f'fifty_pcaps_experiment_results_{timestamp}'
    os.makedirs(base_results_dir, exist_ok=True)

    # Define experiment configurations
    configurations = [
        False, True
    ]

    results_summary = []

    for use_fifty_pcaps in configurations:
        exp_name = f'{"50_pcaps" if use_fifty_pcaps else "20_pcaps"}_setting'
        print(f"\nRunning experiment: {exp_name}")
        
        # Create directory for this specific experiment
        exp_dir = os.path.join(base_results_dir, exp_name)
        os.makedirs(exp_dir, exist_ok=True)
        
        # Get the data splits
        test_df, train_df, val_df = run_experiment_setting(True, 0, full_dataset=True, fifty_pcaps=use_fifty_pcaps)
        
        
        # Reset indices
        train_df = train_df.reset_index(drop=True)
        val_df = val_df.reset_index(drop=True)
        test_df = test_df.reset_index(drop=True)
        
        # Train model
        predictor = train_main(train_df, val_df, "label", "medium_quality")
        
        # Prepare test data
        x_test = test_df.drop(columns=['label'])
        y_test = test_df['label']
        
        # Run testing
        res1, fimp1, cmatrix, ypred_proba, bestmodel, perf, auc_score, mistakes = test_main(
            x_test, y_test, predictor, test_df, train_df, True
        )
        
        # Save results
        results = {
            'predictor': predictor,
            'results': res1,
            'feature_importance': fimp1, 
            'confusion_matrix': cmatrix,
            'predictions_proba': ypred_proba,
            'best_model': bestmodel,
            'performance': perf,
            'auc_score': auc_score,
            'mistakes': mistakes
        }
        
        # Save DataFrames
        test_df.to_csv(os.path.join(exp_dir, 'test_data.csv'), index=False)
        train_df.to_csv(os.path.join(exp_dir, 'train_data.csv'), index=False)
        val_df.to_csv(os.path.join(exp_dir, 'val_data.csv'), index=False)
        res1.to_csv(os.path.join(exp_dir, 'results.csv'), index=True)
        fimp1.to_csv(os.path.join(exp_dir, 'feature_importance.csv'), index=True)
        
        # Save full results
        with open(os.path.join(exp_dir, 'full_results.pkl'), 'wb') as f:
            pickle.dump(results, f)
            
        print("=" * 15 + exp_name + "=" * 15)
        f1 = perf['f1']
        precision = perf['precision']
        recall = perf['recall']
        
        print(f"f1: {100 * f1:.4f}")
        print(f"precision: {100 * precision:.4f}")
        print(f"recall: {100 * recall:.4f}")
        
        TN = cmatrix[0]  # True Negatives
        FP = cmatrix[1]  # False Positives
        FN = cmatrix[2]  # False Negatives 
        TP = cmatrix[3]  # True Positives
        
        # Calculate rates
        FPR = (FP / (FP + TN))*100 if (FP + TN) > 0 else 0
        FNR = (FN / (FN + TP))*100 if (FN + TP) > 0 else 0

        print(f"False Positive Rate (FPR): {FPR:.4f} %")
        print(f"False Negative Rate (FNR): {FNR:.4f} %")
        
        # Save experiment summary
        exp_summary = {
            'experiment': exp_name,
            'use_fifty_pcaps': use_fifty_pcaps,
            'auc_score': auc_score,
            'best_model': bestmodel,
            'timestamp': timestamp,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'FPR(%)': f"{FPR:.4f}"
        }
        
        results_summary.append(exp_summary)

    # Save overall summary
    summary_df = pd.DataFrame(results_summary)
    summary_df.to_csv(os.path.join(base_results_dir, 'experiments_summary.csv'), index=False)

    print("\nAll experiments completed!")
    print(f"Results saved in: {base_results_dir}")

if __name__ == "__main__":
    main()