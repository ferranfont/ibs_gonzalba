"""
impot_data.py

Download SPY daily data using yfinance (interval = 1d).

Usage:
    pip install yfinance
    python impot_data.py

The script saves the latest data to `data/spy.csv` by default.
"""

import yfinance as yf
import os


def download_spy(period='1y', start=None, end=None, interval='1d', save_path=None):

    ticker = yf.Ticker("SPY")
    if period is not None:
        df = ticker.history(period=period, interval=interval)
    else:
        df = ticker.history(start=start, end=end, interval=interval)

    if save_path:
        d = os.path.dirname(save_path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        df.to_csv(save_path)
    return df


if __name__ == '__main__':
    out_path = os.path.join('data', 'spy.csv')
    df = download_spy(period='1y', interval='1d', save_path=out_path)
    print(f"Saved {len(df)} rows to {out_path}")
    print(df.tail())
