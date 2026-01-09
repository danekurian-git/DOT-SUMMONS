# NYC DOT Summons Automation

## Quick Start

To lookup all summons with **hearing dates and violation charges**:

```bash
cd AI_Code
python run_NOW.py
```

Results will be saved to the main folder as `summons_results_v2_[timestamp].xlsx`

## Your Data

**Current Results:** [summons_results_20260102_101700.xlsx](summons_results_20260102_101700.xlsx)
- 74 summons processed
- 71 found, 3 not found
- 52 with outstanding balances

## Files

- **ML TRACKING.xlsx** - Your original summons list (Column B, Row 5+)
- **summons_results_*.xlsx** - Results from automation
- **summons_results_*.json** - JSON backup
- **AI_Code/** - All automation scripts

## What the Enhanced Script Captures

- ✅ Hearing dates (e.g., "06/08/2026")
- ✅ Hearing locations (e.g., "Bronx")
- ✅ Violation codes (e.g., "AD01")
- ✅ Violation descriptions (e.g., "USE OPENING OF STREET W O PERMIT")
- ✅ All basic summons info (dates, balances, addresses, etc.)

## Documentation

See [AI_Code/README_FINAL.md](AI_Code/README_FINAL.md) for complete documentation.

## Need Help?

All scripts are in the `AI_Code` folder with detailed comments.
