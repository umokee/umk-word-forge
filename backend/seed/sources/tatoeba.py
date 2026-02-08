"""Tatoeba API client for fetching example sentences with translations."""

from typing import Optional

try:
    import asyncio
    import aiohttp
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False


class TatoebaAPI:
    """Client for Tatoeba sentence search API with caching."""

    BASE_URL = "https://tatoeba.org/api_v0/search"

    def __init__(self, rate_limit_delay: float = 1.0):
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

    async def _rate_limit(self):
        """Ensure we don't exceed rate limits."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def search_sentences(
        self,
        query: str,
        from_lang: str = "eng",
        to_lang: str = "rus",
        limit: int = 5,
    ) -> list[dict]:
        """Search for sentences containing the query word/phrase.

        Returns list of dicts with 'en', 'ru', 'source' keys.
        """
        await self._rate_limit()

        params = {
            "from": from_lang,
            "to": to_lang,
            "query": query,
            "sort": "relevance",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    results = []

                    for item in data.get("results", [])[:limit]:
                        text_en = item.get("text", "")
                        translations = item.get("translations", [])

                        # Find Russian translation
                        text_ru = ""
                        for trans_group in translations:
                            for trans in trans_group:
                                if trans.get("lang") == "rus":
                                    text_ru = trans.get("text", "")
                                    break
                            if text_ru:
                                break

                        if text_en and text_ru:
                            results.append({
                                "en": text_en,
                                "ru": text_ru,
                                "source": "tatoeba",
                                "difficulty": self._estimate_difficulty(text_en),
                            })

                    return results

        except (aiohttp.ClientError, asyncio.TimeoutError):
            return []

    def _estimate_difficulty(self, sentence: str) -> int:
        """Estimate sentence difficulty based on length and complexity."""
        words = sentence.split()
        word_count = len(words)
        avg_word_len = sum(len(w) for w in words) / max(word_count, 1)

        if word_count <= 6 and avg_word_len < 5:
            return 1
        elif word_count <= 12 and avg_word_len < 6:
            return 2
        else:
            return 3

    async def get_sentences_for_word(self, word: str, limit: int = 5) -> list[dict]:
        """Get example sentences for a single word."""
        return await self.search_sentences(word, limit=limit)

    async def get_sentences_for_phrase(self, phrase: str, limit: int = 5) -> list[dict]:
        """Get example sentences for a phrasal verb or multi-word phrase."""
        # Search for exact phrase first
        results = await self.search_sentences(f'"{phrase}"', limit=limit)

        # If not enough results, try without quotes
        if len(results) < limit:
            more = await self.search_sentences(phrase, limit=limit - len(results))
            # Avoid duplicates
            existing = {r["en"] for r in results}
            for r in more:
                if r["en"] not in existing:
                    results.append(r)

        return results[:limit]


# Synchronous wrapper for use in seed script
def get_tatoeba_sentences(query: str, limit: int = 5) -> list[dict]:
    """Synchronous wrapper for getting Tatoeba sentences."""
    if not ASYNC_AVAILABLE:
        return []
    api = TatoebaAPI()
    return asyncio.run(api.search_sentences(query, limit=limit))
