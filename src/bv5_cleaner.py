import pandas as pd

# Define the input and output file paths
input_file_path = 'data/BV5-All-report-May-10-2025-to-May-22-2025.csv'
output_file_path = 'data/clean_bv5_global.csv'

print(f"Starting BV5 data cleaning process for: {input_file_path}")

try:
    # Read the CSV file
    df = pd.read_csv(input_file_path)
    print(f"Original BV5 data ({input_file_path}) loaded successfully. Rows: {len(df)}")

    # Store the original number of rows for comparison
    original_row_count = len(df)

    # Remove rows where the 'Country' column is NaN or empty
    # It's good practice to also check for empty strings if that's a possibility
    df_cleaned = df.dropna(subset=['Country'])
    # If 'Country' might contain empty strings like '' which are not NaN:
    # df_cleaned = df[df['Country'].notna() & (df['Country'] != '')]


    cleaned_row_count = len(df_cleaned)
    rows_removed = original_row_count - cleaned_row_count

    print(f"'Country' column cleaned. Rows removed: {rows_removed}. Rows remaining: {cleaned_row_count}")

    # Save the cleaned data to a new CSV file
    df_cleaned.to_csv(output_file_path, index=False)
    print(f"Cleaned BV5 data saved to: {output_file_path}")

    print("\n--- BV5 Cleaning Summary ---")
    print(f"Input file: {input_file_path}")
    print(f"Output file: {output_file_path}")
    print(f"Original rows: {original_row_count}")
    print(f"Rows removed (empty 'Country'): {rows_removed}")
    print(f"Cleaned rows: {cleaned_row_count}")
    print("BV5 data cleaning process completed successfully.")

except FileNotFoundError:
    print(f"Error: The file {input_file_path} was not found. Please ensure the file exists in the 'data' directory.")
except Exception as e:
    print(f"An error occurred during the BV5 cleaning process: {e}") 