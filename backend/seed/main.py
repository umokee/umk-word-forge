import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.database import Base, engine, SessionLocal
from backend.modules.words.models import (
    Word,
    WordContext,
    PhrasalVerb,
    PhrasalVerbContext,
    IrregularVerb,
    IrregularVerbContext,
)
from backend.seed.sources.frequency import get_top_words
from backend.seed.sources.ipa import load_ipa_dict
from backend.seed.sources.translations import get_translations
from backend.seed.sources.pos_tagger import get_pos_tags
from backend.seed.sources.sentences import get_sentences_for_word
from backend.seed.sources.cefr import assign_cefr_levels
from backend.seed.sources.phrasal_verbs import get_phrasal_verbs
from backend.seed.sources.irregular_verbs import get_irregular_verbs


def seed_phrasal_verbs(db, force: bool = False):
    """Seed phrasal verbs into database."""
    print("\nSeeding phrasal verbs...")

    if force:
        db.query(PhrasalVerbContext).delete()
        db.query(PhrasalVerb).delete()
        db.commit()

    existing = db.query(PhrasalVerb).count()
    if existing > 0 and not force:
        print(f"  Already have {existing} phrasal verbs, skipping...")
        return

    phrasal_verbs = get_phrasal_verbs()
    count = 0

    for rank, pv_data in enumerate(phrasal_verbs, 1):
        existing_pv = db.query(PhrasalVerb).filter(
            PhrasalVerb.phrase == pv_data["phrase"]
        ).first()
        if existing_pv:
            continue

        pv = PhrasalVerb(
            phrase=pv_data["phrase"],
            base_verb=pv_data["base_verb"],
            particle=pv_data["particle"],
            translations=pv_data["translations"],
            definitions=pv_data["definitions"],
            frequency_rank=rank,
            cefr_level="B1",  # Default level
            is_separable=pv_data.get("is_separable", True),
        )
        db.add(pv)
        count += 1

        if count % 50 == 0:
            print(f"  {count} phrasal verbs added...")
            db.commit()

    db.commit()
    total = db.query(PhrasalVerb).count()
    print(f"  Done! {total} phrasal verbs in database.")


def seed_irregular_verbs(db, force: bool = False):
    """Seed irregular verbs into database."""
    print("\nSeeding irregular verbs...")

    if force:
        db.query(IrregularVerbContext).delete()
        db.query(IrregularVerb).delete()
        db.commit()

    existing = db.query(IrregularVerb).count()
    if existing > 0 and not force:
        print(f"  Already have {existing} irregular verbs, skipping...")
        return

    irregular_verbs = get_irregular_verbs()
    count = 0

    for rank, iv_data in enumerate(irregular_verbs, 1):
        existing_iv = db.query(IrregularVerb).filter(
            IrregularVerb.base_form == iv_data["base"]
        ).first()
        if existing_iv:
            continue

        iv = IrregularVerb(
            base_form=iv_data["base"],
            past_simple=iv_data["past"],
            past_participle=iv_data["participle"],
            translations=iv_data["translations"],
            verb_pattern=iv_data.get("pattern", "ABC"),
            frequency_rank=rank,
            cefr_level="A2",  # Most common irregular verbs are A2
        )
        db.add(iv)
        count += 1

        if count % 50 == 0:
            print(f"  {count} irregular verbs added...")
            db.commit()

    db.commit()
    total = db.query(IrregularVerb).count()
    print(f"  Done! {total} irregular verbs in database.")


def seed_database(word_count: int = 10000, skip_ai: bool = True, force: bool = False):
    print(f"Starting seed with {word_count} words...")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if force:
            print("Clearing existing data...")
            db.query(IrregularVerbContext).delete()
            db.query(IrregularVerb).delete()
            db.query(PhrasalVerbContext).delete()
            db.query(PhrasalVerb).delete()
            db.query(WordContext).delete()
            db.query(Word).delete()
            db.commit()

        existing = db.query(Word).count()
        if existing > 0 and not force:
            print(f"Database has {existing} words. Adding new words up to {word_count}...")
            if existing >= word_count:
                print(f"Already have {existing} words, nothing to add.")
                return

        print("Step 1: Getting frequency list...")
        words = get_top_words(word_count)
        print(f"  Got {len(words)} words")

        print("Step 2: Loading IPA dictionary...")
        try:
            ipa_dict = load_ipa_dict()
            print(f"  Got {len(ipa_dict)} IPA entries")
        except Exception as e:
            print(f"  IPA loading failed: {e}, continuing without transcriptions")
            ipa_dict = {}

        print("Step 3: Getting translations...")
        translations = get_translations(words)
        print(f"  Got translations for {len(translations)} words")

        print("Step 4: POS tagging...")
        pos_tags = get_pos_tags(words)
        print(f"  Tagged {len(pos_tags)} words")

        print("Step 5: Assigning CEFR levels...")
        cefr_levels = assign_cefr_levels(words)

        print("Step 6: Writing to database...")
        count = 0
        for rank, word_text in enumerate(words, 1):
            existing_word = db.query(Word).filter(Word.english == word_text).first()
            if existing_word:
                continue

            word = Word(
                english=word_text,
                transcription=ipa_dict.get(word_text, ""),
                part_of_speech=pos_tags.get(word_text, "noun"),
                translations=translations.get(word_text, [word_text]),
                frequency_rank=rank,
                cefr_level=cefr_levels.get(word_text, "B1"),
            )
            db.add(word)
            db.flush()

            word_pos = pos_tags.get(word_text, "noun")
            sentences = get_sentences_for_word(word_text, word_pos)
            for sent in sentences:
                ctx = WordContext(
                    word_id=word.id,
                    sentence_en=sent["en"],
                    sentence_ru=sent.get("ru", ""),
                    source="seed",
                    difficulty=sent.get("difficulty", 1),
                )
                db.add(ctx)

            count += 1
            if count % 100 == 0:
                print(f"  {count}/{word_count} words added...")
                db.commit()

        db.commit()
        total = db.query(Word).count()
        contexts = db.query(WordContext).count()
        print(f"\nDone! {total} words and {contexts} contexts in database.")

        # Seed phrasal verbs and irregular verbs
        seed_phrasal_verbs(db, force=force)
        seed_irregular_verbs(db, force=force)

        # Print final summary
        print("\n" + "=" * 50)
        print("Database seeding complete!")
        print(f"  Words: {db.query(Word).count()}")
        print(f"  Word Contexts: {db.query(WordContext).count()}")
        print(f"  Phrasal Verbs: {db.query(PhrasalVerb).count()}")
        print(f"  Irregular Verbs: {db.query(IrregularVerb).count()}")
        print("=" * 50)

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed WordForge database")
    parser.add_argument("--count", type=int, default=10000, help="Number of words (default: 10000)")
    parser.add_argument("--skip-ai", action="store_true", help="Skip AI translations")
    parser.add_argument("--force", action="store_true", help="Overwrite existing data")
    args = parser.parse_args()

    seed_database(
        word_count=args.count,
        skip_ai=args.skip_ai,
        force=args.force,
    )


if __name__ == "__main__":
    main()
