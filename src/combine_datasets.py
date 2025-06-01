import pandas as pd
import os

# Define file paths
DATA_DIR = 'data'
OUTPUT_DIR = 'data' # Save combined files in the same data directory

# Files for Period 1 (10-22 Mayıs)
file_p1_1 = os.path.join(DATA_DIR, 'clean_global.csv') # BV2 10-22 May (has 'Ad Set Name')
file_p1_2 = os.path.join(DATA_DIR, 'clean_bv5_global.csv') # BV5 10-22 May (has 'Ad Set Name')
output_file_p1 = os.path.join(OUTPUT_DIR, 'combined_period1_10_22_may.csv')

# Files for Period 2 (23-29 Mayıs)
file_p2_1 = os.path.join(DATA_DIR, 'clean_tt_bv2_may23_global.csv') # TT BV2 23-29 May (has 'Campaign name')
file_p2_2 = os.path.join(DATA_DIR, 'clean_bv5_may23_global.csv')    # BV5 23-29 May (has 'Campaign name')
output_file_p2 = os.path.join(OUTPUT_DIR, 'combined_period2_23_29_may.csv')

UNIVERSAL_ID_COLUMN = 'Universal_Campaign_ID'

def combine_period_data(file1_path, file1_id_col, file2_path, file2_id_col, output_path):
    r"""Loads two CSVs, standardizes their campaign/ad set ID column, concatenates, and saves."""
    print(f"Processing period for output: {output_path}")
    try:
        df1 = pd.read_csv(file1_path)
        print(f"Loaded {file1_path} with {len(df1)} rows. Columns: {list(df1.columns)}")
        if file1_id_col in df1.columns:
            df1.rename(columns={file1_id_col: UNIVERSAL_ID_COLUMN}, inplace=True)
            print(f"Renamed '{file1_id_col}' to '{UNIVERSAL_ID_COLUMN}' in first DataFrame.")
        else:
            print(f"Warning: ID column '{file1_id_col}' not found in {file1_path}. Adding placeholder if needed.")
            if UNIVERSAL_ID_COLUMN not in df1.columns: df1[UNIVERSAL_ID_COLUMN] = "Unknown_ID_DF1"

        df2 = pd.read_csv(file2_path)
        print(f"Loaded {file2_path} with {len(df2)} rows. Columns: {list(df2.columns)}")
        if file2_id_col in df2.columns:
            df2.rename(columns={file2_id_col: UNIVERSAL_ID_COLUMN}, inplace=True)
            print(f"Renamed '{file2_id_col}' to '{UNIVERSAL_ID_COLUMN}' in second DataFrame.")
        else:
            print(f"Warning: ID column '{file2_id_col}' not found in {file2_path}. Adding placeholder if needed.")
            if UNIVERSAL_ID_COLUMN not in df2.columns: df2[UNIVERSAL_ID_COLUMN] = "Unknown_ID_DF2"
        
        # Ensure all essential columns are present before concat, fill with NA or 0 if necessary
        # This is a simplified check; a more robust solution would align all columns.
        # For now, assuming core metric columns are largely consistent due to prior cleaning.

        combined_df = pd.concat([df1, df2], ignore_index=True, sort=False)
        print(f"Combined DataFrame shape: {combined_df.shape}")
        
        # Save the combined data
        combined_df.to_csv(output_path, index=False)
        print(f"Successfully combined and saved to {output_path}")
        print(f"Columns in combined file: {list(combined_df.columns)}")

    except FileNotFoundError as e:
        print(f"Error: One of the files not found. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    print("---")

if __name__ == "__main__":
    print("Starting dataset combination process...")
    
    # Create output directory if it doesn't exist (though it should be 'data')
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    # Process Period 1
    combine_period_data(file_p1_1, 'Ad Set Name', file_p1_2, 'Ad Set Name', output_file_p1)
    
    # Process Period 2
    combine_period_data(file_p2_1, 'Campaign name', file_p2_2, 'Campaign name', output_file_p2)
    
    print("Dataset combination process finished.") 