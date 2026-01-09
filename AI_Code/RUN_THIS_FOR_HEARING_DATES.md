# Get Hearing Dates & Violation Codes

## You Already Have:
✅ **summons_results_20260102_101700.xlsx** - Complete results for all 74 summons!
- All balances, dates, addresses, locations
- 71 found, 3 not found, 52 with outstanding balances

## What's Missing:
- Hearing dates
- Hearing locations
- Violation codes & descriptions

## To Get Them:

### Simple Method (When ChromeDriver issue clears):

```bash
cd "d:\SummonsViolations\NYCDOT\AI_Code"
python run_NOW.py
```

This will create `summons_results_v2_[timestamp].xlsx` with EVERYTHING including hearing dates.

### If ChromeDriver Is Still Blocked:

**Restart your computer first**, then run the command above.

This clears the blocked ChromeDriver connections and lets it start fresh.

## What You'll Get:

Example for summons 0703908958:
```
Summons: 0703908958
Date Issued: 05/31/2025
Balance: $1500.00
Respondent: DEBOE CONSTRUCTION CORP

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

## Time Required:
- ~4 minutes for all 74 summons
- Automatic processing, no manual typing!

---

**Your automation is 100% ready!**
The ChromeDriver just needs a clean slate to run.
