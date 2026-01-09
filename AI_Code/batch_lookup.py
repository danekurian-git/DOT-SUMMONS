"""
Batch lookup specifically for ML TRACKING.xlsx - Column B from row 5 down
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import json

# Read summons from Excel - Column B (index 1), starting from row 5 (index 4)
print("Reading summons from ML TRACKING.xlsx...")
df = pd.read_excel('ML TRACKING.xlsx', header=None)
summons_list = df.iloc[4:, 1].dropna().astype(str).tolist()

print(f"Found {len(summons_list)} summons to process")
print(f"First few: {summons_list[:5]}")
print(f"Last few: {summons_list[-5:]}")

# Setup
url = 'https://a820-ecbticketfinder.nyc.gov/getViolationbyID.action'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://a820-ecbticketfinder.nyc.gov/searchHome.action',
    'Content-Type': 'application/x-www-form-urlencoded'
}

results = []
total = len(summons_list)

print(f"\nStarting lookup of {total} summons...")
print("=" * 60)

for idx, summons in enumerate(summons_list, 1):
    data = {
        'searchType': 'violationNumber',
        'violationNumber': summons.strip(),
        'searchBtn': 'Search'
    }

    print(f"[{idx}/{total}] Processing: {summons}", end='')

    try:
        response = requests.post(url, data=data, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')

        result = {
            'summons_number': summons,
            'row_number': idx + 4,  # Excel row number
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Parse tables
        tables = soup.find_all('table')
        if tables:
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).replace(':', '')
                        value = cells[1].get_text(strip=True)
                        if label and value:
                            result[label] = value

        # Check status
        if 'Summons/Notice Number' in result:
            if result['Summons/Notice Number'] == 'No Record Available':
                result['status'] = 'NOT_FOUND'
                print(" - NOT FOUND")
            else:
                result['status'] = 'FOUND'
                print(" - FOUND ✓")
        else:
            result['status'] = 'UNKNOWN'
            print(" - UNKNOWN")

        results.append(result)

    except Exception as e:
        print(f" - ERROR: {str(e)}")
        results.append({
            'summons_number': summons,
            'row_number': idx + 4,
            'status': 'ERROR',
            'error': str(e)
        })

    # Rate limiting - be nice to the server
    if idx < total:
        time.sleep(1.5)

# Save results
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Excel output
df_results = pd.DataFrame(results)
excel_file = f'summons_results_{timestamp}.xlsx'
df_results.to_excel(excel_file, index=False)

# JSON output
json_file = f'summons_results_{timestamp}.json'
with open(json_file, 'w') as f:
    json.dump(results, f, indent=2)

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total processed: {len(results)}")
print(f"Found: {sum(1 for r in results if r.get('status') == 'FOUND')}")
print(f"Not found: {sum(1 for r in results if r.get('status') == 'NOT_FOUND')}")
print(f"Errors: {sum(1 for r in results if r.get('status') == 'ERROR')}")
print(f"Unknown: {sum(1 for r in results if r.get('status') == 'UNKNOWN')}")

print(f"\nResults saved to:")
print(f"  - {excel_file}")
print(f"  - {json_file}")

# Show any found summons
found_summons = [r for r in results if r.get('status') == 'FOUND']
if found_summons:
    print(f"\n🔍 ACTIVE SUMMONS FOUND ({len(found_summons)}):")
    for r in found_summons:
        print(f"  - {r['summons_number']} (Row {r['row_number']})")
        if 'Balance Due' in r:
            print(f"    Balance: {r.get('Balance Due', 'N/A')}")
else:
    print("\n✓ No active summons found in the system")
