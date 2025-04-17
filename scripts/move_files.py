import os
import csv
import shutil
import argparse

def move_files(input_folder, output_folder, csv_file):
    """
    Move files from input folder to output folder based on names in the first column of a CSV file.
    
    Args:
        input_folder: The source folder containing files to be moved
        output_folder: The destination folder where files will be moved to
        csv_file: Path to the CSV file containing the list of files to move in the first column
    """
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")
    
    # Read file names from the CSV
    files_to_move = []
    try:
        with open(csv_file, 'r', newline='') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                if row and row[1] == "test":  # Check if row is not empty
                    files_to_move.append(row[0])
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    print(f"Found {len(files_to_move)} files to move in the CSV file")
    
    # Move each file
    moved_count = 0
    errors = []
    
    for file_name in files_to_move:
        source_path = os.path.join(input_folder, file_name)
        dest_path = os.path.join(output_folder, file_name)
        
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
    print(f"Total files processed: {len(files_to_move)}")
    print(f"Successfully moved: {moved_count}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nError details:")
        for error in errors:
            print(f"- {error}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Move files listed in a CSV to a destination folder")
    parser.add_argument("--input", required=True, help="Input folder path")
    parser.add_argument("--output", required=True, help="Output folder path")
    parser.add_argument("--csv", required=True, help="CSV file with file names in first column")
    
    args = parser.parse_args()
    
    move_files(args.input, args.output, args.csv)
