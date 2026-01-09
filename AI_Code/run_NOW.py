"""Run enhanced lookup using the driver we JUST downloaded"""
import sys
import glob
sys.stdout.reconfigure(line_buffering=True)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime

print("NYC DOT ENHANCED BATCH - RUNNING NOW!", flush=True)
print("=" * 60)

# Use the driver we just downloaded
driver_path = r'C:\Users\danek\.wdm\drivers\chromedriver\win64\143.0.7499.170\chromedriver-win32\chromedriver.exe'
print(f"Using driver: {driver_path}\n")

# Read summons
df = pd.read_excel('../ML TRACKING.xlsx', header=None)
summons_list = df.iloc[4:, 1].dropna().astype(str).str.strip().tolist()
print(f"Found {len(summons_list)} summons to process\n")

# Setup browser
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

service = ChromeService(executable_path=driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 10)

print("[OK] Chrome initialized\n")
print("Starting lookup...")
print("=" * 60)

results = []

for idx, summons in enumerate(summons_list, 1):
    print(f"[{idx}/{len(summons_list)}] {summons}", end=' ', flush=True)

    try:
        # Navigate and search
        driver.get('https://a820-ecbticketfinder.nyc.gov/searchHome.action')

        summons_input = wait.until(
            lambda d: d.find_element(By.NAME, "searchViolationObject.violationNo")
        )
        summons_input.clear()
        summons_input.send_keys(str(summons))

        search_button = driver.find_element(By.CSS_SELECTOR, "input[value*='Search']")
        search_button.click()

        import time
        time.sleep(2)

        # Parse results
        html = driver.page_source
        result = {'summons_number': summons, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        if "No Record Available" in html:
            result['status'] = 'NOT_FOUND'
            print("[NOT FOUND]")
        else:
            soup = BeautifulSoup(html, 'html.parser')

            # Get all tables
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).replace(':', '')
                        value = cells[1].get_text(strip=True)
                        if label and value and len(label) < 100:
                            key = label.lower().replace(' ', '_').replace('/', '_')
                            if not any(btn in value for btn in ['Hearing Locations', 'One Click', 'How To Pay']):
                                result[key] = value

            # Get charges
            charges_div = soup.find('div', {'id': 'infraDetails'})
            if charges_div:
                charges_table = charges_div.find('table')
                if charges_table:
                    charge_rows = charges_table.find_all('tr')[1:]
                    for row in charge_rows:
                        cells = row.find_all('td')
                        if cells and len(cells) >= 3:
                            result['charge_code'] = cells[0].get_text(strip=True)
                            result['charge_section'] = cells[1].get_text(strip=True)
                            result['charge_description'] = cells[2].get_text(strip=True)
                            if len(cells) > 3:
                                result['charge_face_amount'] = cells[3].get_text(strip=True)

            result['status'] = 'SUCCESS'
            print(f"[FOUND]")
            if 'balance_due' in result:
                print(f"     Balance: {result['balance_due']}", end='')
            if 'hearing_date' in result:
                print(f", Hearing: {result['hearing_date']}", end='')
            print()

        results.append(result)
        time.sleep(2)  # Be nice to server

    except Exception as e:
        print(f"[ERROR: {str(e)[:50]}]")
        results.append({'summons_number': summons, 'status': 'ERROR', 'error': str(e)})

driver.quit()

# Save results (to parent directory)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
excel_file = f'../summons_results_v2_{timestamp}.xlsx'
json_file = f'../summons_results_v2_{timestamp}.json'

pd.DataFrame(results).to_excel(excel_file, index=False)
with open(json_file, 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 60)
print("COMPLETE!")
print(f"Results: {excel_file}")
print(f"JSON: {json_file}")
print("=" * 60)

# Summary
found = sum(1 for r in results if r.get('status') == 'SUCCESS')
not_found = sum(1 for r in results if r.get('status') == 'NOT_FOUND')
errors = sum(1 for r in results if r.get('status') == 'ERROR')

print(f"Total: {len(results)} | Found: {found} | Not Found: {not_found} | Errors: {errors}")

with_balance = [r for r in results if r.get('balance_due', '0') not in ['0.00', '$0.00', '0', '']]
if with_balance:
    print(f"\nWith Outstanding Balance: {len(with_balance)}")
    for r in with_balance[:5]:
        print(f"  {r['summons_number']}: {r.get('balance_due', '?')}")
    if len(with_balance) > 5:
        print(f"  ... and {len(with_balance) - 5} more")
