# NYC DOT NOV Automation System - Master Plan

## Vision
Fully automated system that monitors email, downloads NOVs, analyzes violations, generates AI-powered counter-arguments, and submits responses to NYC DOT portal.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMAIL MONITORING                              │
│  Monitor: dashnov@dot.nyc.gov                                   │
│  Extract: NOV PDFs + Summons Numbers                            │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NOV PARSER                                    │
│  Parse PDF: Extract summons #, violation code, description      │
│  Store: Local database of violations                            │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OATH LOOKUP (✓ BUILT!)                       │
│  Query: https://a820-ecbticketfinder.nyc.gov                   │
│  Get: Hearing dates, status, prior results                      │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CASE ANALYZER                                 │
│  Compare: Current violation vs historical cases                 │
│  Identify: Patterns in DISMISSED vs IN VIOLATION                │
│  Extract: Winning arguments from past successes                 │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI ARGUMENT GENERATOR                         │
│  Input: Violation details + Historical patterns                 │
│  API: Claude/GPT-4 for legal argument generation                │
│  Output: Structured counter-argument with evidence              │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PORTAL SUBMISSION                             │
│  Navigate: NYC DOT response portal                              │
│  Upload: Counter-argument + supporting documents                │
│  Confirm: Submission receipt                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Email Integration ⏳ PENDING

### Objective
Automatically download NOV PDFs from dashnov@dot.nyc.gov

### Components Needed

**1.1 Email Client Integration**
- Library: `imaplib` (built-in) or `exchangelib` for Exchange
- Connection: IMAP/OAuth to email account
- Filter: Sender = dashnov@dot.nyc.gov
- Download: PDF attachments

**1.2 NOV Storage**
- Directory: `NOVs/raw/`
- Naming: `NOV_{summons}_{date}.pdf`
- Tracking: SQLite database of processed emails

### Technical Considerations
- Email credentials (use env vars or keyring)
- Mark emails as processed (avoid re-downloading)
- Handle multiple attachments per email
- Error handling for network issues

### File Structure
```
NOVs/
├── raw/              # Downloaded PDFs
├── processed/        # Successfully parsed NOVs
├── failed/           # Failed to parse
└── database.db       # Tracking database
```

---

## Phase 2: NOV Parser ⏳ PENDING

### Objective
Extract structured data from NOV PDFs

### Components Needed

**2.1 PDF Text Extraction**
- Library: `PyPDF2`, `pdfplumber`, or `pypdf`
- Extract: All text from PDF
- OCR: `pytesseract` if scanned images

**2.2 Data Extraction Patterns**
Extract these fields:
- Summons Number (e.g., 0703908958)
- Violation Code (e.g., AD01, AD30)
- Violation Description
- Date Issued
- Hearing Date (if scheduled)
- Respondent Name
- Location/Address
- Fine Amount

**2.3 Structured Storage**
```json
{
  "summons_number": "0703908958",
  "violation_code": "AD01",
  "description": "USE OPENING OF STREET W O PERMIT",
  "date_issued": "05/31/2025",
  "hearing_date": "06/08/2026",
  "location": "123 Main St, Brooklyn",
  "fine_amount": "$1500.00",
  "pdf_path": "NOVs/raw/NOV_0703908958_20250531.pdf",
  "parsed_date": "2026-01-06 18:30:00"
}
```

### Validation
- Verify summons number format (10 digits)
- Cross-check with OATH database
- Flag discrepancies

---

## Phase 3: OATH Database Integration ✅ COMPLETE

### Status
**ALREADY BUILT!**

### Existing Components
- `run_NOW.py` - Batch lookup script
- `analyze_results.py` - Results analysis
- Data extraction includes:
  - Hearing dates
  - Hearing results (DISMISSED/IN VIOLATION/DEFAULTED)
  - Balance due
  - Status updates

### Enhancement Needed
- Real-time lookup function (not just batch)
- Integration with NOV parser output
- Historical case database

---

## Phase 4: Case Analyzer ⏳ PENDING

### Objective
Build a knowledge base from historical cases to identify winning patterns

### Components Needed

**4.1 Historical Case Database**
```sql
CREATE TABLE violations (
  id INTEGER PRIMARY KEY,
  summons_number TEXT,
  violation_code TEXT,
  description TEXT,
  hearing_result TEXT,  -- DISMISSED, IN VIOLATION, DEFAULTED
  hearing_date DATE,
  arguments_used TEXT,  -- If we submitted response
  outcome_notes TEXT
);
```

**4.2 Pattern Analysis**
For each violation code:
- Success rate (% DISMISSED)
- Common defenses that worked
- Common prosecution arguments
- Time patterns (certain judges more lenient?)

**4.3 Similarity Matching**
- Find similar past cases
- Compare violation codes, locations, circumstances
- Extract successful arguments from similar DISMISSED cases

---

## Phase 5: AI Argument Generator ⏳ PENDING

### Objective
Generate legal counter-arguments using AI based on violation specifics and historical patterns

### Components Needed

**5.1 AI Integration**
- API: Anthropic Claude or OpenAI GPT-4
- Model: Claude 3.5 Sonnet (best for legal reasoning)
- Prompt engineering for legal arguments

**5.2 Prompt Structure**
```
You are a legal expert specializing in NYC DOT violations.

CURRENT VIOLATION:
- Code: {violation_code}
- Description: {description}
- Date: {date_issued}
- Location: {location}

HISTORICAL CONTEXT:
- This violation code has {success_rate}% dismissal rate
- Common successful defenses:
  {winning_arguments_list}

SIMILAR DISMISSED CASES:
{similar_cases}

Generate a structured counter-argument that:
1. Challenges the violation on procedural grounds
2. Provides factual defense
3. Cites relevant NYC regulations
4. Requests dismissal or reduction

Format: Professional, concise, legally sound
```

