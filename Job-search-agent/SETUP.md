# European Job Search Agent — Setup Guide

This guide walks you through the one-time setup needed to run the agent.

---

## Prerequisites

- Python 3.10 or newer
- A Google account (for Google Drive)
- An Anthropic account (for Claude API)

---

## Step 1 — Install Python dependencies

Open a terminal in the project root and run:

```
pip install -r requirements.txt
```

---

## Step 2 — Add your resume

Place your resume file in the `base_resume/` folder. Supported formats:

- `resume.docx` (recommended — best formatting control)
- `resume.pdf`
- `resume.txt`

The agent reads this file as the base for all customizations.

---

## Step 3 — Get your Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign in (or create a free account)
3. Click **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-...`)

---

## Step 4 — Set up Google Drive API

### 4a. Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Click the project dropdown at the top → **New Project**
3. Name it `job-search-agent` → **Create**

### 4b. Enable the Google Drive API

1. In your new project, go to **APIs & Services** → **Library**
2. Search for `Google Drive API` → click it → **Enable**

### 4c. Create OAuth 2.0 credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. If prompted to configure the consent screen:
   - Choose **External** → **Create**
   - Fill in App name: `Job Search Agent`, your email for support and developer email
   - Click **Save and Continue** through all screens
   - On the **Test users** screen, add your own Google email → **Save**
4. Back on Credentials → **+ Create Credentials** → **OAuth client ID**
5. Application type: **Desktop app**
6. Name: `Job Search Agent Desktop`
7. Click **Create** → **Download JSON**
8. Rename the downloaded file to `credentials.json` and place it in the **project root** (next to `config.yaml`)

### 4d. Create the Drive folder

1. Open [Google Drive](https://drive.google.com/)
2. Click **+ New** → **New folder**
3. Name it `Job Search Resumes`
4. Open the folder — look at the URL:
   ```
   https://drive.google.com/drive/folders/1ABC123XYZ_your_folder_id_here
   ```
5. Copy the ID at the end (everything after `/folders/`)

---

## Step 5 — Create your .env file

Copy the example:

```
copy .env.example .env
```

Then open `.env` in a text editor and fill in:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_DRIVE_FOLDER_ID=1ABC123XYZ_your_folder_id_here
```

---

## Step 6 — Run setup verification

```
python setup/verify_setup.py
```

This checks that all dependencies, API keys, and files are in place. Fix any issues it reports before continuing.

---

## Step 7 — First run (triggers Google auth)

The first time you run the agent, it will open a browser window asking you to authorize access to your Google Drive. This only happens once — the token is saved to `token.json` for future runs.

```
python src/main.py --dry-run
```

This runs the job search and prints results to the terminal without writing files or uploading anything. Confirm the jobs look right.

Then run the full pipeline:

```
python src/main.py
```

Your Excel file will appear in `output/excel/jobs_YYYY-MM-DD.xlsx` and resumes in your Google Drive folder.

---

## Step 8 — Schedule daily runs at 7:00 AM

Open PowerShell **as Administrator** and run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
cd "d:\Admin_Vedant\Projects\Job-applier\Mine_agentic_job_applier"
.\setup\setup_scheduler.ps1
```

The agent will now run automatically every morning at 7:00 AM.

To manually trigger it anytime:

```powershell
Start-ScheduledTask -TaskName "EuroJobSearchAgent"
```

To check the log:

```powershell
Get-Content "output\agent.log" -Tail 50
```

---

## Customizing the search

Edit `config.yaml` to adjust:

- `search.roles` — add or remove job titles
- `search.max_jobs_per_search` — increase if you want more results (watch rate limits)
- `search.days_old` — how many days back to search (default: 1 for daily runs)
- `search.eu_countries` — remove countries you don't want

---

## Troubleshooting

**"No resume file found"** — Make sure your resume is in `base_resume/` with a `.docx`, `.pdf`, or `.txt` extension.

**"ANTHROPIC_API_KEY is not set"** — Confirm your `.env` file exists in the project root and has the correct key.

**"Google credentials file not found"** — Make sure `credentials.json` is in the project root (not inside a subfolder).

**LinkedIn returns 0 jobs** — LinkedIn rate-limits scrapers. Wait a few minutes and retry, or reduce `max_jobs_per_search` to 15.

**Drive token expired** — Delete `token.json` and re-run; a new browser OAuth flow will run automatically.
