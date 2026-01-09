"""
NYC DOT Summons Lookup using Selenium (Browser Automation)
Automates the manual process of looking up summons on the NYC website
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
import json


class SummonsSeleniumLookup:
    def __init__(self, headless=False):
        """
        Initialize the browser

        Args:
            headless: If True, runs browser in background without opening window
        """
        chrome_options = Options()

        if headless:
            chrome_options.add_argument('--headless')

        # Disable bot detection features
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Initialize the driver
        print("Setting up browser driver...")
        try:
            # Try to use cached driver first to avoid network issues
            import os
            os.environ['WDM_LOCAL'] = '1'  # Use local cache
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
        """
        Look up a single summons number
        """
        try:
            # Navigate to the search page
            url = "https://a820-ecbticketfinder.nyc.gov/searchHome.action"
            self.driver.get(url)

            # Wait for page to load
            time.sleep(1)

            # Find the summons number input field
            # Try different possible selectors
            summons_input = None
            try:
                summons_input = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "searchViolationObject.violationNo"))
                )
            except:
                try:
                    summons_input = self.driver.find_element(By.ID, "violationNo")
                except:
                    # Find by any input that looks like a summons field
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        if inp.get_attribute("type") == "text":
                            summons_input = inp
                            break

            if not summons_input:
                return {
                    'summons_number': summons_number,
                    'status': 'ERROR',
                    'error': 'Could not find summons input field'
                }

            # Clear and enter summons number
            summons_input.clear()
            summons_input.send_keys(str(summons_number))

            # Find and click the search button
            search_button = None
            try:
                # Try to find by value
                search_button = self.driver.find_element(By.CSS_SELECTOR, "input[value*='Search']")
            except:
                try:
                    search_button = self.driver.find_element(By.NAME, "submit")
                except:
                    # Find any submit button
                    buttons = self.driver.find_elements(By.TAG_NAME, "input")
                    for btn in buttons:
                        if btn.get_attribute("type") == "submit":
                            search_button = btn
                            break

            if not search_button:
                return {
                    'summons_number': summons_number,
                    'status': 'ERROR',
                    'error': 'Could not find search button'
                }

            # Click search
            search_button.click()

            # Wait for results to load
            time.sleep(2)

            # Extract the results
            return self.extract_results(summons_number)

        except Exception as e:
            return {
                'summons_number': summons_number,
                'status': 'ERROR',
                'error': str(e)
            }

    def extract_results(self, summons_number):
        """
        Extract violation details from the results page
        """
        result = {
            'summons_number': summons_number,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            # Check for "No Record Available"
            page_source = self.driver.page_source
            if "No Record Available" in page_source:
                result['status'] = 'NOT_FOUND'
                result['note'] = 'No Record Available'
                return result

            # Find all tables with violation data
            # The page has multiple tables: vioContent (Case Details) and details (More Details)
            tables = self.driver.find_elements(By.TAG_NAME, "table")

            for table in tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            label = cells[0].text.strip().replace(':', '')
                            value = cells[1].text.strip()

                            if label and value and len(label) < 50:  # Reasonable label length
                                # Clean up the label for use as dictionary key
                                key = label.lower().replace(' ', '_').replace('/', '_')

                                # Skip if value is just a button or irrelevant
                                if value and not value.startswith('http') and len(value) < 500:
                                    result[key] = value
                except:
                    continue

            # Determine status
            if len(result) > 3:  # More than just summons_number, timestamp, and status
                result['status'] = 'SUCCESS'
            else:
                result['status'] = 'NO_DATA'

            return result

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            return result

    def lookup_batch(self, summons_list, delay=3):
        """
        Look up multiple summons numbers

        Args:
            summons_list: List of summons numbers
            delay: Seconds to wait between lookups (default 3)
        """
        results = []
        total = len(summons_list)

        print(f"\nStarting lookup of {total} summons...")
        print("=" * 60)

        for idx, summons in enumerate(summons_list, 1):
            print(f"[{idx}/{total}] Processing: {summons}", end=' ')

            result = self.lookup_summons(summons)
            result['row_number'] = idx + 4  # Excel row number (assuming data starts at row 5)

            if result.get('status') == 'SUCCESS':
                print(f"[FOUND]")
                if 'balance_due' in result:
                    print(f"          Balance: {result['balance_due']}")
            elif result.get('status') == 'NOT_FOUND':
                print("[NOT FOUND]")
            else:
                print(f"[ERROR] {result.get('error', 'UNKNOWN ERROR')}")

            results.append(result)

            # Add delay between requests
            if idx < total:
                time.sleep(delay)

        return results

    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("\n[OK] Browser closed")


def read_summons_from_excel(file_path='ML TRACKING.xlsx'):
    """
    Read summons from column B, starting at row 5
    """
    print(f"Reading summons from {file_path}...")
    df = pd.read_excel(file_path, header=None)

    # Column B is index 1, row 5 is index 4
    summons_list = df.iloc[4:, 1].dropna().astype(str).str.strip().tolist()

    print(f"Found {len(summons_list)} summons")
    return summons_list


def save_results(results, filename_prefix='summons_results'):
    """
    Save results to Excel and JSON
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save to Excel
    df = pd.DataFrame(results)
    excel_file = f'{filename_prefix}_{timestamp}.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"\n[OK] Results saved to: {excel_file}")

    # Save to JSON
    json_file = f'{filename_prefix}_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"[OK] JSON backup saved to: {json_file}")

    return df, excel_file


def print_summary(results):
    """
    Print summary statistics
    """
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Found: {sum(1 for r in results if r.get('status') == 'SUCCESS')}")
    print(f"Not found: {sum(1 for r in results if r.get('status') == 'NOT_FOUND')}")
    print(f"Errors: {sum(1 for r in results if r.get('status') == 'ERROR')}")

    # Show active summons with balances
    active = [r for r in results if r.get('status') == 'SUCCESS' and
              'balance_due' in r and
              r['balance_due'] not in ['0.00', '$0.00', '0']]

    if active:
        print(f"\n[WARNING] ACTIVE SUMMONS WITH BALANCE ({len(active)}):")
        for r in active:
            print(f"  {r['summons_number']}: ${r.get('balance_due', 'unknown')}")


def main():
    """
    Main function
    """
    print("NYC DOT Summons Lookup - Selenium Automation")
    print("=" * 60)

    # Ask user preferences
    print("\nOptions:")
    print("1. Run with visible browser (you can watch the automation)")
    print("2. Run headless (faster, no browser window)")

    choice = input("\nChoice (1 or 2, default=1): ").strip()
    headless = (choice == '2')

    # Read summons from Excel
    try:
        summons_list = read_summons_from_excel('ML TRACKING.xlsx')

        if not summons_list:
            print("No summons found in Excel file")
            return

        print(f"First few: {summons_list[:5]}")
        print(f"Last few: {summons_list[-5:]}")

        # Confirm
        print(f"\nReady to lookup {len(summons_list)} summons")
        response = input("Continue? (y/n): ").strip().lower()

        if response != 'y':
            print("Cancelled")
            return

    except FileNotFoundError:
        print("ML TRACKING.xlsx not found. Enter summons manually:")
        summons_input = input("Summons numbers (comma-separated): ")
        summons_list = [s.strip() for s in summons_input.split(',')]

    # Initialize browser and run lookup
    lookup = None
    try:
        lookup = SummonsSeleniumLookup(headless=headless)
        results = lookup.lookup_batch(summons_list, delay=3)

        # Save results
        df, excel_file = save_results(results)

        # Print summary
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
