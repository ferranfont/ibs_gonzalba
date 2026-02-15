import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import ENTRY_THRESHOLD, EXIT_THRESHOLD, MIN_LAST_DAYS, MAX_OPEN_POSITIONS, INSTRUMENT, START_DATE, END_DATE, POINT_VALUE
import sys

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def run_ibs_trading_system():
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

    # Calculate Indicators
    # 1. Rolling minimum of Low (Last Days)
    # rolling().min() includes current row.
    df['min_last_days'] = df['Low'].rolling(window=MIN_LAST_DAYS).min()

    # 2. IBS
    df['high_low_diff'] = df['High'] - df['Low']
    df['ibs'] = df.apply(
        lambda row: (row['Close'] - row['Low']) / row['high_low_diff'] if row['high_low_diff'] != 0 else 0, 
        axis=1
    )
    df['ibs'] = df['ibs'].fillna(0.0)

    # Identify Potential Signals (Day T)
    # Entry Signal (Green Dot): IBS < ENTRY_THRESHOLD AND Low <= min_last_days
    df['signal_entry'] = (df['ibs'] < ENTRY_THRESHOLD) & (df['Low'] <= df['min_last_days'])
    
    # Exit Signal (Red Dot): IBS > EXIT_THRESHOLD
    df['signal_exit'] = df['ibs'] > EXIT_THRESHOLD

    # Trading Logic with Position Management
    trades = []
    open_positions = [] # List of dicts: {'entry_date': ..., 'entry_price': ..., 'entry_idx': ...}

    # Iterate day by day
    # We make decisions based on Day T signals to execute on Day T+1 Open
    
    records = df.to_dict('records')
    # Loop from 1 to len-1 because execution is on T+1 based on T signal
    
    for i in range(len(records) - 1):
        day_t = records[i]
        day_t_plus_1 = records[i+1] # Execution Day
        
        # 1. Check for Exits (Priority: Exit before Entry?)
        # Usually strategy defines this. Let's process exits first to free up slots.
        # Rule: If Day T has Red Dot (Exit Signal), Exit at Day T+1 Open.
        
        if day_t['signal_exit']:
            # Close ALL open positions? Or FIFO?
            # "salga al dia siguiente de tener una vela con un puntito rojo" implies all positions exit.
            # Assuming getting a red dot means "Condition to Exit Market".
            
            if open_positions:
                exit_price = day_t_plus_1['Open']
                exit_date = day_t_plus_1['datetime']
                exit_idx = day_t_plus_1['index']
                
                for pos in open_positions:
                    pnl_points = exit_price - pos['entry_price']
                    pnl_dollars = pnl_points * POINT_VALUE
                    result = 'win' if pnl_points > 0 else 'loss'
                    
                    trades.append({
                        'entry_date': pos['entry_date'],
                        'entry_price': code_format(pos['entry_price']),
                        'entry_index': pos['entry_index'],
                        'exit_date': exit_date,
                        'exit_price': code_format(exit_price),
                        'exit_index': exit_idx,
                        'pnl_points': code_format(pnl_points),
                        'pnl_dollars': code_format(pnl_dollars),
                        'result': result
                    })
                open_positions = [] # All positions closed

        # 2. Check for Entries
        # Rule: If Day T has Green Dot (Entry Signal), Enter at Day T+1 Open.
        # Condition: MAX_OPEN_POSITIONS not reached.
        
        if day_t['signal_entry']:
            if len(open_positions) < MAX_OPEN_POSITIONS:
                entry_price = day_t_plus_1['Open']
                entry_date = day_t_plus_1['datetime']
                entry_idx = day_t_plus_1['index']
                
                open_positions.append({
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'entry_index': entry_idx
                })

    # Save Trades to CSV
    trades_df = pd.DataFrame(trades)
    
    outputs_dir = 'outputs'
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir)
        
    output_path = os.path.join(outputs_dir, 'trading_record.csv')
    if not trades_df.empty:
        trades_df.to_csv(output_path, index=False)
        
        # Calculate Stats
        total_points = trades_df['pnl_points'].sum()
        total_dollars = trades_df['pnl_dollars'].sum()
        wins = len(trades_df[trades_df['result'] == 'win'])
        losses = len(trades_df[trades_df['result'] == 'loss'])
        
        print(f"System execution complete.")
        print(f"Trades Generated: {len(trades_df)}")
        print(f"Wins: {wins} | Losses: {losses}")
        print(f"Total Profit: {total_points:.2f} points | ${total_dollars:.2f}")
        print(f"Detailed record saved to {output_path}")
    else:
        print("No trades generated.")
        return

    # --- Plotting ---
    plot_chart(df, trades_df)

def code_format(val):
    return float(f"{val:.2f}")

