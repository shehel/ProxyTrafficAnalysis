import os
import csv
import shutil
import argparse

REQUIRED_FILES = ['mixed_02_01_2025_06_08_10_low', 'mixed_03_01_2025_13_59_38_medium', 'mixed_01_01_2025_04_30_20_low', 'mixed_27_12_2024_17_48_05_medium', 'mixed_29_12_2024_03_36_31_medium', 'mixed_31_12_2024_09_16_08_low', 'mixed_05_01_2025_05_06_52_medium', 'mixed_31_12_2024_04_59_41_medium', 'mixed_05_01_2025_08_58_05_low', 'mixed_03_01_2025_15_45_57_high', 'mixed_25_12_2024_19_43_12_high', 'mixed_05_01_2025_02_54_54_low', 'mixed_27_12_2024_19_34_41_medium', 'mixed_29_12_2024_13_32_22_low', 'mixed_27_12_2024_01_45_20_high', 'mixed_05_01_2025_01_04_28_medium', 'mixed_02_01_2025_06_09_38_low', 'mixed_01_01_2025_10_54_44_low', 'mixed_31_12_2024_06_12_23_medium', 'mixed_04_01_2025_02_50_14_medium', 'mixed_31_12_2024_13_53_34_medium', 'mixed_26_12_2024_09_50_07_medium', 'mixed_03_01_2025_17_53_58_low', 'mixed_01_01_2025_17_44_52_low', 'mixed_02_01_2025_04_49_19_medium', 'mixed_29_12_2024_22_05_16_medium', 'mixed_29_12_2024_11_24_11_high', 'mixed_29_12_2024_09_16_06_medium']

def move_files(BASE_PATH, dest_path):
    """
    Move files from input folder to output folder based on names in the first column of a CSV file.
    
    Args:
        input_folder: The source folder containing files to be moved
        output_folder: The destination folder where files will be moved to
    """
    errors = []
    for file_name in REQUIRED_FILES:
        source_path = os.path.join(BASE_PATH, file_name)
        
        if os.path.exists(source_path):
            try:
                # Create directories in the destination if they don't exist
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Move the file
                shutil.copytree(source_path, dest_path)
                moved_count += 1
                print(f"Moved: {file_name}")
            except Exception as e:
                errors.append(f"Error moving {file_name}: {e}")
        else:
            errors.append(f"Source file not found: {source_path}")
    
    # Summary
    print(f"\nSummary:")
    print(f"Total files processed: {len(REQUIRED_FILES)}")
    print(f"Successfully moved: {moved_count}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nError details:")
        for error in errors:
            print(f"- {error}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Move files listed in a CSV to a destination folder")
    parser.add_argument("--base_path", required=True, help="Base path with all files")
    parser.add_argument("--output", required=True, help="Output path")
    
    args = parser.parse_args()
    
    move_files(args.input, args.output)
