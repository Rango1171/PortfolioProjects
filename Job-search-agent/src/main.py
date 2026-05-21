"""
Main orchestrator for the European Job Search Agent.
Runs the full pipeline: search → deduplicate → enrich → customize resume → upload → write Excel.

Usage:
  python main.py            # Full run
  python main.py --dry-run  # Search and print jobs only; skip Drive upload and Excel write
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Allow running from the src/ directory or the project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from job_searcher import search_all, fetch_job_description
from visa_detector import detect_sponsorship
from resume_customizer import ResumeCustomizer
from job_scorer import JobScorer
from drive_uploader import DriveUploader
from excel_writer import ExcelWriter
from llm_router import LLMRouter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path | None = None) -> dict:
    if config_path is None:
        config_path = PROJECT_ROOT / "config.yaml"
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    # Override Drive folder_id from env if set
    env_folder = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    if env_folder:
        cfg["google_drive"]["folder_id"] = env_folder
    return cfg


def load_seen_jobs(seen_file: Path) -> set[str]:
    if seen_file.exists():
        data = json.loads(seen_file.read_text())
        return set(data)
    return set()


def save_seen_jobs(seen_file: Path, seen: set[str]) -> None:
    seen_file.parent.mkdir(parents=True, exist_ok=True)
    seen_file.write_text(json.dumps(sorted(seen), indent=2))


def _safe(text: str, max_len: int) -> str:
    """Truncate and strip non-ASCII for Windows console compatibility."""
    return text[:max_len].encode("ascii", errors="replace").decode("ascii")


def print_jobs_table(jobs: list[dict]) -> None:
    print(f"\n{'#':<4} {'Company':<30} {'Title':<35} {'Country':<10} {'Visa':<10} {'Score':<7} Source")
    print("-" * 108)
    for i, job in enumerate(jobs, 1):
        score = job.get("resume_match_score")
        score_str = f"{score}%" if score is not None else "N/A"
        print(
            f"{i:<4} {_safe(job['company'], 28):<30} {_safe(job['title'], 33):<35} "
            f"{_safe(job['country'], 8):<10} {job.get('visa_sponsorship','?'):<10} "
            f"{score_str:<7} {job['source']}"
        )
    print()


def run(dry_run: bool = False, config_path: Path | None = None) -> None:
    logger.info("=" * 60)
    logger.info(f"European Job Search Agent — {date.today().isoformat()}")
    if dry_run:
        logger.info("DRY RUN MODE — no Drive uploads or Excel writes")
    logger.info("=" * 60)

    config = load_config(config_path)

    # Build LLM routers — separate instances so scorer/customizer exhaust independently
    try:
        scorer_router = LLMRouter.from_env(scorer_mode=True)
        customizer_router = LLMRouter.from_env(scorer_mode=False)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    scorer = JobScorer(
        router=scorer_router,
        base_resume_dir=str(PROJECT_ROOT / "base_resume"),
    )

    drive_folder_id = config["google_drive"]["folder_id"]
    if not drive_folder_id and not dry_run:
        logger.error(
            "GOOGLE_DRIVE_FOLDER_ID is not set. Add it to your .env file or config.yaml. "
            "Run with --dry-run to test without Drive."
        )
        sys.exit(1)

    seen_file = PROJECT_ROOT / config["output"]["seen_jobs_file"]
    seen_jobs = load_seen_jobs(seen_file)
    logger.info(f"Already seen: {len(seen_jobs)} jobs (will skip duplicates)")

    # ── 1. Search ──────────────────────────────────────────────────────────────
    all_jobs = search_all(config)

    # ── 2. Deduplicate against historical seen_jobs.json ──────────────────────
    new_jobs = [j for j in all_jobs if j["job_url"] not in seen_jobs]
    logger.info(f"New jobs after dedup: {len(new_jobs)} (skipped {len(all_jobs) - len(new_jobs)})")

    if not new_jobs:
        logger.info("No new jobs found today. Done.")
        return

    # ── 3. Enrich: fetch full JD + detect visa sponsorship ────────────────────
    logger.info("Enriching jobs (fetching full descriptions + visa detection)...")
    for job in new_jobs:
        job["description"] = fetch_job_description(job["job_url"], job.get("description", ""))
        job["visa_sponsorship"] = detect_sponsorship(job["description"])
        time.sleep(0.5)

    # ── 4. Score each job against the base resume ─────────────────────────────
    min_score = config["search"].get("min_match_score", 80)
    logger.info(f"Scoring {len(new_jobs)} jobs against base resume (threshold: {min_score}%)...")
    for job in new_jobs:
        job["resume_match_score"] = scorer.score(job)
        logger.info(
            f"  {_safe(job['company'], 28)} / {_safe(job['title'], 33)}: "
            f"{job['resume_match_score']}%"
        )

    if dry_run:
        print_jobs_table(new_jobs)
        logger.info("Dry run complete. No files written.")
        return

    # ── 5. Filter jobs that qualify for resume generation ────────────────────
    # Filter 1: match score threshold
    score_qualified = [j for j in new_jobs if j["resume_match_score"] >= min_score]
    logger.info(
        f"Score filter (>={min_score}%): {len(score_qualified)} qualify, "
        f"{len(new_jobs) - len(score_qualified)} below threshold — skipped for resume. "
        f"All {len(new_jobs)} jobs written to Excel."
    )

    # Filter 2: visa sponsorship (applied only on score-qualified jobs)
    resume_statuses: list[str] = config["search"].get("resume_for_sponsorship", ["Yes", "Unknown"])
    sponsorship_jobs = [j for j in score_qualified if j.get("visa_sponsorship") in resume_statuses]
    skipped_visa = len(score_qualified) - len(sponsorship_jobs)
    logger.info(
        f"Visa filter ({resume_statuses}): {len(sponsorship_jobs)} jobs qualify, "
        f"{skipped_visa} skipped (sponsorship status not in filter)."
    )
    if not sponsorship_jobs:
        logger.info("No qualifying jobs for resume generation. All jobs written to Excel without resumes.")

    # ── 6. Initialize services ────────────────────────────────────────────────
    drive_cfg = config["google_drive"]
    credentials_file = str(PROJECT_ROOT / drive_cfg["credentials_file"])
    token_file = str(PROJECT_ROOT / drive_cfg["token_file"])
    resumes_dir = str(PROJECT_ROOT / config["output"]["resumes_dir"])
    excel_dir = str(PROJECT_ROOT / config["output"]["excel_dir"])

    customizer = ResumeCustomizer(
        router=customizer_router,
        base_resume_dir=str(PROJECT_ROOT / "base_resume"),
        output_dir=resumes_dir,
    )
    uploader = DriveUploader(
        credentials_file=credentials_file,
        token_file=token_file,
        folder_id=drive_folder_id,
    )
    writer = ExcelWriter(excel_dir=excel_dir)

    # ── 7. Generate resumes + upload for qualifying jobs ─────────────────────
    processed = 0
    failed = 0
    drive_links: dict[str, str] = {}

    for job in sponsorship_jobs:
        logger.info(f"Generating resume: {job['company']} — {job['title']}")
        try:
            resume_path = customizer.customize(job)
            drive_links[job["job_url"]] = uploader.upload(resume_path)
            processed += 1
        except Exception as e:
            logger.error(f"Failed to generate resume for {job['company']} / {job['title']}: {e}")
            failed += 1
        time.sleep(1)

    # ── 8. Write ALL jobs to Excel (score + resume link where generated) ──────
    for job in new_jobs:
        writer.add_job(
            {
                "date_found": date.today().isoformat(),
                "company": job["company"],
                "title": job["title"],
                "country": job["country"],
                "job_url": job["job_url"],
                "linkedin_url": job.get("linkedin_url", ""),
                "visa_sponsorship": job["visa_sponsorship"],
                "resume_match_score": job.get("resume_match_score", 0),
                "drive_link": drive_links.get(job["job_url"], ""),
            }
        )
        seen_jobs.add(job["job_url"])

    # ── 9. Save outputs ───────────────────────────────────────────────────────
    excel_path = writer.save()
    save_seen_jobs(seen_file, seen_jobs)

    logger.info("=" * 60)
    logger.info(f"Done. Processed: {processed} jobs, Failed: {failed}")
    logger.info(f"Excel: {excel_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="European Job Search Agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and print jobs only; skip Drive upload and Excel write",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to a custom config YAML (default: config.yaml in project root)",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run, config_path=args.config)
