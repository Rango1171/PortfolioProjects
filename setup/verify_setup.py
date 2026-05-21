"""
Smoke-test for the European Job Search Agent.
Run this BEFORE your first full run to confirm all integrations are working.

Usage: python setup/verify_setup.py
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"
WARN = "\033[93m WARN\033[0m"


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = PASS if ok else FAIL
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))
    return ok


def main():
    print("\n European Job Search Agent — Setup Verification\n" + "=" * 50)
    all_ok = True

    # 1. Python version
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    all_ok &= check("Python >= 3.10", ok, f"Found {v.major}.{v.minor}.{v.micro}")

    # 2. Required packages
    packages = [
        ("google.genai", "google-genai"),
        ("openai", "openai"),
        ("jobspy", "python-jobspy"),
        ("googleapiclient", "google-api-python-client"),
        ("google_auth_oauthlib", "google-auth-oauthlib"),
        ("openpyxl", "openpyxl"),
        ("docx", "python-docx"),
        ("pdfplumber", "pdfplumber"),
        ("requests", "requests"),
        ("bs4", "beautifulsoup4"),
        ("yaml", "pyyaml"),
        ("dotenv", "python-dotenv"),
    ]
    for module, pkg in packages:
        try:
            __import__(module)
            all_ok &= check(f"Package: {pkg}", True)
        except ImportError:
            all_ok &= check(f"Package: {pkg}", False, f"Run: pip install {pkg}")

    # 3. .env file
    env_path = PROJECT_ROOT / ".env"
    ok = env_path.exists()
    all_ok &= check(".env file exists", ok, "Copy .env.example to .env and fill in values" if not ok else "")

    # 4. LLM API keys — at least one required
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    mistral_key = os.getenv("MISTRAL_API_KEY", "")

    gemini_ok = bool(gemini_key and gemini_key.startswith("AIza"))
    groq_ok = bool(groq_key and groq_key.startswith("gsk_"))
    mistral_ok = bool(mistral_key)

    all_ok &= check(
        "At least one LLM key set",
        gemini_ok or groq_ok or mistral_ok,
        "Set GEMINI_API_KEY, GROQ_API_KEY, or MISTRAL_API_KEY in .env" if not (gemini_ok or groq_ok or mistral_ok) else "",
    )
    if gemini_ok:
        check("GEMINI_API_KEY set", True)
    else:
        print(f"[{WARN}] GEMINI_API_KEY not set — get free key at aistudio.google.com/apikey")
    if groq_ok:
        check("GROQ_API_KEY set", True)
    else:
        print(f"[{WARN}] GROQ_API_KEY not set — get free key at console.groq.com")
    if mistral_ok:
        check("MISTRAL_API_KEY set", True)
    else:
        print(f"[{WARN}] MISTRAL_API_KEY not set — get free key at console.mistral.ai")

    if gemini_ok:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            resp = client.models.generate_content(model="gemini-2.5-flash-lite", contents="Say OK in one word")
            all_ok &= check("Gemini API reachable", True, f"Response: {resp.text.strip()[:20]}")
        except Exception as e:
            all_ok &= check("Gemini API reachable", False, str(e))

    if groq_ok:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "Say OK in one word"}],
            )
            all_ok &= check("Groq API reachable", True, f"Response: {resp.choices[0].message.content.strip()[:20]}")
        except Exception as e:
            all_ok &= check("Groq API reachable", False, str(e))

    if mistral_ok:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=mistral_key, base_url="https://api.mistral.ai/v1")
            resp = client.chat.completions.create(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": "Say OK in one word"}],
            )
            all_ok &= check("Mistral API reachable", True, f"Response: {resp.choices[0].message.content.strip()[:20]}")
        except Exception as e:
            all_ok &= check("Mistral API reachable", False, str(e))

    # 5. Base resume
    base_resume_dir = PROJECT_ROOT / "base_resume"
    resume_files = list(base_resume_dir.glob("*.docx")) + list(base_resume_dir.glob("*.pdf")) + list(base_resume_dir.glob("*.txt"))
    ok = bool(resume_files)
    all_ok &= check(
        "Base resume file found",
        ok,
        f"Found: {resume_files[0].name}" if ok else "Place your resume (.docx/.pdf/.txt) in base_resume/",
    )

    # 6. Google credentials
    creds_path = PROJECT_ROOT / "credentials.json"
    ok = creds_path.exists()
    all_ok &= check(
        "Google credentials.json found",
        ok,
        "See SETUP.md → Step 2 to download from Google Cloud Console" if not ok else "",
    )

    if ok:
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path),
                scopes=["https://www.googleapis.com/auth/drive.file"],
            )
            check("credentials.json is valid", True)
        except Exception as e:
            all_ok &= check("credentials.json is valid", False, str(e))

    # 7. Google Drive folder ID
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    ok = bool(folder_id)
    all_ok &= check(
        "GOOGLE_DRIVE_FOLDER_ID set",
        ok,
        "Add to .env file (see SETUP.md → Step 5)" if not ok else folder_id,
    )

    # 8. Drive auth token
    token_path = PROJECT_ROOT / "token.json"
    if token_path.exists():
        check("Google Drive token.json found", True, "Auth already complete")
    else:
        print(f"[{WARN}] Google Drive token.json not found — will be created on first run (browser popup)")

    # 9. Config file
    config_path = PROJECT_ROOT / "config.yaml"
    ok = config_path.exists()
    all_ok &= check("config.yaml found", ok)

    # 10. Output directories
    for d in ["output/excel", "output/resumes"]:
        p = PROJECT_ROOT / d
        p.mkdir(parents=True, exist_ok=True)
        check(f"Directory: {d}", True)

    # Summary
    print("\n" + "=" * 50)
    if all_ok:
        print("\033[92mAll checks passed! You're ready to run:\033[0m")
        print("  python src/main.py --dry-run   # test search only")
        print("  python src/main.py             # full run\n")
    else:
        print("\033[91mSome checks failed. Fix the issues above before running.\033[0m\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
