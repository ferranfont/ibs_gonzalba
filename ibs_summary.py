
import pandas as pd
import plotly.graph_objects as go
import os
from config import INSTRUMENT, START_DATE, END_DATE

def generate_summary_report():
    input_file = os.path.join('outputs', 'trading_record.csv')
    output_html = os.path.join('charts', 'summary.html')

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # Read data
    df = pd.read_csv(input_file)
    if df.empty:
        print("No trades found in CSV.")
        return

    # --- Calculations ---
    
    # Basic Stats
    total_trades = len(df)
    winners = df[df['pnl_dollars'] > 0]
    losers = df[df['pnl_dollars'] <= 0]
    
    num_wins = len(winners)
    num_losses = len(losers)
    win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0
    
    gross_profit = winners['pnl_dollars'].sum()
    gross_loss = losers['pnl_dollars'].sum()
    
    total_pnl = df['pnl_dollars'].sum()
    avg_pnl = df['pnl_dollars'].mean()
    
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
    
    avg_winner = winners['pnl_dollars'].mean() if num_wins > 0 else 0
    avg_loser = losers['pnl_dollars'].mean() if num_losses > 0 else 0
    
    largest_winner = winners['pnl_dollars'].max() if num_wins > 0 else 0
    largest_loser = losers['pnl_dollars'].min() if num_losses > 0 else 0

    # Equity Curve & Drawdown
    df['equity'] = df['pnl_dollars'].cumsum()
    df['peak'] = df['equity'].cummax()
    df['drawdown'] = df['equity'] - df['peak']
    max_drawdown = df['drawdown'].min()

    # Ratios
    # Sharpe Ratio (Simplified: using trade returns, usually annualized daily returns are used but we have per-trade)
    # Assuming 'risk free' is 0 per trade.
    std_pnl = df['pnl_dollars'].std()
    sharpe_ratio = (avg_pnl / std_pnl) if std_pnl != 0 else 0
    # Note: Annualizing sharpe from trade frequency is varying, keeping it raw or clarifying "Per Trade Sharpe"
    
    # Sortino (Downside deviation)
    downside_returns = losers['pnl_dollars']
    downside_std = downside_returns.std()
    sortino_ratio = (avg_pnl / downside_std) if downside_std != 0 else 0

    # Trade Direction Analysis (Assuming all Long for IBS typically, but let's check PnL points vs Price diff)
    # The current logic suggests long only: pnl = exit - entry.
    # If strategy adds shorting, we check type. Here we assume Long based on code logic.
    long_trades = df # All are long in this strategy version
    short_trades = []
    
    long_pnl = long_trades['pnl_dollars'].sum()
    short_pnl = 0

    # --- Plotly Equity Curve ---
    fig = go.Figure()
    
    # Area chart for Equity
    fig.add_trace(go.Scatter(
        x=list(range(len(df))),
        y=df['equity'],
        mode='lines',
        fill='tozeroy',
        name='Equity',
        line=dict(color='#2ecc71', width=2),
        fillcolor='rgba(46, 204, 113, 0.2)'
    ))
    
    fig.update_layout(
        title='Equity Curve',
        xaxis_title='Trade Number',
        yaxis_title='Accumulated Profit ($)',
        template='plotly_white',
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=False
    )
    
    equity_chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    # --- Yearly Analysis ---
    df['year'] = pd.to_datetime(df['entry_date']).dt.year
    yearly_stats = []
    
    unique_years = sorted(df['year'].unique())
    for year in unique_years:
        ydf = df[df['year'] == year]
        y_total_trades = len(ydf)
        y_winners = ydf[ydf['pnl_dollars'] > 0]
        y_losers = ydf[ydf['pnl_dollars'] <= 0]
        
        y_gross_profit = y_winners['pnl_dollars'].sum()
        y_gross_loss = y_losers['pnl_dollars'].sum()
        y_total_pnl = ydf['pnl_dollars'].sum()
        y_avg_pnl = ydf['pnl_dollars'].mean()
        
        y_win_rate = (len(y_winners) / y_total_trades * 100) if y_total_trades > 0 else 0
        y_profit_factor = abs(y_gross_profit / y_gross_loss) if y_gross_loss != 0 else float('inf')
        
        y_std_pnl = ydf['pnl_dollars'].std()
        y_sharpe = (y_avg_pnl / y_std_pnl) if y_std_pnl and y_std_pnl != 0 else 0
        
        y_downside = y_losers['pnl_dollars']
        y_downside_std = y_downside.std()
        y_sortino = (y_avg_pnl / y_downside_std) if y_downside_std and y_downside_std != 0 else 0
        
        yearly_stats.append({
            'Year': year,
            'Total Trades': y_total_trades,
            'Win Rate': y_win_rate,
            'Total PnL': y_total_pnl,
            'Avg PnL': y_avg_pnl,
            'Profit Factor': y_profit_factor,
            'Sharpe': y_sharpe,
            'Sortino': y_sortino
        })
    
    # Generate Yearly HTML Table
    yearly_table_html = """
        <h2>Yearly Performance</h2>
        <table>
            <thead>
                <tr>
                    <th>Year</th>
                    <th>Trades</th>
                    <th>Win Rate</th>
                    <th>Total PnL</th>
                    <th>Avg PnL</th>
                    <th>Profit Factor</th>
                    <th>Sharpe</th>
                    <th>Sortino</th>
                </tr>
            </thead>
            <tbody>
    """
    for stat in yearly_stats:
        pnl_class = "profit" if stat['Total PnL'] > 0 else "loss"
        yearly_table_html += f"""
                <tr>
                    <td>{stat['Year']}</td>
                    <td>{stat['Total Trades']}</td>
                    <td>{stat['Win Rate']:.1f}%</td>
                    <td class="{pnl_class}">${stat['Total PnL']:,.2f}</td>
                    <td>${stat['Avg PnL']:,.2f}</td>
                    <td>{stat['Profit Factor']:.2f}</td>
                    <td>{stat['Sharpe']:.2f}</td>
                    <td>{stat['Sortino']:.2f}</td>
                </tr>
        """
    yearly_table_html += """
            </tbody>
        </table>
    """

    # --- HTML Generation ---
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>IBS Strategy Summary | {INSTRUMENT}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-card .value {{
            font-size: 28px;
            font-weight: bold;
            margin: 0;
        }}
        .win-loss {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        .win-loss p {{
            margin: 8px 0;
            color: #2c3e50;
        }}
        .win-loss .value {{
            font-weight: bold;
            color: #34495e;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .profit {{
            color: green;
            font-weight: bold;
        }}
        .loss {{
            color: red;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>IBS Strategy Summary ({INSTRUMENT})</h1>
        <p><strong>Date Range:</strong> {START_DATE} to {END_DATE}</p>
        <p><strong>Total Trades:</strong> {total_trades}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Trades</h3>
                <p class="value">{total_trades}</p>
            </div>
            <div class="summary-card">
                <h3>Win Rate</h3>
                <p class="value">{win_rate:.1f}%</p>
            </div>
            <div class="summary-card">
                <h3>Total P&L</h3>
                <p class="value">${total_pnl:,.2f}</p>
            </div>
            <div class="summary-card">
                <h3>Avg P&L per Trade</h3>
                <p class="value">${avg_pnl:,.2f}</p>
            </div>
        </div>

        <h2>Performance Breakdown</h2>
        <div class="win-loss">
            <p>Win Rate: <span class="value">{win_rate:.1f}%</span></p>
            <p>Winners / Losers: <span class="value">{num_wins} / {num_losses}</span></p>
            <p>Gross Profit: <span class="value">${gross_profit:,.2f}</span></p>
            <p>Gross Loss: <span class="value">${gross_loss:,.2f}</span></p>
            <p>Profit Factor: <span class="value">{profit_factor:.2f}</span></p>
            <p>Avg Winner: <span class="value">${avg_winner:,.2f}</span></p>
            <p>Avg Loser: <span class="value">${avg_loser:,.2f}</span></p>
            <p>Largest Winner: <span class="value">${largest_winner:,.2f}</span></p>
            <p>Largest Loser: <span class="value">${largest_loser:,.2f}</span></p>
        </div>

        <h2>Risk Metrics</h2>
        <div class="win-loss">
            <p>Max Drawdown: <span class="value">${max_drawdown:,.2f}</span></p>
            <p>Sharpe Ratio (Per Trade): <span class="value">{sharpe_ratio:.2f}</span></p>
            <p>Sortino Ratio (Per Trade): <span class="value">{sortino_ratio:.2f}</span></p>
        </div>

        <h2>Equity Curve</h2>
        <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {equity_chart_html}
        </div>

        {yearly_table_html}

        <h2>Trade List</h2>
        <table>
            <thead>
                <tr>
                    <th>Entry Date</th>
                    <th>Entry Price</th>
                    <th>Exit Date</th>
                    <th>Exit Price</th>
                    <th>PnL Points</th>
                    <th>PnL $</th>
                    <th>Result</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add Rows
    for _, row in df.iterrows():
        pnl_class = "profit" if row['pnl_dollars'] > 0 else "loss"
        entry_date = row['entry_date'].split(' ')[0] # Simple split
        exit_date = row['exit_date'].split(' ')[0]
        html_content += f"""
                <tr>
                    <td>{entry_date}</td>
                    <td>{row['entry_price']:.2f}</td>
                    <td>{exit_date}</td>
                    <td>{row['exit_price']:.2f}</td>
                    <td>{row['pnl_points']:.2f}</td>
                    <td class="{pnl_class}">${row['pnl_dollars']:,.2f}</td>
                    <td class="{pnl_class}">{row['result'].upper()}</td>
                </tr>
        """

    html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
    """

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Summary report saved to: {output_html}")
    
    # Open in browser
    import webbrowser
    webbrowser.open(f'file://{os.path.abspath(output_html)}')

if __name__ == "__main__":
    generate_summary_report()
