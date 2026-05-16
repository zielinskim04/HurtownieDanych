import pandas as pd

def filter_transactions_by_year(input_file, output_file):
    # load the CSV file
    df = pd.read_csv(input_file)
    
    # convert 'Data_transakcji' column to datetime objects
    df['Data_transakcji'] = pd.to_datetime(df['Data_transakcji'], errors='coerce')
    
    # drop rows where can't parse date
    df = df.dropna(subset=['Data_transakcji'])
    
    # keep only rows between 2005 and 2025 (inclusive)
    filtered_df = df[(df['Data_transakcji'].dt.year >= 2005) & (df['Data_transakcji'].dt.year <= 2025)]
    
    # save result to csv
    filtered_df.to_csv(output_file, index=False)
    
    print(f"Filtering complete. Original rows: {len(df)}, Filtered rows: {len(filtered_df)}")
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    INPUT_CSV = 'deweloperuch_ceny_w_polsce.csv'
    OUTPUT_CSV = 'deweloperuch_transactions_daterange.csv'
    
    filter_transactions_by_year(INPUT_CSV, OUTPUT_CSV)