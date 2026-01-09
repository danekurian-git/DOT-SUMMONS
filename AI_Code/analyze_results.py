"""
Analyze summons results and show status breakdowns
"""
import pandas as pd
from datetime import datetime
import sys

def parse_balance(val):
    """Convert balance string to float"""
    if pd.isna(val) or val == '' or val == '0.00':
        return 0.0
    val_str = str(val).replace('$', '').replace(',', '').strip()
    try:
        return float(val_str)
    except:
        return 0.0

def analyze_results(excel_file):
    """Analyze the results file and show detailed breakdown"""

    df = pd.read_excel(excel_file)

    # Parse dates and balances
    df['hearing_date_parsed'] = pd.to_datetime(df['hearing_date'], errors='coerce', format='%m/%d/%Y')
    df['balance_numeric'] = df['balance_due'].apply(parse_balance)

    today = datetime.now()
    past_hearings = df[df['hearing_date_parsed'] < today].copy()
    future_hearings = df[df['hearing_date_parsed'] >= today].copy()

    print('=' * 100)
    print('NYC DOT SUMMONS ANALYSIS')
    print('=' * 100)
    print(f'\nAnalyzing: {excel_file}')
    print(f'Generated: {today.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Total summons: {len(df)}')

    # Overall financial summary
    print('\n' + '=' * 100)
    print('FINANCIAL SUMMARY')
    print('=' * 100)
    print(f'Total outstanding balance: ${df["balance_numeric"].sum():,.2f}')
    print(f'Cases with balance due: {len(df[df["balance_numeric"] > 0])}')
    print(f'Cases paid/dismissed: {len(df[df["balance_numeric"] == 0])}')

    # Breakdown by hearing result
    print('\n' + '=' * 100)
    print('BREAKDOWN BY HEARING RESULT')
    print('=' * 100)

    hearing_results = df['hearing_result'].value_counts()
    for result, count in hearing_results.items():
        subset = df[df['hearing_result'] == result]
        total_balance = subset['balance_numeric'].sum()
        print(f'\n{result}: {count} cases (${total_balance:,.2f} total balance)')

        if result == 'DISMISSED':
            print('  -> Cases thrown out/dropped. You won!')
        elif result == 'IN VIOLATION':
            print('  -> Hearing occurred, found guilty')
        elif result == 'DEFAULTED':
            print('  -> MISSED HEARING - decided against you in absence')

    # Past vs Future hearings
    print('\n' + '=' * 100)
    print('HEARING TIMELINE')
    print('=' * 100)
    print(f'Past hearings (before {today.strftime("%m/%d/%Y")}): {len(past_hearings)}')
    print(f'  Outstanding balance: ${past_hearings["balance_numeric"].sum():,.2f}')
    print(f'\nUpcoming hearings: {len(future_hearings)}')
    print(f'  Outstanding balance: ${future_hearings["balance_numeric"].sum():,.2f}')

    # DEFAULTED CASES - Detailed report
    defaulted = df[df['hearing_result'] == 'DEFAULTED']
    if len(defaulted) > 0:
        print('\n\n' + '=' * 100)
        print(f'DEFAULTED CASES - MISSED HEARINGS ({len(defaulted)} total)')
        print('=' * 100)
        print('\nThese cases were decided against you because the hearing was missed.')
        print('Action needed: Check if you can request a new hearing or need to pay.')
        print('-' * 100)

        for idx, row in defaulted.iterrows():
            print(f'\n[{idx+1}] Summons: {row["summons_number"]}')
            print(f'    Issued: {row["date_issued"]}')
            print(f'    Hearing Date (MISSED): {row["hearing_date"]}')
            print(f'    Violation: {row.get("charge_code", "N/A")} - {row.get("charge_description", "N/A")}')
            print(f'    Status: {row["status_of_summons_notice"]}')
            print(f'    Balance Due: ${row["balance_numeric"]:,.2f}')
            if row["balance_numeric"] == 0:
                print('    [PAID]')

    # DISMISSED CASES
    dismissed = df[df['hearing_result'] == 'DISMISSED']
    if len(dismissed) > 0:
        print('\n\n' + '=' * 100)
        print(f'DISMISSED CASES - YOU WON ({len(dismissed)} total)')
        print('=' * 100)
        print('\nThese cases were thrown out. No action needed.')
        print('-' * 100)

        for idx, row in dismissed.iterrows():
            print(f'\n[{idx+1}] Summons: {row["summons_number"]}')
            print(f'    Issued: {row["date_issued"]}')
            print(f'    Hearing Date: {row["hearing_date"]}')
            print(f'    Violation: {row.get("charge_code", "N/A")} - {row.get("charge_description", "N/A")}')
            print(f'    Balance: $0.00 [DISMISSED]')

    # UPCOMING HEARINGS
    if len(future_hearings) > 0:
        print('\n\n' + '=' * 100)
        print(f'UPCOMING HEARINGS ({len(future_hearings)} total)')
        print('=' * 100)
        print('\nThese hearings have not occurred yet. Mark your calendar!')
        print('-' * 100)

        future_sorted = future_hearings.sort_values('hearing_date_parsed')
        for idx, row in future_sorted.iterrows():
            print(f'\n[UPCOMING] Summons: {row["summons_number"]}')
            print(f'    Hearing Date: {row["hearing_date"]} at {row.get("hearing_location", "N/A")}')
            print(f'    Issued: {row["date_issued"]}')
            print(f'    Violation: {row.get("charge_code", "N/A")} - {row.get("charge_description", "N/A")}')
            print(f'    Potential penalty: ${row["balance_numeric"]:,.2f}')

    # Cases needing payment
    needs_payment = df[(df['balance_numeric'] > 0) & (df['hearing_date_parsed'] < today)]
    if len(needs_payment) > 0:
        print('\n\n' + '=' * 100)
        print(f'ACTION REQUIRED - PAYMENT NEEDED ({len(needs_payment)} cases)')
        print('=' * 100)
        print(f'Total due: ${needs_payment["balance_numeric"].sum():,.2f}')
        print('-' * 100)

        for idx, row in needs_payment.iterrows():
            print(f'\n[PAY] Summons: {row["summons_number"]}')
            print(f'      Amount due: ${row["balance_numeric"]:,.2f}')
            print(f'      Hearing result: {row["hearing_result"]}')
            print(f'      Violation: {row.get("charge_code", "N/A")} - {row.get("charge_description", "N/A")}')

    print('\n' + '=' * 100)
    print('END OF REPORT')
    print('=' * 100)

if __name__ == '__main__':
    # Find the most recent results file
    import glob
    import os

    # Go up one directory if we're in AI_Code
    if os.path.basename(os.getcwd()) == 'AI_Code':
        os.chdir('..')

    results_files = glob.glob('summons_results_v2_*.xlsx')

    if not results_files:
        print('ERROR: No results files found!')
        print('Looking for: summons_results_v2_*.xlsx')
        sys.exit(1)

    # Use the most recent file
    latest_file = max(results_files, key=os.path.getctime)

    print(f'\nFound results file: {latest_file}\n')
    analyze_results(latest_file)
