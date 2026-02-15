import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
from config import MIN_LAST_DAYS, INSTRUMENT

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def find_and_plot_min_last_days():
    # Load data
    file_path = os.path.join('data', f'{INSTRUMENT}.csv')
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    print(f"Reading data from {file_path}...")
    df = pd.read_csv(file_path, skipinitialspace=True)
    df.columns = df.columns.str.strip()
    
    # Process date
    if 'Date' in df.columns:
        df['datetime'] = pd.to_datetime(df['Date'], utc=True)
    elif df.index.name == 'Date':
        df['datetime'] = pd.to_datetime(df.index, utc=True)
    else:
        df['datetime'] = pd.to_datetime(df.iloc[:, 0], utc=True)
    
    # Create index for x-axis
    df = df.reset_index(drop=True)
    df['index'] = df.index

    # Calculate Min Last Days
    # Rolling minimum of 'Low'
    df['min_last_days'] = df['Low'].rolling(window=MIN_LAST_DAYS).min()

    print(f"Calculated Minimum of last {MIN_LAST_DAYS} days.")
    print(df[['datetime', 'Low', 'min_last_days']].tail())

    # Create figure
    # Save to CSV
    outputs_dir = 'outputs'
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir)
        
    output_csv_path = os.path.join(outputs_dir, 'min_last_days.csv')
    df_output = df[['datetime', 'Low', 'min_last_days']].copy()
    df_output.to_csv(output_csv_path, index=False)
    print(f"Datos guardados exitosamente en: {output_csv_path}")

    # Create figure
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
        name=INSTRUMENT,
        increasing=dict(line=dict(color='green')),
        decreasing=dict(line=dict(color='red')),
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

    # Configure layout
    fig.update_layout(
        title=f'{INSTRUMENT} Close Price with Min Last {MIN_LAST_DAYS} Days',
        template='plotly_white',
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12, color="#333333"),
        showlegend=True,
        height=900,
        xaxis_rangeslider_visible=False
    )

    # Configure x-axis ticks
    num_ticks = 30
    tick_indices = [int(i) for i in range(0, len(df), max(1, len(df)//num_ticks))]
    tick_vals = df.iloc[tick_indices]['index']
    tick_text = df.iloc[tick_indices]['datetime'].dt.strftime('%Y-%m-%d')

    fig.update_xaxes(
        tickmode='array', tickvals=tick_vals, ticktext=tick_text,
        tickangle=-45, showgrid=False,
        showline=True, linewidth=1, linecolor='#d3d3d3',
        row=1, col=1
    )

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
    
    output_html = os.path.join(charts_dir, f'{INSTRUMENT}_min_last_days.html')
    fig.write_html(output_html)
    print(f"Gráfico guardado exitosamente en: {output_html}")
    
    # Open in browser
    import webbrowser
    webbrowser.open(f'file://{os.path.abspath(output_html)}')

if __name__ == "__main__":
    find_and_plot_min_last_days()
