import pandas as pd
import os
from config import ENTRY_THRESHOLD, EXIT_THRESHOLD, INSTRUMENT

def calculate_ibs():
    # Define input and output paths
    input_path = os.path.join('data', f'{INSTRUMENT}.csv')
    output_dir = 'outputs'
    output_path = os.path.join(output_dir, 'ibs_indicator.csv')

    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Reading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Clean column names (remove surrounding whitespace)
    df.columns = df.columns.str.strip()

    # Ensure required columns exist
    required_cols = ['High', 'Low', 'Close', 'Open']
    for col in required_cols:
        if col not in df.columns:
            # Try lowercase if title case not found
            if col.lower() in df.columns:
                df.rename(columns={col.lower(): col}, inplace=True)
            else:
                print(f"Error: Column '{col}' not found in input data.")
                return

    # Parse datetime if available
    if 'Date' in df.columns:
        df['datetime'] = pd.to_datetime(df['Date'], utc=True)
    elif df.index.name == 'Date':
        df['datetime'] = pd.to_datetime(df.index, utc=True)
    else:
        # Fallback to first column
        df['datetime'] = pd.to_datetime(df.iloc[:, 0], utc=True)

    # Calculate IBS
    # Formula: IBS = (Close - Low) / (High - Low)
    # Handle division by zero (if High == Low)
    df['denominator'] = df['High'] - df['Low']
    
    # Avoid division by zero by replacing 0 with NaN or a small epsilon, 
    # but practically if High == Low, IBS is essentially undefined or can be considered 0.5 or 0 depending on interpretation.
    # Here we will set it to 0.5 (neutral) if range is 0 to avoid errors, or just let pandas handle infs if preferred.
    # Let's handle it safely.
    
    df['ibs_value'] = (df['Close'] - df['Low']) / df['denominator']
    
    # Fill NaN/Inf results (where High == Low) with 0.5 or 0
    df['ibs_value'] = df['ibs_value'].fillna(0.0)

    # Determine Tags based on Thresholds
    # tag = 'entry' if ibs > ENTRY_THRESHOLD
    # tag = 'exit' if ibs < EXIT_THRESHOLD
    # else empty string or None
    def get_tag(ibs):
        if ibs < ENTRY_THRESHOLD:
            return 'entry'
        elif ibs > EXIT_THRESHOLD:
            return 'exit'
        else:
            return None

    df['tag'] = df['ibs_value'].apply(get_tag)

    # Select columns for output
    # datetime, open, close, high, low, ibs_value, tag
    output_columns = ['datetime', 'Open', 'Close', 'High', 'Low', 'ibs_value', 'tag']
    
    # Rename columns to lowercase for the output as requested ("datetime, open, close, hihg, low...... and ibs_value")
    # Note: user wrote "hihg", assuming "high"
    
    result_df = df[output_columns].copy()
    result_df.columns = ['datetime', 'open', 'close', 'high', 'low', 'ibs_value', 'tag']

    print(f"IBS calculated. Sample:\n{result_df[['datetime', 'ibs_value']].head()}")

    # Save to CSV
    print(f"Saving to {output_path}...")
    result_df.to_csv(output_path, index=False)
    print("Done.")

if __name__ == "__main__":
    calculate_ibs()
