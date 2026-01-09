"""
NYC DOT Summons Lookup Automation
Automatically queries summons information from NYC OATH website
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime
import os


class SummonsLookup:
    def __init__(self):
        self.base_url = "https://a820-ecbticketfinder.nyc.gov"
        self.search_url = f"{self.base_url}/getViolationbyID.action"
        self.session = requests.Session()
        # Set headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': f'{self.base_url}/searchHome.action',
            'Content-Type': 'application/x-www-form-urlencoded'
        })

    def lookup_summons(self, summons_number):
        """
        Look up a single summons by number
        """
        try:
            # Prepare the POST data
            data = {
                'searchType': 'violationNumber',
                'violationNumber': str(summons_number).strip(),
                'searchBtn': 'Search'
            }

            print(f"Looking up summons: {summons_number}")

            # Make the POST request
            response = self.session.post(self.search_url, data=data, timeout=30)

            if response.status_code == 200:
                return self.parse_response(response.text, summons_number)
            else:
                return {
                    'summons_number': summons_number,
                    'status': 'ERROR',
                    'error': f'HTTP {response.status_code}'
                }

        except Exception as e:
            return {
                'summons_number': summons_number,
                'status': 'ERROR',
                'error': str(e)
            }

    def parse_response(self, html, summons_number):
        """
        Parse the HTML response to extract violation details
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = {
            'summons_number': summons_number,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Check for "No records found" or error messages
        error_div = soup.find('div', {'id': 'error'})
        if error_div and error_div.text.strip():
            result['status'] = 'NOT_FOUND'
            result['error'] = error_div.text.strip()
            return result

        # Look for violation details table
        # The structure may vary, so we'll extract all tables
        tables = soup.find_all('table')

        if not tables:
            result['status'] = 'NO_DATA'
            return result

        # Extract data from tables
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).replace(':', '')
                    value = cells[1].get_text(strip=True)

                    # Clean up the label to use as dictionary key
                    key = label.lower().replace(' ', '_').replace('/', '_')
                    if key and value:
                        result[key] = value

        result['status'] = 'SUCCESS'
        return result

    def lookup_batch(self, summons_list, delay=2):
        """
        Look up multiple summons with a delay between requests
        """
        results = []
        total = len(summons_list)

        for idx, summons in enumerate(summons_list, 1):
            print(f"Processing {idx}/{total}: {summons}")
            result = self.lookup_summons(summons)
            results.append(result)

            # Add delay to avoid overwhelming the server
            if idx < total:
                time.sleep(delay)

        return results

    def save_results(self, results, output_file='summons_results.xlsx'):
        """
        Save results to Excel file
        """
        df = pd.DataFrame(results)
        df.to_excel(output_file, index=False)
        print(f"\nResults saved to: {output_file}")

        # Also save as JSON for backup
        json_file = output_file.replace('.xlsx', '.json')
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"JSON backup saved to: {json_file}")

        return df


def read_summons_from_excel(file_path, column_name=None):
    """
    Read summons numbers from an Excel file

    Args:
        file_path: Path to Excel file
        column_name: Name of column containing summons numbers (optional)

    Returns:
        List of summons numbers
    """
    df = pd.read_excel(file_path)

    print(f"Columns found in file: {list(df.columns)}")

    if column_name:
        if column_name in df.columns:
            summons_list = df[column_name].dropna().tolist()
        else:
            raise ValueError(f"Column '{column_name}' not found in Excel file")
    else:
        # Try to auto-detect the column with summons numbers
        possible_columns = [col for col in df.columns if
                          any(keyword in col.lower() for keyword in
                              ['summons', 'violation', 'ticket', 'notice', 'number'])]

        if possible_columns:
            print(f"Auto-detected summons column: {possible_columns[0]}")
            summons_list = df[possible_columns[0]].dropna().tolist()
        else:
            # Use first column
            print("Using first column for summons numbers")
            summons_list = df.iloc[:, 0].dropna().tolist()

    # Clean the summons numbers
    summons_list = [str(s).strip() for s in summons_list if str(s).strip() and str(s).lower() != 'nan']

    return summons_list


def main():
    """
    Main function - can be customized based on your needs
    """
    print("NYC DOT Summons Lookup Automation")
    print("=" * 50)

    # Option 1: Read from your Excel file
    excel_file = "ML TRACKING.xlsx"

    if os.path.exists(excel_file):
        print(f"\nReading summons from: {excel_file}")

        # You may need to specify the column name containing summons numbers
        # For now, we'll try to auto-detect it
        summons_list = read_summons_from_excel(excel_file)

        print(f"\nFound {len(summons_list)} summons to look up")
        print(f"First few: {summons_list[:5]}")

        # Ask for confirmation
        response = input("\nProceed with lookup? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
    else:
        # Option 2: Manual entry
        print(f"\nExcel file '{excel_file}' not found.")
        print("Enter summons numbers (comma-separated):")
        summons_input = input("> ")
        summons_list = [s.strip() for s in summons_input.split(',')]

    if not summons_list:
        print("No summons numbers provided")
        return

    # Perform the lookup
    lookup = SummonsLookup()
    print(f"\nStarting lookup for {len(summons_list)} summons...")
    print("This may take a few minutes...\n")

    results = lookup.lookup_batch(summons_list, delay=2)

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"summons_results_{timestamp}.xlsx"
    df = lookup.save_results(results, output_file)

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total processed: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r.get('status') == 'SUCCESS')}")
    print(f"Not found: {sum(1 for r in results if r.get('status') == 'NOT_FOUND')}")
    print(f"Errors: {sum(1 for r in results if r.get('status') == 'ERROR')}")
    print("\nResults saved to:", output_file)


if __name__ == "__main__":
    main()
