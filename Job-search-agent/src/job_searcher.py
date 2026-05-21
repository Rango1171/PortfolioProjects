"""
Searches for Data Engineer and Project Manager jobs across Europe.
Sources: LinkedIn (via JobSpy) + Indeed country portals (via JobSpy).
"""

import logging
import time
import random
from datetime import date, timedelta

import requests

logger = logging.getLogger(__name__)

# JobSpy country_indeed values for European country portals
INDEED_COUNTRY_MAP = {
    "AT": "Austria",
    "BE": "Belgium",
    "CZ": "Czech Republic",
    "DK": "Denmark",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "GR": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LU": "Luxembourg",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "ES": "Spain",
    "SE": "Sweden",
    "NO": "Norway",
    "CH": "Switzerland",
    "GB": "UK",
}


def _str(val) -> str:
    """Convert a value to string, treating NaN/None as empty string."""
    if val is None:
        return ""
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return ""
    except Exception:
        pass
    return str(val).strip()


def _normalize_job(raw: dict, source: str) -> dict:
    return {
        "company": _str(raw.get("company", "")),
        "title": _str(raw.get("title", "")),
        "country": _str(raw.get("country", "")),
        "job_url": _str(raw.get("job_url", "")),
        "linkedin_url": _str(raw.get("linkedin_url", "")) if source == "linkedin" else "",
        "description": _str(raw.get("description", "")),
        "date_posted": str(raw.get("date_posted", date.today())),
        "source": source,
    }


def search_linkedin(role: str, max_results: int, days_old: int) -> list[dict]:
    """Scrape LinkedIn via python-jobspy."""
    try:
        from jobspy import scrape_jobs
    except ImportError:
        logger.error("python-jobspy not installed. Run: pip install python-jobspy")
        return []

    logger.info(f"LinkedIn: searching '{role}' in Europe (last {days_old}d)...")
    try:
        df = scrape_jobs(
            site_name=["linkedin"],
            search_term=role,
            location="Europe",
            results_wanted=max_results,
            hours_old=days_old * 24,
            linkedin_fetch_description=True,
        )
    except Exception as e:
        logger.warning(f"LinkedIn search failed for '{role}': {e}")
        return []

    jobs = []
    for _, row in df.iterrows():
        raw = {
            "company": row.get("company", ""),
            "title": row.get("title", ""),
            "country": row.get("location", ""),
            "job_url": row.get("job_url", ""),
            "linkedin_url": row.get("job_url", ""),
            "description": row.get("description", ""),
            "date_posted": row.get("date_posted", date.today()),
        }
        jobs.append(_normalize_job(raw, "linkedin"))

    logger.info(f"LinkedIn: found {len(jobs)} jobs for '{role}'")
    return jobs


def search_indeed(role: str, countries: list[str], max_results: int, days_old: int) -> list[dict]:
    """Search Indeed country portals via JobSpy for European jobs."""
    try:
        from jobspy import scrape_jobs
    except ImportError:
        logger.error("python-jobspy not installed. Run: pip install python-jobspy")
        return []

    # Pick countries that Indeed supports; cycle through top ones to spread results
    target_countries = [INDEED_COUNTRY_MAP[c] for c in countries if c in INDEED_COUNTRY_MAP]
    # Rotate the list each run so we don't always hit the same countries first
    random.shuffle(target_countries)

    all_jobs: list[dict] = []
    seen_urls: set[str] = set()

    for country_name in target_countries:
        if len(all_jobs) >= max_results:
            break
        logger.info(f"Indeed ({country_name}): searching '{role}'...")
        try:
            df = scrape_jobs(
                site_name=["indeed"],
                search_term=role,
                location=country_name,
                results_wanted=min(10, max_results - len(all_jobs)),
                hours_old=days_old * 24,
                country_indeed=country_name,
            )
        except Exception as e:
            logger.warning(f"Indeed search failed for '{role}' in {country_name}: {e}")
            time.sleep(random.uniform(1, 2))
            continue

        for _, row in df.iterrows():
            url = str(row.get("job_url", "")).strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            raw = {
                "company": row.get("company", ""),
                "title": row.get("title", ""),
                "country": country_name,
                "job_url": url,
                "description": row.get("description", ""),
                "date_posted": row.get("date_posted", date.today()),
            }
            all_jobs.append(_normalize_job(raw, "indeed"))

        time.sleep(random.uniform(1.5, 3))

    logger.info(f"Indeed: found {len(all_jobs)} jobs for '{role}'")
    return all_jobs


def search_all(config: dict) -> list[dict]:
    """
    Run all job searches and return a combined, deduplicated list.
    Deduplication by job_url only — seen_jobs.json dedup happens in main.py.
    """
    roles: list[str] = config["search"]["roles"]
    max_per_search: int = config["search"]["max_jobs_per_search"]
    days_old: int = config["search"]["days_old"]
    # Priority countries first, then extras — order matters for Indeed quota
    priority: list[str] = config["search"].get("priority_countries", [])
    extra: list[str] = config["search"].get("extra_countries", [])
    countries: list[str] = priority + [c for c in extra if c not in priority]

    seen_urls: set[str] = set()
    combined: list[dict] = []

    for role in roles:
        # LinkedIn
        li_jobs = search_linkedin(role, max_per_search, days_old)
        for job in li_jobs:
            if job["job_url"] and job["job_url"] not in seen_urls:
                seen_urls.add(job["job_url"])
                job["search_role"] = role
                combined.append(job)

        time.sleep(random.uniform(2, 4))  # be polite between searches

        # Indeed (multi-country)
        eu_jobs = search_indeed(role, countries, max_per_search, days_old)
        for job in eu_jobs:
            if job["job_url"] and job["job_url"] not in seen_urls:
                seen_urls.add(job["job_url"])
                job["search_role"] = role
                combined.append(job)

    logger.info(f"Total unique jobs found this run: {len(combined)}")
    return combined


def fetch_job_description(job_url: str, existing_desc: str = "") -> str:
    """
    Fetch the full job description text from the job URL.
    Falls back to existing_desc if scraping fails.
    """
    if existing_desc and len(existing_desc) > 300:
        return existing_desc

    try:
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(job_url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:8000]  # cap to keep Claude prompt reasonable
    except Exception as e:
        logger.debug(f"Could not fetch JD from {job_url}: {e}")
        return existing_desc
