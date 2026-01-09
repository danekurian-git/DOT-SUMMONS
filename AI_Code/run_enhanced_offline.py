"""Run enhanced lookup using cached driver (no network needed)"""
import sys
import glob
sys.stdout.reconfigure(line_buffering=True)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from summons_selenium_v2 import (
    read_summons_from_excel,
    save_results,
    print_summary
)

# Import the lookup class but we'll override the __init__
from summons_selenium_v2 import SummonsSeleniumLookup

print("NYC DOT Summons Enhanced Batch Lookup (OFFLINE MODE)", flush=True)
print("=" * 60)
print("Using cached Chrome driver...\n")

# Find cached driver
driver_paths = glob.glob(r'C:\Users\danek/.wdm/drivers/chromedriver/win64/*/chromedriver-win32/chromedriver.exe')
if not driver_paths:
    print("ERROR: Cached Chrome driver not found!")
    print("Please run with internet connection once to download driver.")
    sys.exit(1)

driver_path = driver_paths[0]
print(f"Found driver: {driver_path}\n")

# Read summons
summons_list = read_summons_from_excel('ML TRACKING.xlsx')
print(f"Found {len(summons_list)} summons to process")
print(f"Estimated time: ~{len(summons_list) * 3 // 60} minutes\n")

# Create lookup instance with cached driver
print("Setting up browser...", flush=True)
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

service = ChromeService(executable_path=driver_path)

# Monkey-patch to use our driver
original_init = SummonsSeleniumLookup.__init__

def new_init(self, headless=True):
    from selenium.webdriver.support.ui import WebDriverWait
    self.driver = webdriver.Chrome(service=service, options=chrome_options)
    self.wait = WebDriverWait(self.driver, 10)
    print("[OK] Chrome browser initialized\n")

SummonsSeleniumLookup.__init__ = new_init

lookup = None
try:
    lookup = SummonsSeleniumLookup(headless=True)
    results = lookup.lookup_batch(summons_list, delay=2)

    df, excel_file = save_results(results)
    print_summary(results)

except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

finally:
    if lookup:
        lookup.close()

print("\nDone!")
