import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.database import Base, engine, SessionLocal
from backend.modules.words.models import Word, WordContext
from backend.seed.sources.frequency import get_top_words
from backend.seed.sources.ipa import load_ipa_dict
from backend.seed.sources.translations import get_translations
from backend.seed.sources.pos_tagger import get_pos_tags
from backend.seed.sources.sentences import get_sentences_for_word
from backend.seed.sources.cefr import assign_cefr_levels


def seed_database(word_count: int = 5000, skip_ai: bool = True, force: bool = False):
    print(f"Starting seed with {word_count} words...")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if force:
            print("Clearing existing data...")
            db.query(WordContext).delete()
            db.query(Word).delete()
            db.commit()

        existing = db.query(Word).count()
        if existing > 0 and not force:
            print(f"Database already has {existing} words. Use --force to overwrite.")
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

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed WordForge database")
    parser.add_argument("--count", type=int, default=5000, help="Number of words (default: 5000)")
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
