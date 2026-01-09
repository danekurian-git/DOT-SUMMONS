# NYC DOT Summons Lookup Automation

Automated tools to lookup NYC DOT summons/violations from the NYC OATH website.

## Setup

1. Install required Python packages:
```bash
pip install -r requirements.txt
```

## Usage

### Option 1: Automated Batch Lookup (from Excel)

Use `summons_lookup.py` to automatically process multiple summons from your Excel file:

```bash
python summons_lookup.py
```

This script will:
- Read summons numbers from `ML TRACKING.xlsx`
- Auto-detect the column containing summons numbers
- Lookup each summons on the NYC website
- Save results to `summons_results_[timestamp].xlsx` and `.json`

**Features:**
- Automatic column detection (looks for columns with "summons", "violation", "ticket", etc.)
- Rate limiting (2 second delay between requests)
- Error handling and retry logic
- Saves both Excel and JSON formats
- Progress tracking

### Option 2: Simple Manual Lookup

Use `simple_lookup.py` for quick lookups of one or more summons:

```bash
python simple_lookup.py
```

Then enter summons number(s) when prompted:
- Single: `1234567890`
- Multiple: `1234567890, 0987654321, 1122334455`

Results are saved to `summons_results.json`

## Excel File Format

The script can read summons numbers from any Excel file. It will try to auto-detect the column, but you can also specify it in the code.

Expected format:
```
| Summons Number | ... other columns ...
|----------------|----------------------
| 1234567890     | ...
| 0987654321     | ...
```

## Output

Results include (when available):
- Summons/Violation Number
- Respondent Name
- Violation Type
- Violation Date
- Location
- Fine Amount
- Payment Status
- Hearing Information
- Any other fields from the OATH system

## Notes

- The script adds a 2-second delay between requests to be respectful to the server
- All results are timestamped
- Both Excel and JSON formats are generated for backup
- The script handles errors gracefully and reports them in the results

## Troubleshooting

**"Column not found" error:**
- Edit `summons_lookup.py` line ~177
- Specify your exact column name: `summons_list = read_summons_from_excel(excel_file, column_name='Your Column Name')`

**"Connection timeout" error:**
- The NYC website may be slow or down
- Try again later
- Increase timeout in the code (line ~36: `timeout=30` to higher value)

**Missing data in results:**
- The website's HTML structure may have changed
- Check `parse_response()` function in the script
- The raw HTML is saved in error cases for debugging

## Legal & Ethical Use

This tool is for personal use to lookup your own summons information. Please:
- Only lookup summons you are authorized to access
- Respect the server with reasonable delays between requests
- Do not use for commercial purposes without permission
