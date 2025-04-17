import pandas as pd
import os


for i in ['train', 'test', 'val']:
    BASE_PATH = f"content/subset_features_03_18/{i}/"
    file_paths = os.listdir(BASE_PATH)

    bg_paths = [BASE_PATH + f for f in file_paths if ".csv" and "background" in f]
    relayed_paths = [BASE_PATH + f for f in file_paths if ".csv" and "relayed" in f]

    print(bg_paths)

    bg_merged_df = pd.concat([pd.read_csv(f) for f in bg_paths], ignore_index = True)
    relayed_merged_df = pd.concat([pd.read_csv(f) for f in relayed_paths], ignore_index = True)

    bg_merged_df['label'] = 0
    relayed_merged_df['label'] = 1

    merged_df = pd.concat([bg_merged_df, relayed_merged_df], ignore_index = True)
    merged_df.to_csv(f'content/subset_features_03_18/{i}/all_features.csv', index = False)



