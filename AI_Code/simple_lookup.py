"""
Simple script to lookup a single summons or a manual list
Use this if you just want to test or lookup a few summons numbers
"""

import requests
from bs4 import BeautifulSoup
import json

def lookup_summons(summons_number):
    """Look up a single summons number"""
    url = "https://a820-ecbticketfinder.nyc.gov/getViolationbyID.action"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://a820-ecbticketfinder.nyc.gov/searchHome.action',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'searchType': 'violationNumber',
        'violationNumber': str(summons_number).strip(),
        'searchBtn': 'Search'
    }

    print(f"\nLooking up summons: {summons_number}")
    print("-" * 50)

    try:
        response = requests.post(url, data=data, headers=headers, timeout=30)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for errors
            error_div = soup.find('div', {'id': 'error'})
            if error_div and error_div.text.strip():
                print(f"ERROR: {error_div.text.strip()}")
                return None

            # Extract all tables
            tables = soup.find_all('table')
            result = {}

            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).replace(':', '')
                        value = cells[1].get_text(strip=True)
                        if label and value:
                            result[label] = value

            if result:
                print("Found information:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
                return result
            else:
                print("No violation data found")
                return None
        else:
            print(f"HTTP Error: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


if __name__ == "__main__":
    print("NYC Summons Lookup")
    print("=" * 50)

    # Method 1: Single summons lookup
    summons = input("Enter summons number (or comma-separated list): ")

    summons_list = [s.strip() for s in summons.split(',')]

    results = []
    for s in summons_list:
        result = lookup_summons(s)
        if result:
            results.append({
                'summons_number': s,
                'data': result
            })

    # Save results to JSON
    if results:
        output_file = "summons_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n\nResults saved to: {output_file}")
