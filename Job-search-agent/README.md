# European Job Search Agent

An AI-powered Python agent that searches for Data Engineer and Project Manager jobs across Europe, generates a tailored resume for each role using Google Gemini, uploads it to Google Drive, and compiles everything into a dated Excel file — ready for review.

---

## What it does

1. **Searches** LinkedIn and Indeed across European countries for your target roles
2. **Detects** visa sponsorship from job descriptions (Yes / No / Unknown)
3. **Filters** jobs by your priority countries and sponsorship preference
4. **Generates** a customized resume for each qualifying job using the Gemini AI API
5. **Uploads** each resume to Google Drive and records the shareable link
6. **Writes** all jobs + resume links to a dated Excel file (`output/excel/jobs_YYYY-MM-DD.xlsx`)

---

## Project structure

```
├── src/
│   ├── main.py               # Orchestrator — runs the full pipeline
│   ├── job_searcher.py       # LinkedIn + Indeed search via JobSpy
│   ├── visa_detector.py      # Keyword scan of JD → Yes / No / Unknown
│   ├── resume_customizer.py  # Gemini API → tailored DOCX per job
│   ├── drive_uploader.py     # Upload DOCX to Google Drive, return link
│   └── excel_writer.py       # openpyxl — one row per job with hyperlinks
├── setup/
│   └── verify_setup.py       # Smoke-test all integrations before first run
├── base_resume/              # Drop your resume here (.docx / .pdf / .txt)
├── output/
│   ├── excel/                # Daily Excel output files
│   └── resumes/              # Local copies of generated resumes
├── config.yaml               # All search settings — edit this to customize
├── .env                      # API keys (never commit this)
├── .env.example              # Template for .env
└── requirements.txt
```

---

## Quickstart

### 1. Clone and install dependencies

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
pip install -r requirements.txt
```

### 2. Add your resume

Place your resume file (`.docx`, `.pdf`, or `.txt`) inside the `base_resume/` folder.

### 3. Set up API keys

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — free |
| `GOOGLE_DRIVE_FOLDER_ID` | From your Google Drive folder URL |

### 4. Set up Google Drive access

Follow the steps in [SETUP.md](SETUP.md) to:
- Create a Google Cloud project
- Enable the Drive API
- Download `credentials.json`
- Run the one-time OAuth browser flow

### 5. Verify everything works

```bash
python setup/verify_setup.py
```

All checks should pass before running the full pipeline.

### 6. Run

```bash
# Test search only — no files written, no Drive uploads
python src/main.py --dry-run

# Full run — generates resumes, uploads to Drive, writes Excel
python src/main.py
```

---

## Configuration

All settings live in [`config.yaml`](config.yaml). Key options:

```yaml
search:
  roles:
    - "Data Engineer"
    - "Project Manager"

  max_jobs_per_search: 20      # Jobs per role per source per run

  days_old: 7                  # Only jobs posted in the last N days
                               # Use 1 for daily runs, 7 for testing

  priority_countries:          # Searched first, every run
    - NL  # Netherlands
    - DE  # Germany
    - IE  # Ireland
    - SE  # Sweden
    - GB  # UK
    # ... add/remove as needed

  extra_countries:             # Searched after priority ones
    - FR, AT, BE, CH ...

  resume_for_sponsorship:      # Which jobs get a tailored resume
    - "Yes"                    # Explicitly offers sponsorship
    - "Unknown"                # JD didn't mention it either way
```

---

## Excel output

Each run produces `output/excel/jobs_YYYY-MM-DD.xlsx` with these columns:

| Column | Description |
|---|---|
| # | Row number |
| Date Found | Date of this run |
| Company | Employer name |
| Role Title | Job title |
| Country | Country / location |
| Job Description Link | Clickable link to original posting |
| LinkedIn Link | LinkedIn URL (if from LinkedIn) |
| Visa Sponsorship | Yes / No / Unknown |
| Tailored Resume (Drive) | Clickable Google Drive link to your custom resume |
| Notes | Empty — fill in manually |

---

## Tech stack

| Component | Library / Service |
|---|---|
| Job search | [python-jobspy](https://github.com/Bunsly/JobSpy) (LinkedIn + Indeed) |
| AI resume writing | Google Gemini API (`gemini-2.5-flash-lite`) |
| Resume file I/O | `python-docx`, `pdfplumber` |
| Google Drive upload | `google-api-python-client`, `google-auth-oauthlib` |
| Excel generation | `openpyxl` |
| Config | `pyyaml`, `python-dotenv` |

---

## Limitations

- **Gemini free tier**: `gemini-2.5-flash-lite` has a daily request limit. If you hit it, the run logs a warning and skips remaining resumes — all jobs are still written to Excel.
- **LinkedIn scraping**: Uses an unofficial scraper (JobSpy). LinkedIn may throttle or block requests occasionally.
- **Visa detection**: Based on keyword matching. Many job descriptions don't mention sponsorship explicitly, so most results will show `Unknown`.

---

## Files that must not be committed

The `.gitignore` already excludes these — double-check before pushing:

- `.env` — contains your API key
- `credentials.json` — Google OAuth client secret
- `token.json` — Google OAuth token
- `base_resume/` — your personal resume
- `output/` — generated files

---

## License

MIT
