import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
from CONFIG import THRESHOLD

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
    df = pd.read_csv(file_path)
    # Clean column names (remove surrounding whitespace)
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

    # Add Price trace (Candlestick)
    trace_price = go.Candlestick(
        x=df['index'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='SPY',
        increasing=dict(line=dict(color='green')),
        decreasing=dict(line=dict(color='red')),
        opacity=0.9
    )
    fig.add_trace(trace_price, row=1, col=1)

    # Calculate IBS and Filter Signals
    # Formula: IBS = (Close - Low) / (High - Low)
    # Ensure denominator is not zero
    df['high_low_diff'] = df['High'] - df['Low']
    # Use a small epsilon or fillna to handle div by zero but effectively 0 range means 0 IBS or ignore
    df['ibs'] = (df['Close'] - df['Low']) / df['high_low_diff']
    df['ibs'] = df['ibs'].fillna(0.0)

    # Filter rows where IBS > THRESHOLD
    signals = df[df['ibs'] > THRESHOLD].copy()
    
    print(f"Found {len(signals)} signals with IBS > {THRESHOLD}")

    # Save signals to CSV
    outputs_dir = 'outputs'
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir)
    signals_output_path = os.path.join(outputs_dir, 'entry_signals.csv')
    signals.to_csv(signals_output_path, index=False)
    print(f"Entry signals saved to: {signals_output_path}")

    # Add Blue Dots for Signals
    if not signals.empty:
        trace_signals = go.Scatter(
            x=signals['index'],
            y=signals['Close'], # Plot dot at Close price
            mode='markers',
            name=f'IBS > {THRESHOLD}',
            marker=dict(
                color='blue',
                size=8,
                symbol='circle'
            ),
            hovertemplate='<b>Signal</b><br>Price: %{y:.2f}<br>IBS: %{customdata:.2f}<extra></extra>',
            customdata=signals['ibs']
        )
        fig.add_trace(trace_signals, row=1, col=1)

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
        title='SPY Close Price - Inspired Style',
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
