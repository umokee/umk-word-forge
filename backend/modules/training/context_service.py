"""Context generation service for training exercises."""

import logging
from sqlalchemy.orm import Session as DBSession

from backend.modules.words.models import Word, WordContext
from backend.modules.ai.service import ai_service
from backend.modules.settings.repository import get_settings

logger = logging.getLogger(__name__)


async def ensure_ai_contexts(db: DBSession, word_id: int) -> list[WordContext]:
    """Ensure a word has AI-generated contexts. Generate if missing.

    Returns existing AI contexts or generates new ones.
    """
    # Check for existing AI contexts
    existing = (
        db.query(WordContext)
        .filter(WordContext.word_id == word_id)
        .filter(WordContext.source == "ai")
        .all()
    )

    if existing:
        return existing

    # Get word data
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        return []

    # Check if AI is configured
    settings = get_settings(db)
    if not settings.gemini_api_key:
        logger.debug(f"No AI key configured, skipping context generation for word {word_id}")
        return []

    # Generate contexts via AI
    try:
        difficulty = settings.ai_difficulty_context or "simple"
        result = await ai_service.generate_contexts(
            word=word.english,
            part_of_speech=word.part_of_speech or "noun",
            translations=word.translations or [],
            count=3,
            difficulty=difficulty,
        )

        # Save to database
        new_contexts = []
        for ctx_data in result.contexts:
            # Map difficulty string to int
            diff_map = {"A1": 1, "A2": 1, "B1": 2, "B2": 3, 1: 1, 2: 2, 3: 3}
            diff_val = ctx_data.get("difficulty", 1)
            if isinstance(diff_val, str):
                diff_int = diff_map.get(diff_val, 1)
            else:
                diff_int = int(diff_val)

            context = WordContext(
                word_id=word_id,
                sentence_en=ctx_data["en"],
                sentence_ru=ctx_data.get("ru", ""),
                source="ai",
                difficulty=diff_int,
            )
            db.add(context)
            new_contexts.append(context)

        db.commit()
        logger.info(f"Generated {len(new_contexts)} AI contexts for word '{word.english}'")
        return new_contexts

    except Exception as e:
        logger.warning(f"Failed to generate AI contexts for word {word_id}: {e}")
        return []


def get_best_context(db: DBSession, word_id: int) -> WordContext | None:
    """Get the best available context for a word.

    Prefers AI-generated contexts over seed contexts.
    """
    # First try AI contexts
    ai_context = (
        db.query(WordContext)
        .filter(WordContext.word_id == word_id)
        .filter(WordContext.source == "ai")
        .first()
    )
    if ai_context:
        return ai_context

    # Fall back to any context
    return (
        db.query(WordContext)
        .filter(WordContext.word_id == word_id)
        .first()
    )
