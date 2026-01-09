"""
NYC DOT Summons Lookup using Selenium (Browser Automation) - Version 2
Enhanced to capture hearing dates and violation charges
"""

import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
import json


class SummonsSeleniumLookup:
    def __init__(self, headless=False):
        """Initialize the browser"""
        chrome_options = Options()

        if headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        print("Setting up browser driver...")
        try:
            import os
            os.environ['WDM_LOCAL'] = '1'
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            print("[OK] Chrome browser initialized")
        except Exception as e:
            print(f"Chrome failed: {str(e)[:100]}")
            print("Trying Edge browser instead...")
            try:
                edge_options = EdgeOptions()
                if headless:
                    edge_options.add_argument('--headless')
                edge_options.add_argument('--disable-blink-features=AutomationControlled')
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])

                service = EdgeService(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=edge_options)
                self.wait = WebDriverWait(self.driver, 10)
                print("[OK] Edge browser initialized")
            except Exception as e2:
                raise Exception(f"Could not initialize any browser. Chrome error: {str(e)[:100]}, Edge error: {str(e2)[:100]}")

    def lookup_summons(self, summons_number):
        """Look up a single summons number"""
        try:
            url = "https://a820-ecbticketfinder.nyc.gov/searchHome.action"
            self.driver.get(url)
            time.sleep(1)

            # Find and fill summons input
            summons_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "searchViolationObject.violationNo"))
            )
            summons_input.clear()
            summons_input.send_keys(str(summons_number))

            # Click search button
            search_button = self.driver.find_element(By.CSS_SELECTOR, "input[value*='Search']")
            search_button.click()

            time.sleep(2)

            return self.extract_results(summons_number)

        except Exception as e:
            return {
                'summons_number': summons_number,
                'status': 'ERROR',
                'error': str(e)
            }

    def extract_results(self, summons_number):
        """Extract ALL violation details using BeautifulSoup"""
        result = {
            'summons_number': summons_number,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            # Get full page source
            html = self.driver.page_source

            # Check for "No Record Available"
            if "No Record Available" in html:
                result['status'] = 'NOT_FOUND'
                result['note'] = 'No Record Available'
                return result

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Extract from Case Details table (id="vioContent")
            case_details = soup.find('table', {'id': 'vioContent'})
            if case_details:
                rows = case_details.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).replace(':', '')
                        value = cells[1].get_text(strip=True)
                        if label and value and len(label) < 100:
                            key = label.lower().replace(' ', '_').replace('/', '_')
                            result[key] = value

            # Extract from More Details table (all tables with id="details")
            details_tables = soup.find_all('table', {'id': 'details'})
            for table in details_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).replace(':', '')
                        value = cells[1].get_text(strip=True)
                        if label and value and len(label) < 100:
                            key = label.lower().replace(' ', '_').replace('/', '_')
                            # Filter out button text
                            if not any(btn in value for btn in ['Hearing Locations', 'One Click', 'How To Pay']):
                                result[key] = value

            # Extract Explanation of Charges (even if hidden)
            charges_div = soup.find('div', {'id': 'infraDetails'})
            if charges_div:
                charges_table = charges_div.find('table')
                if charges_table:
                    # Get headers
                    headers = []
                    header_row = charges_table.find('tr')
                    if header_row:
                        headers = [th.get_text(strip=True).lower().replace(' ', '_')
                                 for th in header_row.find_all('th')]

                    # Get charge data
                    charge_rows = charges_table.find_all('tr')[1:]  # Skip header
                    for idx, row in enumerate(charge_rows, 1):
                        cells = row.find_all('td')
                        if cells and len(cells) >= 3:
                            # Create prefixed keys for each charge
                            prefix = f"charge_{idx}_" if len(charge_rows) > 1 else "charge_"

                            if len(cells) > 0:
                                result[f'{prefix}code'] = cells[0].get_text(strip=True)
                            if len(cells) > 1:
                                result[f'{prefix}section'] = cells[1].get_text(strip=True).replace('\\xa0', ' ')
                            if len(cells) > 2:
                                result[f'{prefix}description'] = cells[2].get_text(strip=True)
                            if len(cells) > 3:
                                result[f'{prefix}face_amount'] = cells[3].get_text(strip=True)

            # Set status
            if len(result) > 3:
                result['status'] = 'SUCCESS'
            else:
                result['status'] = 'NO_DATA'

            return result

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            return result

    def lookup_batch(self, summons_list, delay=3):
        """Look up multiple summons numbers"""
        results = []
        total = len(summons_list)

        print(f"\nStarting lookup of {total} summons...")
        print("=" * 60)

        for idx, summons in enumerate(summons_list, 1):
            print(f"[{idx}/{total}] Processing: {summons}", end=' ')

            result = self.lookup_summons(summons)
            result['row_number'] = idx + 4

            if result.get('status') == 'SUCCESS':
                print(f"[FOUND]")
                if 'balance_due' in result:
                    print(f"          Balance: {result['balance_due']}")
                if 'hearing_date' in result:
                    print(f"          Hearing: {result['hearing_date']}")
            elif result.get('status') == 'NOT_FOUND':
                print("[NOT FOUND]")
            else:
                print(f"[ERROR] {result.get('error', 'UNKNOWN ERROR')}")

            results.append(result)

            if idx < total:
                time.sleep(delay)

        return results

    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("\n[OK] Browser closed")


