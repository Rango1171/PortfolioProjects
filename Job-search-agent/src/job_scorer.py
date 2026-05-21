"""
Scores each job description against the candidate's base resume.
Returns an integer 0-100 representing how well the job matches the candidate's profile.
"""

import logging
import time

from resume_customizer import _load_base_resume
from llm_router import LLMRouter

logger = logging.getLogger(__name__)

SCORER_SYSTEM_PROMPT = (
    "You are a technical recruiter evaluating how well a candidate's resume matches a job description. "
    "Score the match from 0 to 100 where:\n"
    "- 90-100: Near-perfect fit — candidate has all required skills and experience level\n"
    "- 70-89: Strong match — candidate meets most key requirements\n"
    "- 50-69: Moderate match — candidate meets some requirements but has notable gaps\n"
    "- 0-49: Poor match — significant skill or experience gaps\n\n"
    "Consider: required technical skills, years of experience, domain knowledge, seniority level.\n"
    "Output ONLY a single integer from 0 to 100. No text, no explanation, no punctuation."
)


class JobScorer:
    """
    Stateful scorer. Reuse one instance per run — the base resume is loaded once
    and reused across all scoring calls.
    """

    def __init__(self, router: LLMRouter, base_resume_dir: str):
        self.router = router
        self.base_resume_text = _load_base_resume(base_resume_dir)

    def _call_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call the LLM router; retry on transient (non-quota) failures."""
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                return self.router.generate(prompt, SCORER_SYSTEM_PROMPT)
            except RuntimeError:
                raise  # all providers exhausted — surface immediately
            except Exception as e:
                last_err = e
                if attempt < max_retries - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"Scorer LLM error: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
        raise RuntimeError(f"Scorer failed after {max_retries} attempts") from last_err

    def score(self, job: dict) -> int:
        """
        Score how well the job matches the base resume.
        Returns an integer 0-100. Returns 0 on any error.
        """
        jd_text = job.get("description", "")[:3000] or "(No description available)"
        prompt = (
            f"RESUME:\n{self.base_resume_text[:3000]}\n\n"
            f"---\n\n"
            f"JOB ({job.get('company', '')} — {job.get('title', '')}):\n{jd_text}\n\n"
            "Score:"
        )

        # Conservative pacing: 13 s keeps us safely under Gemini's 5 RPM free tier.
        # Other providers (Groq 30 RPM, Mistral 1 RPM) are handled by their own limits.
        time.sleep(13)
        raw = ""
        try:
            raw = self._call_with_retry(prompt).strip()
            score = int("".join(c for c in raw if c.isdigit())[:3])
            return max(0, min(100, score))
        except (ValueError, TypeError):
            logger.warning(
                f"Could not parse score for {job.get('company')} / {job.get('title')}: "
                f"got {raw!r:.40} — defaulting to 0"
            )
            return 0
