import os
import sys
from config import INSTRUMENT, START_DATE, END_DATE

# Import workflow functions
from import_data import download_data
from find_min_last_days import find_and_plot_min_last_days
from find_ibs_indicator import calculate_ibs
from ibs_trading_system import run_ibs_trading_system
from ibs_summary import generate_summary_report

def main():
    print("=== Starting Trading Workflow ===\n")

    # 1. Download Data
    print("Step 1: Downloading Data...")
    save_path = os.path.join('data', f'{INSTRUMENT}.csv')
    
    # We use start/end dates from config, so set period=None to trigger start/end logic in impot_data
    # Assume interval is '1d' for daily data
    try:
        download_data(INSTRUMENT, period=None, start=START_DATE, end=END_DATE, interval='1d', save_path=save_path)
    except Exception as e:
        print(f"Error downloading data: {e}")
        return

    # 2. Calculate Min Last Days Indicator
    print("\nStep 2: Calculating Min Last Days Indicator...")
    find_and_plot_min_last_days()

    # 3. Calculate IBS Indicator
    print("\nStep 3: Calculating IBS Indicator...")
    calculate_ibs()

    # 4. Run IBS Trading System
    print("\nStep 4: Running IBS Trading System...")
    run_ibs_trading_system()

    # 5. Generate Summary Report
    print("\nStep 5: Generating Summary Report...")
    generate_summary_report()

    print("\n=== Workflow Completed Successfully ===")

if __name__ == "__main__":
    main()
