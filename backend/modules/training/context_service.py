"""Context generation and word enrichment service for training exercises."""

import json
import logging
from sqlalchemy.orm import Session as DBSession

from backend.modules.words.models import Word, WordContext
from backend.modules.ai.service import ai_service
from backend.modules.settings.repository import get_settings
from backend.core.config import settings as env_settings

logger = logging.getLogger(__name__)


def _get_api_key(db: DBSession) -> str | None:
    """Get Gemini API key from database settings OR environment variable."""
    db_settings = get_settings(db)
    # Prefer database setting, fall back to env
    return db_settings.gemini_api_key or env_settings.GEMINI_API_KEY or None


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

    # Check if AI is configured (database OR env)
    api_key = _get_api_key(db)
    if not api_key:
        logger.debug(f"No AI key configured, skipping context generation for word {word_id}")
        return []

    # Configure AI service with the API key
    ai_service.configure(api_key)

    # Generate contexts via AI
    try:
        db_settings = get_settings(db)
        difficulty = db_settings.ai_difficulty_context or "simple"
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


async def enrich_word_data(db: DBSession, word_id: int) -> bool:
    """Generate and save linguistic data for a word (collocations, verb forms, etc.).

    Returns True if enrichment was performed or already done.
    """
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        return False

    # Check if already enriched
    if word.ai_enriched:
        return True

    # Check if AI is configured (database OR env)
    api_key = _get_api_key(db)
    if not api_key:
        return False

    # Configure AI service with the API key
    ai_service.configure(api_key)

    try:
        result = await ai_service.enrich_word(
            word=word.english,
            part_of_speech=word.part_of_speech or "noun",
            translations=word.translations or [],
        )

        # Save to database
        word.verb_forms = json.dumps(result.verb_forms) if result.verb_forms else None
        word.collocations = json.dumps(result.collocations) if result.collocations else None
        word.phrasal_verbs = json.dumps(result.phrasal_verbs) if result.phrasal_verbs else None
        word.usage_notes = json.dumps(result.usage_notes) if result.usage_notes else None
        word.ai_enriched = 1

        db.commit()
        logger.info(f"Enriched word '{word.english}' with linguistic data")
        return True

    except Exception as e:
        logger.warning(f"Failed to enrich word {word_id}: {e}")
        return False


async def ensure_rich_contexts(db: DBSession, word_id: int) -> dict | None:
    """Ensure rich contexts for a word, with special handling for function words.

    For function words (the, a, to, in, etc.), generates usage rules, comparisons,
    and common errors instead of simple contexts.

    Returns a dict with rich context data or None.
    """
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        return None

    # Check if this is a function word
    is_function_word = word.word_category in ("function", "preposition")

    if not is_function_word:
        # Regular word - use standard context generation
        await ensure_ai_contexts(db, word_id)
        return None

    # Function word - check if we already have rich contexts
    existing_rich = (
        db.query(WordContext)
        .filter(WordContext.word_id == word_id)
        .filter(WordContext.context_type == "usage_rule")
        .first()
    )

    if existing_rich:
        # Already have rich contexts, return them
        return _get_function_word_data(db, word_id)

    # Generate rich contexts for function word
    api_key = _get_api_key(db)
    if not api_key:
        return None

    ai_service.configure(api_key)

    try:
        from backend.modules.ai.prompts import generate_function_word_prompt
        prompt = generate_function_word_prompt(word.english, word.part_of_speech or "")

        # Call AI to get function word data
        response = await ai_service._call_with_fallback(prompt)
        if not response:
            return None

        import json
        data = json.loads(response)

        # Save usage rules as contexts
        for rule_data in data.get("usage_rules", []):
            context = WordContext(
                word_id=word_id,
                sentence_en=rule_data.get("example", ""),
                sentence_ru="",
                source="ai",
                context_type="usage_rule",
                usage_explanation=rule_data.get("rule", ""),
            )
            db.add(context)

        # Save common errors
        for error_data in data.get("common_errors", []):
            context = WordContext(
                word_id=word_id,
                sentence_en=error_data.get("correct", ""),
                sentence_ru="",
                source="ai",
                context_type="comparison",
                common_errors=json.dumps([error_data]),
            )
            db.add(context)

        # Save example contexts
        for ex_data in data.get("context_examples", []):
            context = WordContext(
                word_id=word_id,
                sentence_en=ex_data.get("en", ""),
                sentence_ru=ex_data.get("ru", ""),
                source="ai",
                context_type="example",
                usage_explanation=ex_data.get("note", ""),
            )
            db.add(context)

        # Store comparisons in word grammar_notes
        if data.get("comparisons"):
            word.grammar_notes = json.dumps({"comparisons": data["comparisons"]})

        db.commit()
        logger.info(f"Generated rich contexts for function word '{word.english}'")

        return data

    except Exception as e:
        logger.warning(f"Failed to generate rich contexts for function word {word_id}: {e}")
        return None


def _get_function_word_data(db: DBSession, word_id: int) -> dict:
    """Retrieve stored function word data from database."""
    import json

    word = db.query(Word).filter(Word.id == word_id).first()

    # Get usage rules
    usage_rules = []
    rule_contexts = (
        db.query(WordContext)
        .filter(WordContext.word_id == word_id)
        .filter(WordContext.context_type == "usage_rule")
        .all()
    )
    for ctx in rule_contexts:
        usage_rules.append({
            "rule": ctx.usage_explanation or "",
            "example": ctx.sentence_en or "",
        })

    # Get common errors
    common_errors = []
    error_contexts = (
        db.query(WordContext)
        .filter(WordContext.word_id == word_id)
        .filter(WordContext.context_type == "comparison")
        .all()
    )
    for ctx in error_contexts:
        if ctx.common_errors:
            try:
                errors = json.loads(ctx.common_errors) if isinstance(ctx.common_errors, str) else ctx.common_errors
                common_errors.extend(errors)
            except:
                pass

    # Get comparisons from grammar_notes
    comparisons = []
    if word and word.grammar_notes:
        try:
            notes = json.loads(word.grammar_notes) if isinstance(word.grammar_notes, str) else word.grammar_notes
            comparisons = notes.get("comparisons", [])
        except:
            pass

    return {
        "usage_rules": usage_rules,
        "comparisons": comparisons,
        "common_errors": common_errors,
    }


def get_best_context(db: DBSession, word_id: int) -> WordContext | None:
    """Get the best available context for a word.

    Prefers AI-generated contexts over seed contexts.
    Skips low-quality template contexts like 'This is a X'.
    """
    # First try AI contexts (highest quality)
    ai_context = (
        db.query(WordContext)
        .filter(WordContext.word_id == word_id)
        .filter(WordContext.source == "ai")
        .first()
    )
    if ai_context:
        return ai_context

    # Fall back to seed contexts, but skip template garbage
    seed_context = (
        db.query(WordContext)
        .filter(WordContext.word_id == word_id)
        .first()
    )

    # Don't return low-quality template sentences
    if seed_context and seed_context.sentence_en:
        bad_patterns = ["This is a ", "This is an ", "I see the ", "It is very "]
        if any(seed_context.sentence_en.startswith(p) for p in bad_patterns):
            return None  # Better no context than a bad one

    return seed_context
