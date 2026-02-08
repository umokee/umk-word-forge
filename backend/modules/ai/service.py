import json
import logging

import httpx

from backend.core.config import settings
from .schemas import AICheckResult, AIContextResult, AIEnrichResult
from .prompts import check_sentence_prompt, generate_contexts_prompt, enrich_word_prompt
from .exceptions import AllProvidersFailedError, AIRateLimitError

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key={api_key}"
)


class AIService:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self.providers = []
        if self._api_key:
            self.providers.append(
                {"name": "gemini", "call": self._call_gemini}
            )

    def configure(self, api_key: str) -> None:
        """Dynamically configure the API key (e.g., from database settings)."""
        self._api_key = api_key
        self.providers = [{"name": "gemini", "call": self._call_gemini}]

    async def check_sentence(
        self, word: str, translation: str, sentence: str
    ) -> AICheckResult:
        """Check a user-written sentence using available AI providers."""
        prompt = check_sentence_prompt(word, translation, sentence)
        raw = await self._call_with_fallback(prompt)
        data = self._parse_json(raw)
        return AICheckResult(**data)

    async def generate_contexts(
        self,
        word: str,
        part_of_speech: str,
        translations: list[str] | None = None,
        count: int = 3,
        difficulty: str = "simple",
    ) -> AIContextResult:
        """Generate example context sentences using available AI providers."""
        prompt = generate_contexts_prompt(
            word, part_of_speech, translations or [], count, difficulty
        )
        raw = await self._call_with_fallback(prompt)
        data = self._parse_json(raw)

        # Handle both list and dict-with-contexts-key responses
        if isinstance(data, list):
            contexts = data
        elif isinstance(data, dict) and "contexts" in data:
            contexts = data["contexts"]
        else:
            contexts = [data]

        return AIContextResult(contexts=contexts)

    async def enrich_word(
        self,
        word: str,
        part_of_speech: str,
        translations: list[str] | None = None,
    ) -> AIEnrichResult:
        """Generate comprehensive linguistic data for a word."""
        prompt = enrich_word_prompt(word, part_of_speech, translations or [])
        raw = await self._call_with_fallback(prompt)
        data = self._parse_json(raw)

        return AIEnrichResult(
            verb_forms=data.get("verb_forms"),
            collocations=data.get("collocations", []),
            phrasal_verbs=data.get("phrasal_verbs"),
            usage_notes=data.get("usage_notes", []),
            common_mistakes=data.get("common_mistakes", []),
        )

    async def _call_with_fallback(self, prompt: str) -> str:
        """Try each provider in order until one succeeds."""
        if not self.providers:
            raise AllProvidersFailedError(
                "No AI providers configured. Set GEMINI_API_KEY."
            )

        errors = []
        for provider in self.providers:
            try:
                logger.info(f"Trying AI provider: {provider['name']}")
                result = await provider["call"](prompt)
                return result
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit hit on {provider['name']}")
                    errors.append(f"{provider['name']}: rate limited")
                    continue
                logger.error(f"HTTP error from {provider['name']}: {e}")
                errors.append(f"{provider['name']}: {e}")
            except Exception as e:
                logger.error(f"Error from {provider['name']}: {e}")
                errors.append(f"{provider['name']}: {e}")

        # Check if all failures were rate limits
        if all("rate limited" in err for err in errors):
            raise AIRateLimitError()

        raise AllProvidersFailedError(
            f"All AI providers failed: {'; '.join(errors)}"
        )

    async def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API."""
        url = GEMINI_URL.format(api_key=self._api_key)
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()

    @staticmethod
    def _parse_json(raw: str) -> dict | list:
        """Parse JSON from AI response, stripping markdown fences if present."""
        cleaned = raw.strip()

        # Strip markdown code fences
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        return json.loads(cleaned)


# Module-level singleton
ai_service = AIService()
