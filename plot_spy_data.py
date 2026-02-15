import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
from config import ENTRY_THRESHOLD, EXIT_THRESHOLD, MIN_LAST_DAYS

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def plot_spy_chart():
    # Load data
    file_path = os.path.join('data', 'spy.csv')
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    print(f"Reading data from {file_path}...")
    # Handle spaces in CSV with skipinitialspace
    df = pd.read_csv(file_path, skipinitialspace=True)
    # Clean column names (remove surrounding whitespace just in case)
    df.columns = df.columns.str.strip()
    
    # Process date
    # The file has a 'Date' column: 2025-02-14 00:00:00-05:00
    if 'Date' in df.columns:
        # data often comes with timezone info, convert to UTC or coerce
        df['timestamp'] = pd.to_datetime(df['Date'], utc=True)
    else:
        print(f"Columns found: {df.columns}")
        # Check if index has name 'Date'
        if df.index.name == 'Date':
             df['timestamp'] = pd.to_datetime(df.index, utc=True)
        else:
             print("Warning: 'Date' column not found, attempting to parse first column.")
             df['timestamp'] = pd.to_datetime(df.iloc[:, 0], utc=True)
    
    print(f"Timestamp dtype: {df['timestamp'].dtype}")


    # Create index for x-axis to skip gaps (weekends) - mimicking the requested style
    df = df.reset_index(drop=True)
    df['index'] = df.index

    # Create figure
    # Using make_subplots even for single plot to match the "inspiration" structure
    fig = make_subplots(
        rows=1, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03
    )

    # Calculate IBS and Filter Signals
    # Formula: IBS = (Close - Low) / (High - Low)
    # This formula is independent of candle color (Open vs Close).
    # It purely measures the position of the Close relative to the Day's Range.
    df['high_low_diff'] = df['High'] - df['Low']
    # Avoid division by zero
    df['ibs'] = df.apply(
        lambda row: (row['Close'] - row['Low']) / row['high_low_diff'] if row['high_low_diff'] != 0 else 0, 
        axis=1
    )

    # Calculate Min Last Days (Rolling Low)
    df['min_last_days'] = df['Low'].rolling(window=MIN_LAST_DAYS).min()

    # Filter rows for Entry Signals
    # Logic: IBS < ENTRY_THRESHOLD (0.2) AND Low <= min_last_days (Current Low is the 10-day low)
    # Note: rolling().min() includes current row, so Low <= min is Low == min
    entry_signals = df[(df['ibs'] < ENTRY_THRESHOLD) & (df['Low'] <= df['min_last_days'])].copy()
    entry_signals['tag'] = 'entry'
    
    # Filter rows for Exit Signals
    # Logic: IBS > EXIT_THRESHOLD (0.6)
    # User's request mention "IBS > MIN_LAST_DAYS" was interpreted as "IBS > EXIT_THRESHOLD" since IBS is 0-1.
    exit_signals = df[df['ibs'] > EXIT_THRESHOLD].copy()
    exit_signals['tag'] = 'exit'

    print(f"Found {len(entry_signals)} Entry signals (IBS < {ENTRY_THRESHOLD} & Low <= 10d Low)")
    print(f"Found {len(exit_signals)} Exit signals (IBS > {EXIT_THRESHOLD})")

    # Combine and save signals to CSV
    all_signals = pd.concat([entry_signals, exit_signals]).sort_index()

    outputs_dir = 'outputs'
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir)
    signals_output_path = os.path.join(outputs_dir, 'entry_signals.csv')
    
    # Save relevant columns
    cols_to_save = ['timestamp', 'Open', 'High', 'Low', 'Close', 'ibs', 'tag']
    # Add index to cols if needed, but timestamp is better. timestamp is already in df.
    
    all_signals[cols_to_save].to_csv(signals_output_path, index=False)
    print(f"All signals saved to: {signals_output_path}")

    # Add Price trace (Candlestick)
    trace_price = go.Candlestick(
        x=df['index'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='SPY',
        increasing=dict(line=dict(color='grey', width=1), fillcolor='green'),
        decreasing=dict(line=dict(color='grey', width=1), fillcolor='red'),
        opacity=0.9
    )
    fig.add_trace(trace_price, row=1, col=1)

    # Add Min Last Days Line
    trace_min = go.Scatter(
        x=df['index'],
        y=df['min_last_days'],
        mode='lines',
        name=f'Min Last {MIN_LAST_DAYS} Days',
        line=dict(color='blue', width=2),
        hovertemplate='<b>Min Last Days</b>: %{y:.2f}<extra></extra>'
    )
    fig.add_trace(trace_min, row=1, col=1)

    # Add Green Dots for Entry Signals (Below Low)
    if not entry_signals.empty:
        trace_entry = go.Scatter(
            x=entry_signals['index'],
            y=entry_signals['Low'] * 0.999, # Slightly below Low
            mode='markers',
            name=f'Entry (IBS < {ENTRY_THRESHOLD} & Low=Min)',
            marker=dict(
                color='green',
                size=8,
                symbol='circle'
            ),
            hovertemplate='<b>Entry Signal</b><br>Date: %{text}<br>Price: %{y:.2f}<br>IBS: %{customdata:.2f}<extra></extra>',
            text=entry_signals['timestamp'].dt.strftime('%Y-%m-%d'),
            customdata=entry_signals['ibs']
        )
        fig.add_trace(trace_entry, row=1, col=1)

    # Add Red Dots for Exit Signals (Above High)
    if not exit_signals.empty:
        trace_exit = go.Scatter(
            x=exit_signals['index'],
            y=exit_signals['High'] * 1.001, # Slightly above High
            mode='markers',
            name=f'Exit (IBS > {EXIT_THRESHOLD})',
            marker=dict(
                size=8,
                symbol='circle',
                color='red'
            ),
            hovertemplate='<b>Exit Signal</b><br>Date: %{text}<br>Price: %{y:.2f}<br>IBS: %{customdata:.2f}<extra></extra>',
            text=exit_signals['timestamp'].dt.strftime('%Y-%m-%d'),
            customdata=exit_signals['ibs']
        )
        fig.add_trace(trace_exit, row=1, col=1)



    # Make the rangeslider invisible to maintain the "inspired" usage of x-axis
    fig.update_layout(xaxis_rangeslider_visible=False)

    # Configure x-axis ticks
    # To show dates on X axis instead of integer index
    num_ticks = 30
    tick_indices = [int(i) for i in range(0, len(df), max(1, len(df)//num_ticks))]
    tick_vals = df.iloc[tick_indices]['index']
    # Format date: YYYY-MM-DD
    tick_text = df.iloc[tick_indices]['timestamp'].dt.strftime('%Y-%m-%d')

    fig.update_xaxes(
        tickmode='array', tickvals=tick_vals, ticktext=tick_text,
        tickangle=-45, showgrid=False,
        showline=True, linewidth=1, linecolor='#d3d3d3',
        row=1, col=1
    )

    # Configure layout - strictly following the "inspiration" style
    fig.update_layout(
        title= "QQQ Close Price",
        template='plotly_white',
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12, color="#333333"),
        showlegend=True,
        height=900,
        xaxis_title="",
        yaxis_title=""
    )

    # Configure y-axis with specific grid color
    fig.update_yaxes(
        showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
        showline=True, linewidth=1, linecolor='#d3d3d3',
        tickcolor='gray', tickfont=dict(color='gray'),
        tickformat=',',
        row=1, col=1
    )

    # Output path
    charts_dir = 'charts'
    if not os.path.exists(charts_dir):
        os.makedirs(charts_dir)
    
    output_html = os.path.join(charts_dir, 'spy_chart.html')
    fig.write_html(output_html)
    print(f"Gráfico guardado exitosamente en: {output_html}")
    
    # Open in browser
    import webbrowser
    webbrowser.open(f'file://{os.path.abspath(output_html)}')

if __name__ == "__main__":
    plot_spy_chart()
