"""
Multi-provider LLM router with automatic fallback.
Priority order (per router instance): Gemini → Groq → Mistral.

When a provider returns a rate-limit or quota error it is immediately marked
exhausted and the next provider is tried. Exhausted providers are re-enabled
after EXHAUSTED_COOLDOWN seconds (default 1 hour).

Usage:
    router = LLMRouter.from_env(scorer_mode=True)
    text = router.generate(prompt, system_prompt)
"""

import logging
import os
import time

logger = logging.getLogger(__name__)

# Seconds a provider stays locked out after hitting a quota/rate-limit error.
_EXHAUSTED_COOLDOWN = 3600  # 1 hour

_RATE_LIMIT_SIGNALS = frozenset([
    "429", "rate_limit", "RESOURCE_EXHAUSTED",
    "quota_exceeded", "RateLimitError", "insufficient_quota",
    "too many requests", "exceeded your current quota",
])


def _is_rate_limit(err: str) -> bool:
    err_lower = err.lower()
    return any(s.lower() in err_lower for s in _RATE_LIMIT_SIGNALS)


class _Provider:
    def __init__(self, name: str, api_key: str, model: str):
        self.name = name
        self.api_key = api_key
        self.model = model
        self._exhausted_until: float = 0.0

    def is_available(self) -> bool:
        return bool(self.api_key) and time.monotonic() > self._exhausted_until

    def mark_exhausted(self) -> None:
        self._exhausted_until = time.monotonic() + _EXHAUSTED_COOLDOWN
        logger.warning(
            f"{self.name} ({self.model}): quota/rate-limit hit — "
            f"switching to next provider. Will retry in {_EXHAUSTED_COOLDOWN // 60} min."
        )

    def generate(self, prompt: str, system_prompt: str) -> str:
        raise NotImplementedError


class _GeminiProvider(_Provider):
    def __init__(self, api_key: str, model: str):
        super().__init__("Gemini", api_key, model)
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, system_prompt: str) -> str:
        from google.genai import types
        response = self._get_client().models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        return response.text


class _OpenAICompatProvider(_Provider):
    """Handles Groq (Llama / Gemma) and Mistral — both expose OpenAI-compatible endpoints."""

    def __init__(self, name: str, api_key: str, model: str, base_url: str):
        super().__init__(name, api_key, model)
        self._base_url = base_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key, base_url=self._base_url)
        return self._client

    def generate(self, prompt: str, system_prompt: str) -> str:
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content


class LLMRouter:
    """
    Routes generate() calls through providers in priority order.

    On rate-limit / quota errors the current provider is marked exhausted and
    the next one is tried immediately (no waiting). Non-quota errors propagate
    to the caller unchanged.
    """

    def __init__(self, providers: list):
        if not providers:
            raise ValueError("LLMRouter needs at least one configured provider.")
        self._providers = providers
        names = " → ".join(f"{p.name}/{p.model}" for p in providers)
        logger.info(f"LLM provider chain: {names}")

    def generate(self, prompt: str, system_prompt: str) -> str:
        available = [p for p in self._providers if p.is_available()]
        if not available:
            raise RuntimeError(
                "All LLM providers are exhausted or unconfigured. "
                "Add more API keys in .env or wait ~1 hour for quota reset."
            )
        for provider in available:
            try:
                logger.debug(f"Calling {provider.name} ({provider.model})...")
                return provider.generate(prompt, system_prompt)
            except Exception as e:
                if _is_rate_limit(str(e)):
                    provider.mark_exhausted()
                    continue
                raise
        raise RuntimeError(
            "All available LLM providers hit rate limits. "
            "Wait for quota reset or add API keys for additional providers."
        )

    @classmethod
    def from_env(cls, scorer_mode: bool = False) -> "LLMRouter":
        """
        Build a router from environment variables.

        scorer_mode=True  → lighter models (scoring only needs a single integer output)
        scorer_mode=False → stronger models for resume generation

        Free-tier limits (approximate):
          Gemini 2.0 Flash      : 15 RPM, 1 500 req/day
          Gemini 2.5 Flash Lite : 15 RPM,   500 req/day
          Groq llama-3.1-8b    : 30 RPM, 14 400 req/day
          Groq llama-3.3-70b   : 30 RPM,    1 000 req/day (token-limited)
          Mistral small        : 1 RPM (free tier)
        """
        providers: list[_Provider] = []

        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        if gemini_key:
            if scorer_mode:
                model = os.getenv("GEMINI_SCORER_MODEL", "gemini-2.0-flash")
            else:
                model = os.getenv("GEMINI_CUSTOMIZER_MODEL", "gemini-2.5-flash-lite")
            providers.append(_GeminiProvider(gemini_key, model))

        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if groq_key:
            if scorer_mode:
                # Fast 8B model — plenty of free quota for single-integer outputs
                model = os.getenv("GROQ_SCORER_MODEL", "llama-3.1-8b-instant")
            else:
                # 70B for quality resume generation; daily token budget is tighter
                model = os.getenv("GROQ_CUSTOMIZER_MODEL", "llama-3.3-70b-versatile")
            providers.append(_OpenAICompatProvider(
                "Groq", groq_key, model,
                base_url="https://api.groq.com/openai/v1",
            ))

        mistral_key = os.getenv("MISTRAL_API_KEY", "").strip()
        if mistral_key:
            if scorer_mode:
                model = os.getenv("MISTRAL_SCORER_MODEL", "mistral-small-latest")
            else:
                model = os.getenv("MISTRAL_CUSTOMIZER_MODEL", "mistral-small-latest")
            providers.append(_OpenAICompatProvider(
                "Mistral", mistral_key, model,
                base_url="https://api.mistral.ai/v1",
            ))

        if not providers:
            raise RuntimeError(
                "No LLM API keys configured. Set at least one of: "
                "GEMINI_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY in .env.\n"
                "Free keys:\n"
                "  Gemini : https://aistudio.google.com/apikey\n"
                "  Groq   : https://console.groq.com\n"
                "  Mistral: https://console.mistral.ai"
            )

        return cls(providers)
