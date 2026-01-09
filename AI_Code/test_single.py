"""Quick test of a single summons"""
from summons_selenium import SummonsSeleniumLookup
import json

print("Testing with summons: 0703792522")
print("Opening browser...")

lookup = SummonsSeleniumLookup(headless=False)

try:
    result = lookup.lookup_summons('0703792522')

    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(json.dumps(result, indent=2))

    print("\n[OK] Test complete! Check if the data looks correct.")
    input("\nPress Enter to close browser...")

finally:
    lookup.close()
