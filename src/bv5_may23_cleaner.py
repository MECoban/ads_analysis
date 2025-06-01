import pandas as pd

# Define the input and output file paths
input_file_path = 'data/BV5-May-23-2025-to-May-29-2025.csv'
output_file_path = 'data/clean_bv5_may23_global.csv'

print(f"Starting BV5 May 23-29 data cleaning process for: {input_file_path}")

try:
    # Read the CSV file
    df = pd.read_csv(input_file_path)
    print(f"Original BV5 May 23-29 data ({input_file_path}) loaded successfully. Rows: {len(df)}")

    # Store the original number of rows for comparison
    original_row_count = len(df)

    # Remove rows where the 'Country' column is NaN or empty
    df_cleaned = df.dropna(subset=['Country'])
    df_cleaned = df_cleaned[df_cleaned['Country'] != ''] # Ensure empty strings are also removed

    cleaned_row_count = len(df_cleaned)
    rows_removed = original_row_count - cleaned_row_count

    # Save the cleaned data
    df_cleaned.to_csv(output_file_path, index=False)
    print(f"BV5 May 23-29 data cleaned successfully. Rows removed: {rows_removed}")
    print(f"Cleaned BV5 May 23-29 data saved to: {output_file_path}. Rows: {cleaned_row_count}")

except FileNotFoundError:
    print(f"Error: The file {input_file_path} was not found.")
except pd.errors.EmptyDataError:
    print(f"Error: The file {input_file_path} is empty.")
except Exception as e:
    print(f"An unexpected error occurred during BV5 May 23-29 data cleaning: {e}") 