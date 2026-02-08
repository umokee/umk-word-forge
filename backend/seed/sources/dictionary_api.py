"""Free Dictionary API client for word definitions and phonetics."""

import asyncio
import aiohttp
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Definition:
    """A word definition with part of speech."""

    definition: str
    part_of_speech: str
    example: Optional[str] = None
    synonyms: list[str] = field(default_factory=list)
    antonyms: list[str] = field(default_factory=list)


@dataclass
class DictionaryEntry:
    """Complete dictionary entry for a word."""

    word: str
    phonetic: Optional[str] = None
    phonetics: list[dict] = field(default_factory=list)
    definitions: list[Definition] = field(default_factory=list)
    audio_url: Optional[str] = None


class FreeDictionaryAPI:
    """Client for the Free Dictionary API (dictionaryapi.dev)."""

    BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"

    async def get_word(self, word: str) -> Optional[DictionaryEntry]:
        """Get dictionary entry for a word.

        Returns None if word not found.
        """
        url = f"{self.BASE_URL}/{word}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    if not data or not isinstance(data, list):
                        return None

                    entry = data[0]
                    return self._parse_entry(entry)

        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

    def _parse_entry(self, data: dict) -> DictionaryEntry:
        """Parse API response into DictionaryEntry."""
        word = data.get("word", "")
        phonetic = data.get("phonetic", "")

        # Get phonetics with audio
        phonetics = data.get("phonetics", [])
        audio_url = None
        for ph in phonetics:
            if ph.get("audio"):
                audio_url = ph["audio"]
                if not phonetic and ph.get("text"):
                    phonetic = ph["text"]
                break

        # Parse definitions
        definitions = []
        for meaning in data.get("meanings", []):
            pos = meaning.get("partOfSpeech", "")
            for defn in meaning.get("definitions", []):
                definitions.append(
                    Definition(
                        definition=defn.get("definition", ""),
                        part_of_speech=pos,
                        example=defn.get("example"),
                        synonyms=defn.get("synonyms", []),
                        antonyms=defn.get("antonyms", []),
                    )
                )

        return DictionaryEntry(
            word=word,
            phonetic=phonetic,
            phonetics=phonetics,
            definitions=definitions,
            audio_url=audio_url,
        )

    async def get_phonetic(self, word: str) -> Optional[str]:
        """Get just the phonetic transcription for a word."""
        entry = await self.get_word(word)
        return entry.phonetic if entry else None

    async def get_definitions(self, word: str) -> list[Definition]:
        """Get just the definitions for a word."""
        entry = await self.get_word(word)
        return entry.definitions if entry else []


# Synchronous wrapper
def get_dictionary_entry(word: str) -> Optional[DictionaryEntry]:
    """Synchronous wrapper for getting dictionary entry."""
    api = FreeDictionaryAPI()
    return asyncio.run(api.get_word(word))