def read_summons_from_excel(file_path='ML TRACKING.xlsx'):
    """Read summons from column B, starting at row 5"""
    print(f"Reading summons from {file_path}...")
    df = pd.read_excel(file_path, header=None)
    summons_list = df.iloc[4:, 1].dropna().astype(str).str.strip().tolist()
    print(f"Found {len(summons_list)} summons")
    return summons_list


def save_results(results, filename_prefix='summons_results_v2'):
    """Save results to Excel and JSON"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    df = pd.DataFrame(results)
    excel_file = f'{filename_prefix}_{timestamp}.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"\n[OK] Results saved to: {excel_file}")

    json_file = f'{filename_prefix}_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"[OK] JSON backup saved to: {json_file}")

    return df, excel_file


def print_summary(results):
    """Print summary statistics"""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Found: {sum(1 for r in results if r.get('status') == 'SUCCESS')}")
    print(f"Not found: {sum(1 for r in results if r.get('status') == 'NOT_FOUND')}")
    print(f"Errors: {sum(1 for r in results if r.get('status') == 'ERROR')}")

    active = [r for r in results if r.get('status') == 'SUCCESS' and
              'balance_due' in r and
              r['balance_due'] not in ['0.00', '$0.00', '0']]

    if active:
        print(f"\n[WARNING] ACTIVE SUMMONS WITH BALANCE ({len(active)}):")
        for r in active[:10]:  # Show first 10
            hearing = r.get('hearing_date', 'No date')
            print(f"  {r['summons_number']}: ${r.get('balance_due', 'unknown')} - Hearing: {hearing}")
        if len(active) > 10:
            print(f"  ... and {len(active) - 10} more")


def main():
    """Main function"""
    print("NYC DOT Summons Lookup - Enhanced Version")
    print("=" * 60)

    print("\nOptions:")
    print("1. Run with visible browser")
    print("2. Run headless (faster)")

    choice = input("\nChoice (1 or 2, default=1): ").strip()
    headless = (choice == '2')

    try:
        summons_list = read_summons_from_excel('ML TRACKING.xlsx')

        if not summons_list:
            print("No summons found in Excel file")
            return

        print(f"First few: {summons_list[:5]}")
        print(f"\nReady to lookup {len(summons_list)} summons")
        response = input("Continue? (y/n): ").strip().lower()

        if response != 'y':
            print("Cancelled")
            return

    except FileNotFoundError:
        print("ML TRACKING.xlsx not found. Enter summons manually:")
        summons_input = input("Summons numbers (comma-separated): ")
        summons_list = [s.strip() for s in summons_input.split(',')]

    lookup = None
    try:
        lookup = SummonsSeleniumLookup(headless=headless)
        results = lookup.lookup_batch(summons_list, delay=3)

        df, excel_file = save_results(results)
        print_summary(results)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if lookup:
            lookup.close()


if __name__ == "__main__":
    main()
