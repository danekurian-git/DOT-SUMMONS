"""
Precedent Analyzer - Find similar cases with favorable outcomes
This is Phase 4 of the Master Plan: Case Analyzer
"""
import pandas as pd
from datetime import datetime

def analyze_precedents(excel_file='../summons_results_v2_20260103_004526.xlsx'):
    """Analyze violations to find precedent cases"""

    df = pd.read_excel(excel_file)

    print('=' * 100)
    print('PRECEDENT ANALYSIS - Finding Winning Patterns')
    print('=' * 100)

    # Group by violation code
    violation_codes = df['charge_code'].value_counts()

    print(f'\nTotal unique violation codes: {len(violation_codes)}')
    print('\nViolation code distribution:')
    print(violation_codes.head(15))

    # Analyze each violation code
    print('\n\n' + '=' * 100)
    print('VIOLATION CODE ANALYSIS - Dismissal Rates')
    print('=' * 100)

    for code in violation_codes.index[:15]:
        if pd.isna(code):
            continue

        code_cases = df[df['charge_code'] == code]
        total = len(code_cases)

        dismissed = len(code_cases[code_cases['hearing_result'] == 'DISMISSED'])
        in_violation = len(code_cases[code_cases['hearing_result'] == 'IN VIOLATION'])
        defaulted = len(code_cases[code_cases['hearing_result'] == 'DEFAULTED'])

        dismissal_rate = (dismissed / total * 100) if total > 0 else 0

        description = code_cases['charge_description'].iloc[0] if len(code_cases) > 0 else 'N/A'

        print(f'\n{code} - {description}')
        print(f'  Total cases: {total}')
        print(f'  DISMISSED: {dismissed} ({dismissal_rate:.1f}%)')
        print(f'  IN VIOLATION: {in_violation}')
        print(f'  DEFAULTED: {defaulted}')

        # Show summons numbers for each category
        if dismissed > 0:
            dismissed_summons = code_cases[code_cases['hearing_result'] == 'DISMISSED']['summons_number'].tolist()
            print(f'  Dismissed summons: {", ".join(map(str, dismissed_summons))}')

        if defaulted > 0:
            defaulted_summons = code_cases[code_cases['hearing_result'] == 'DEFAULTED']['summons_number'].tolist()
            defaulted_balance = code_cases[code_cases['hearing_result'] == 'DEFAULTED']['balance_due'].tolist()
            print(f'  Defaulted summons: {", ".join(map(str, defaulted_summons))}')

            # Calculate total at risk
            def parse_balance(val):
                if pd.isna(val) or val == '' or val == '0.00':
                    return 0.0
                val_str = str(val).replace('$', '').replace(',', '').strip()
                try:
                    return float(val_str)
                except:
                    return 0.0

            total_at_risk = sum(parse_balance(b) for b in defaulted_balance)
            if total_at_risk > 0:
                print(f'  Total at risk: ${total_at_risk:,.2f}')

    # SPECIAL FOCUS: ADG4 cases (user identified pattern)
    print('\n\n' + '=' * 100)
    print('SPECIAL ANALYSIS: ADG4 VIOLATIONS')
    print('User identified: Defaulted ADG4 cases may have precedent in dismissed ADG4 cases')
    print('=' * 100)

    adg4_cases = df[df['charge_code'] == 'ADG4']

    if len(adg4_cases) > 0:
        dismissed_adg4 = adg4_cases[adg4_cases['hearing_result'] == 'DISMISSED']
        defaulted_adg4 = adg4_cases[adg4_cases['hearing_result'] == 'DEFAULTED']

        print(f'\nTotal ADG4 cases: {len(adg4_cases)}')
        desc = adg4_cases['charge_description'].iloc[0]
        print(f'Description: {desc}')

        print(f'\n--- DISMISSED ADG4 Cases (PRECEDENT) ---')
        print(f'Count: {len(dismissed_adg4)}')
        print(f'Success rate: {len(dismissed_adg4)/len(adg4_cases)*100:.1f}%')

        for idx, row in dismissed_adg4.iterrows():
            summons = row['summons_number']
            issued = row['date_issued']
            hearing = row['hearing_date']
            location = row.get('inspection_location', 'N/A')
            print(f'\n  Summons: {summons}')
            print(f'    Issued: {issued}')
            print(f'    Hearing: {hearing}')
            print(f'    Location: {location}')
            print(f'    Result: DISMISSED [WON]')

        print(f'\n--- DEFAULTED ADG4 Cases (CAN USE PRECEDENT) ---')
        print(f'Count: {len(defaulted_adg4)}')

        for idx, row in defaulted_adg4.iterrows():
            summons = row['summons_number']
            issued = row['date_issued']
            hearing = row['hearing_date']
            location = row.get('inspection_location', 'N/A')
            balance = row['balance_due']
            status = row['status_of_summons_notice']
            print(f'\n  Summons: {summons}')
            print(f'    Issued: {issued}')
            print(f'    Hearing: {hearing} [MISSED]')
            print(f'    Location: {location}')
            print(f'    Balance: {balance}')
            print(f'    Status: {status}')

            # Check if within 75-day window
            hearing_date = pd.to_datetime(row['hearing_date'], format='%m/%d/%Y')
            days_since = (datetime.now() - hearing_date).days
            if days_since <= 75:
                print(f'    [URGENT] Within 75-day window ({75-days_since} days left)')
            else:
                print(f'    [PAST WINDOW] Need hearing reopening request')

        # Compare dates/locations/circumstances
        print(f'\n--- COMPARISON: Dismissed vs Defaulted ADG4 ---')

        if len(dismissed_adg4) > 0 and len(defaulted_adg4) > 0:
            print('\nDismissed cases dates:', ', '.join(dismissed_adg4['date_issued'].tolist()))
            print('Defaulted cases dates:', ', '.join(defaulted_adg4['date_issued'].tolist()))

            print('\nArgument to make:')
            print('  "The facts underlying these ADG4 violations are substantially')
            print('   similar to summons {} which'.format(', '.join(map(str, dismissed_adg4['summons_number'].tolist()))))
            print('   were DISMISSED after hearings. Under principles of')
            print('   consistency and equal application of law, these violations')
            print('   should also be dismissed."')

            total_at_risk = defaulted_adg4['balance_due'].apply(lambda x: float(str(x).replace('$', '').replace(',', '').strip()) if x and str(x) not in ['nan', '0.00'] else 0).sum()
            print(f'\n  Potential savings if argument succeeds: ${total_at_risk:,.2f}')

    print('\n\n' + '=' * 100)
    print('RECOMMENDATIONS')
    print('=' * 100)

    # Find all codes with both dismissed and defaulted cases
    codes_with_precedent = []
    for code in df['charge_code'].unique():
        if pd.isna(code):
            continue
        code_cases = df[df['charge_code'] == code]
        has_dismissed = len(code_cases[code_cases['hearing_result'] == 'DISMISSED']) > 0
        has_defaulted = len(code_cases[code_cases['hearing_result'] == 'DEFAULTED']) > 0

        if has_dismissed and has_defaulted:
            codes_with_precedent.append(code)

    print(f'\nViolation codes with PRECEDENT (have both dismissed and defaulted cases):')
    print(f'Count: {len(codes_with_precedent)}')
    print(f'Codes: {", ".join(codes_with_precedent)}')
    print('\nFor each of these, you can argue based on prior dismissals!')

if __name__ == '__main__':
    analyze_precedents()