**5.3 Output Format**
```json
{
  "argument_summary": "Request for dismissal based on...",
  "procedural_challenges": [...],
  "factual_defense": [...],
  "legal_citations": [...],
  "supporting_evidence_needed": [...],
  "full_text": "..."
}
```

---

## Phase 6: Portal Submission ⏳ PENDING

### Objective
Automate submission of counter-arguments to NYC DOT portal

### Components Needed

**6.1 Portal Reconnaissance** (NEED TO INVESTIGATE)
- Find response submission URL
- Identify form fields
- Authentication method
- File upload requirements

**6.2 Selenium Automation**
- Navigate to portal
- Login (if required)
- Fill response form
- Upload supporting documents
- Submit and capture confirmation

**6.3 Submission Tracking**
- Store submission timestamp
- Capture confirmation number
- Monitor for response from DOT
- Alert if deadline approaching

---

## Data Flow Example

### Complete Workflow
```
1. EMAIL RECEIVED
   From: dashnov@dot.nyc.gov
   Subject: Notice of Violation - Summons 0704012760
   Attachment: NOV_0704012760.pdf

2. PDF PARSED
   {
     "summons": "0704012760",
     "code": "AD01",
     "description": "USE OPENING OF STREET W O PERMIT",
     "date": "09/26/2025",
     "hearing": "01/08/2026"
   }

3. OATH LOOKUP
   {
     "hearing_date": "01/08/2026",
     "hearing_location": "Brooklyn",
     "balance": "$1500.00",
     "status": "NEW ISSUANCE"
   }

4. CASE ANALYSIS
   {
     "violation_code": "AD01",
     "historical_dismissal_rate": 35.7%,
     "similar_dismissed_cases": 5,
     "winning_arguments": [
       "Permit was valid at time of work",
       "Emergency repair exception",
       "Signage was obscured/missing"
     ]
   }

5. AI GENERATION
   "To the Administrative Law Judge,

   I respectfully request dismissal of summons 0704012760...

   [Full legal argument]"

6. PORTAL SUBMISSION
   ✓ Logged into DOT portal
   ✓ Uploaded counter-argument
   ✓ Confirmation #: DOT-2026-012760-RESP
   ✓ Email confirmation received
```

---

## Technology Stack

### Core Libraries
- **Email:** `imaplib` / `exchangelib`
- **PDF Parsing:** `pdfplumber` / `PyPDF2`
- **Web Scraping:** `selenium` + `beautifulsoup4` (already using)
- **Database:** `sqlite3` (built-in)
- **AI API:** `anthropic` SDK or `openai`
- **Data Analysis:** `pandas`

### Additional Dependencies
```txt
# Already installed:
selenium>=4.0.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
openpyxl>=3.1.0

# New dependencies:
pdfplumber>=0.10.0
anthropic>=0.18.0
python-dotenv>=1.0.0
schedule>=1.2.0  # For periodic email checks
```

---

## Security Considerations

### Credentials Management
- Email password: Environment variable or Windows Credential Manager
- AI API key: Environment variable
- DOT portal credentials: Encrypted storage

### File Security
- NOV PDFs may contain sensitive info
- Restrict file permissions
- Consider encryption at rest

### API Rate Limits
- Claude API: Monitor token usage
- OATH portal: Respect rate limits (we already use 2-3s delays)
- Email: Reasonable polling interval (every 30 min?)

---

## Deployment Strategy

### Phase Rollout
1. **Phase 1-2:** Manual triggering (download + parse on demand)
2. **Phase 3-4:** Semi-automated (lookup + analyze, human reviews AI output)
3. **Phase 5:** Full automation with human approval step
4. **Phase 6:** Fully autonomous with alert notifications

### Testing Strategy
- Test with old/resolved NOVs first
- Dry-run mode for portal submission
- Human review before actual submission
- Gradual confidence building

---

## Success Metrics

### Efficiency Gains
- Time saved per NOV: ~2 hours manual → 5 minutes automated
- Processing 74 NOVs: 148 hours → 6 hours (96% reduction)

### Financial Impact
- Potential savings from DISMISSED cases
- Track: Dismissal rate before vs after AI arguments
- ROI on AI API costs vs legal consultation fees

### Quality Metrics
- Argument quality (subjective review)
- Dismissal rate improvement
- Reduction in DEFAULTED cases (never miss deadlines)

---

## Next Steps

### Immediate Actions
1. Create email integration module
2. Build PDF parser with test NOVs
3. Enhance OATH lookup for real-time queries
4. Set up AI API account and test prompts

### Questions to Answer
1. What email protocol does your account use? (IMAP/Exchange/Office365)
2. Do you have sample NOV PDFs we can test parsing on?
3. Is there an existing DOT portal for submitting responses? What's the URL?
4. AI preference: Claude (Anthropic) or GPT-4 (OpenAI)?

---

## Current Status Summary

| Phase | Component | Status | Priority |
|-------|-----------|--------|----------|
| 1 | Email Integration | 🔴 Not Started | HIGH |
| 2 | PDF Parser | 🔴 Not Started | HIGH |
| 3 | OATH Lookup | ✅ Complete | - |
| 3 | Historical Database | 🟡 Partial (have data) | MEDIUM |
| 4 | Case Analyzer | 🔴 Not Started | MEDIUM |
| 5 | AI Generator | 🔴 Not Started | HIGH |
| 6 | Portal Submission | 🔴 Not Started | LOW (investigate first) |

---

**Last Updated:** 2026-01-06
**Next Review:** After Phase 1 complete
