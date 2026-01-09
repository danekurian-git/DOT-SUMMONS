# NYC DOT Summons Automation - COMPLETE SOLUTION

## Summary

You have **TWO versions** of the automation:

### Version 1: Basic (✅ COMPLETED)
**File:** `summons_results_20260102_101700.xlsx`

**Captured Data:**
- Summons number, date issued, agency
- Respondent name and address
- Balance due, inspection location
- Status

**Results:**
- 74 summons processed
- 71 found, 3 not found
- 52 with outstanding balances

### Version 2: Enhanced (⭐ RECOMMENDED)
**File:** `summons_selenium_v2.py`

**Additional Data Captured:**
- ✅ **Hearing Date** (e.g., 06/08/2026)
- ✅ **Hearing Location** (e.g., Bronx)
- ✅ **Hearing Status** (e.g., RESCHEDULED)
- ✅ **Violation Code** (e.g., AD01)
- ✅ **Violation Section** (e.g., A.C. 19-102(I))
- ✅ **Violation Description** (e.g., "USE OPENING OF STREET W O PERMIT")
- ✅ **Face Amount** (e.g., $1500.00)

## How to Run Enhanced Version

```bash
cd "d:\SummonsViolations\NYCDOT"
python run_enhanced.py
```

**OR** run the main script directly:

```bash
python summons_selenium_v2.py
```

## Example Output from Enhanced Version

For summons **0703908958**:
```
Summons Number: 0703908958
Date Issued: 05/31/2025
Respondent: DEBOE CONSTRUCTION CORP
Balance Due: $1500.00

HEARING INFO:
  Date: 06/08/2026
  Location: Bronx
  Status: RESCHEDULED

VIOLATION:
  Code: AD01
  Section: A.C. 19-102(I)
  Description: USE OPENING OF STREET W O PERMIT
  Face Amount: $1500.00
```

## Files Created

### Scripts:
- `summons_selenium.py` - Original version
- `summons_selenium_v2.py` - **Enhanced version with hearing dates & charges**
- `run_batch.py` - Run basic batch
- `run_enhanced.py` - **Run enhanced batch** ⭐
- `simple_lookup.py` - Test single summons

### Results (from first run):
- `summons_results_20260102_101700.xlsx` - Excel with all 74 summons
- `summons_results_20260102_101700.json` - JSON backup
- `batch_log.txt` - Processing log

### Dependencies:
- `requirements.txt` - Python packages needed

## Summons with Outstanding Balances

From the first run, **52 summons** have outstanding balances:

**Highest Balances:**
- $1,800: 0704059539, 0704075680
- $1,530: 0703874629, 0703874638
- $1,500: 0703908958, 0703908967, 0703922369, 0703922414, 0703922432, 0703922441, 0703922460, 0704012760
- $1,230: 0703995005, 0703995041
- $1,200: 14 summons (see Excel file)

And many more ranging from $100 to $1,030.

## Troubleshooting

### "Could not initialize browser" error:
This happens when the webdriver can't download due to network issues.

**Solution:** The driver is already cached from the first successful run, so just try running again:

```bash
python run_enhanced.py
```

If it still fails, try:
1. Close all Chrome/Edge windows
2. Restart your computer
3. Run the script again

### Want to lookup just a few summons?
Use the simple script:

```bash
python simple_lookup.py
```

Then enter your summons numbers separated by commas.

## Future Use

To lookup your summons in the future:

1. **Update your Excel file** ([ML TRACKING.xlsx](ML TRACKING.xlsx)) with new summons in column B (starting row 5)
2. **Run the enhanced script:**
   ```bash
   cd "d:\SummonsViolations\NYCDOT"
   python run_enhanced.py
   ```
3. Results will be saved to `summons_results_v2_[timestamp].xlsx`

## What This Saves You

**Manual Process:**
- 74 summons × 2 minutes each = **~2.5 hours of manual typing**

**Automated:**
- 74 summons × 3 seconds each = **~4 minutes**

**Time Saved: 2+ hours!** ⏱️

Plus you get:
- ✅ All data in organized Excel format
- ✅ JSON backup for programmatic use
- ✅ No typing errors
- ✅ Complete records including hearing dates and violation codes

---

## Technical Notes

- Uses Selenium WebDriver for browser automation
- BeautifulSoup for HTML parsing
- Respects server with 2-3 second delays between requests
- Handles hidden/collapsed sections on the NYC website
- Works with Chrome or Edge (auto-detects)
- Can run headless (no browser window) for faster processing
