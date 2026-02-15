"""
import_data.py

Download financial data using yfinance.
"""

import yfinance as yf
import os

def download_data(symbol, period='1y', start=None, end=None, interval='1d', save_path=None):
    print(f"Downloading data for {symbol}...")
    ticker = yf.Ticker(symbol)
    
    # Check if period is needed or date range
    if start and end and not period:
        # User provided start/end, let's use them
        df = ticker.history(start=start, end=end, interval=interval)
    elif period:
        df = ticker.history(period=period, interval=interval)
    else:
        # Default
        df = ticker.history(period='1y', interval=interval)

    if df.empty:
        print(f"Warning: No data found for {symbol}.")
        return df

    if save_path:
        d = os.path.dirname(save_path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        df.to_csv(save_path)
        print(f"Saved {len(df)} rows to {save_path}")
        
    return df

if __name__ == '__main__':
    # Test
    out_path = os.path.join('data', 'test_data.csv')
    df = download_data('SPY', period='1mo', save_path=out_path)
    print(df.tail())
