"""Run the enhanced batch lookup with hearing dates and charges"""
import sys
sys.stdout.reconfigure(line_buffering=True)

from summons_selenium_v2 import (
    SummonsSeleniumLookup,
    read_summons_from_excel,
    save_results,
    print_summary
)

print("NYC DOT Summons Enhanced Batch Lookup", flush=True)
print("=" * 60)
print("This version captures:")
print("  - Hearing dates")
print("  - Violation charges (code, section, description)")
print("  - All other summons details")
print()

summons_list = read_summons_from_excel('ML TRACKING.xlsx')
print(f"\nFound {len(summons_list)} summons to process")
print(f"Estimated time: ~{len(summons_list) * 3 // 60} minutes\n")

# Run in headless mode for speed
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