def plot_chart(df, trades_df):
    # Create figure
    fig = make_subplots(
        rows=1, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03
    )

    # 1. Price Trace (Candlestick)
    trace_price = go.Candlestick(
        x=df['index'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Prices',
        increasing=dict(line=dict(color='grey', width=1), fillcolor='green'),
        decreasing=dict(line=dict(color='grey', width=1), fillcolor='red'),
        opacity=0.9
    )
    fig.add_trace(trace_price, row=1, col=1)

    # 2. Min Last Days Line
    trace_min = go.Scatter(
        x=df['index'],
        y=df['min_last_days'],
        mode='lines',
        name=f'Min Last {MIN_LAST_DAYS} Days',
        line=dict(color='blue', width=1),
        hoverinfo='skip'
    )
    fig.add_trace(trace_min, row=1, col=1)

    # 2b. IBS Signals (Raw Dots)
    # Entry Signals (Green Dot)
    entry_signals = df[df['signal_entry']]
    if not entry_signals.empty:
        fig.add_trace(go.Scatter(
            x=entry_signals['index'],
            y=entry_signals['Low'] * 0.995, # Below Low (and below the triangle potentially)
            mode='markers',
            name='IBS Condition Met',
            marker=dict(color='green', size=6, symbol='circle'), # Smaller dot
            hovertemplate='<b>IBS Entry Signal</b><br>IBS: %{customdata:.2f}<extra></extra>',
            customdata=entry_signals['ibs']
        ), row=1, col=1)

    # Exit Signals (Red Dot)
    exit_signals = df[df['signal_exit']]
    if not exit_signals.empty:
        fig.add_trace(go.Scatter(
            x=exit_signals['index'],
            y=exit_signals['High'] * 1.005, # Above High
            mode='markers',
            name='IBS Exit Signal',
            marker=dict(color='red', size=6, symbol='circle'),
            hovertemplate='<b>IBS Exit Signal</b><br>IBS: %{customdata:.2f}<extra></extra>',
            customdata=exit_signals['ibs']
        ), row=1, col=1)

    # 3. Trades (Lines and Markers)
    
    # Entry Markers
    trace_entries = go.Scatter(
        x=df.iloc[trades_df['entry_index']]['index'],
        y=trades_df['entry_price'],
        mode='markers',
        name='Trade Entry',
        marker=dict(
            symbol='triangle-up',
            size=10,
            color='lightgreen',
            line=dict(width=1, color='darkgreen')
        ),
        hovertemplate='<b>Long Entry</b><br>Price: %{y:.2f}<extra></extra>'
    )
    fig.add_trace(trace_entries, row=1, col=1)

    # Exit Markers (Win)
    wins = trades_df[trades_df['result'] == 'win']
    if not wins.empty:
        trace_wins = go.Scatter(
            x=df.iloc[wins['exit_index']]['index'],
            y=wins['exit_price'],
            mode='markers',
            name='Exit (Win)',
            marker=dict(
                symbol='square',
                size=8,
                color='green',
                line=dict(width=1, color='darkgreen')
            ),
            hovertemplate='<b>Exit (Win)</b><br>PnL: $%{customdata:.2f}<extra></extra>',
            customdata=wins['pnl_dollars']
        )
        fig.add_trace(trace_wins, row=1, col=1)

    # Exit Markers (Loss)
    losses = trades_df[trades_df['result'] == 'loss']
    if not losses.empty:
        trace_losses = go.Scatter(
            x=df.iloc[losses['exit_index']]['index'],
            y=losses['exit_price'], # Fixed: use actual exit price from trade
            mode='markers',
            name='Exit (Loss)',
            marker=dict(
                symbol='square',
                size=8,
                color='red',
                line=dict(width=1, color='darkred')
            ),
            hovertemplate='<b>Exit (Loss)</b><br>PnL: $%{customdata:.2f}<extra></extra>',
            customdata=losses['pnl_dollars']
        )
        fig.add_trace(trace_losses, row=1, col=1)

    # Connection Lines
    for _, trade in trades_df.iterrows():
        entry_idx = trade['entry_index']
        exit_idx = trade['exit_index']
            
        fig.add_trace(go.Scatter(
            x=[df.iloc[entry_idx]['index'], df.iloc[exit_idx]['index']],
            y=[trade['entry_price'], trade['exit_price']],
            mode='lines',
            line=dict(color='lightgrey', width=1),
            showlegend=False,
            hoverinfo='skip'
        ), row=1, col=1)

    # Layout
    fig.update_layout(
        title=f'{INSTRUMENT} Close Price | {START_DATE} to {END_DATE} | Max Pos: {MAX_OPEN_POSITIONS}',
        template='plotly_white',
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12, color="#333333"),
        showlegend=True,
        height=900,
        xaxis_rangeslider_visible=False
    )

    # X-Axis styling
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

    # Save Chart
    charts_dir = 'charts'
    if not os.path.exists(charts_dir):
        os.makedirs(charts_dir)
    
    chart_path = os.path.join(charts_dir, 'trading_system_chart.html')
    fig.write_html(chart_path)
    print(f"Chart saved to {chart_path}")
    
    import webbrowser
    webbrowser.open(f'file://{os.path.abspath(chart_path)}')

if __name__ == "__main__":
    run_ibs_trading_system()
