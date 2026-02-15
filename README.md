# IBS Trading System (For Nasdaq Futures - NQ=F)

This project implements a complete algorithmic trading system based on the **Internal Bar Strength (IBS)** indicator and **Minimum Low of Last X Days** logic. It is specifically configured for trading **Nasdaq 100 Futures (NQ=F)**.

## 🚀 Key Features

*   **Instrument:** Nasdaq 100 Futures (`NQ=F`).
*   **Point Value:** **$20 per point** ($5 per tick).
*   **Trading Strategy:**
    *   **Entry (Long Only):** Enter on Open if previous day's IBS < `ENTRY_THRESHOLD` (0.2) AND Low <= Minimum Low of Last `MIN_LAST_DAYS` (10).
    *   **Exit:** Exit on Open if previous day's IBS > `EXIT_THRESHOLD` (0.6).
    *   **Position Management:** Maximum of **3 open positions** at any time.
*   **Reporting:**
    *   Detailed Trade Log (CSV).
    *   Interactive Equity Curve Area Chart (Green).
    *   Comprehensive Performance Metrics (Sharpe, Sortino, Win Rate, Profit Factor).
    *   Yearly Performance Breakdown Table.

## 📂 Project Structure

### Main Scripts

*   **`main.py`**: The orchestrator script. Runs the entire workflow from data download to summary report generation.
*   **`config.py`**: Central configuration file.
    *   Contains parameters like `INSTRUMENT`, `POINT_VALUE`, `ENTRY_THRESHOLD`, `EXIT_THRESHOLD`, `START_DATE`, `END_DATE`.
*   **`ibs_trading_system.py`**: The core trading engine.
    *   Executes the backtest.
    *   Manages positions and calculates PnL (Points and Dollars).
    *   Generates the trade log (`outputs/trading_record.csv`).
*   **`ibs_summary.py`**: Reporting module.
    *   Generates a professional HTML dashboard (`charts/summary.html`).
    *   Calculates advanced metrics and yearly statistics.
*   **`import_data.py`**: Generic data downloader using `yfinance`.
*   **`find_min_last_days.py`**: Calculates and plots the "Minimum Low of Last X Days" indicator.
*   **`find_ibs_indicator.py`**: Calculates the IBS indicator values.

### Directories

*   **`data/`**: Stores raw CSV data (e.g., `NQ=F.csv`).
*   **`outputs/`**: Stores processed data files (`trading_record.csv`, `ibs_indicator.csv`).
*   **`charts/`**: Stores generated HTML charts (`summary.html`, `trading_system_chart.html`).

## 🛠️ Usage

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the System:**
    ```bash
    python main.py
    ```

    This command will automatically:
    1.  Download the latest data for `NQ=F`.
    2.  Calculate indicators.
    3.  Run the trading system backtest.
    4.  Generate the summary report.
    5.  Open `charts/summary.html` in your default web browser.

## 📊 Strategy Logic Details

### IBS Formula
$$ IBS = \frac{Close - Low}{High - Low} $$

### Entry Logic
*   **Signal:** Day's IBS < 0.2
*   **Filter:** Day's Low <= Lowest Low of last 10 days.
*   **Action:** Buy at Next Day's Open.

### Exit Logic
*   **Signal:** Day's IBS > 0.6.
*   **Action:** Sell at Next Day's Open.

### PnL Calculation
*   Standard Point Value for NQ Futures is used ($20/point).
*   PnL ($) = (Exit Price - Entry Price) * 20.
