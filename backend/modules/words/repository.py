from sqlalchemy import func, or_, cast, String
from sqlalchemy.orm import Session, joinedload

from backend.modules.words.models import (
    Word,
    WordContext,
    PhrasalVerb,
    PhrasalVerbContext,
    IrregularVerb,
    IrregularVerbContext,
)


class WordRepository:

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        cefr_level: str | None = None,
        part_of_speech: str | None = None,
    ) -> tuple[list[Word], int]:
        query = db.query(Word)

        if search:
            pattern = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Word.english).like(pattern),
                    cast(Word.translations, String).like(pattern),
                )
            )

        if cefr_level:
            query = query.filter(Word.cefr_level == cefr_level)

        if part_of_speech:
            query = query.filter(Word.part_of_speech == part_of_speech)

        total = query.count()

        words = (
            query.order_by(Word.frequency_rank.asc().nullslast(), Word.english.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return words, total

    @staticmethod
    def get_by_id(db: Session, word_id: int) -> Word | None:
        return (
            db.query(Word)
            .options(joinedload(Word.contexts))
            .filter(Word.id == word_id)
            .first()
        )

    @staticmethod
    def get_by_english(db: Session, english: str) -> Word | None:
        return (
            db.query(Word)
            .filter(func.lower(Word.english) == english.lower())
            .first()
        )

    @staticmethod
    def create(db: Session, word_data: dict) -> Word:
        word = Word(**word_data)
        db.add(word)
        db.commit()
        db.refresh(word)
        return word

    @staticmethod
    def delete(db: Session, word_id: int) -> bool:
        word = db.query(Word).filter(Word.id == word_id).first()
        if not word:
            return False
        db.delete(word)
        db.commit()
        return True

    @staticmethod
    def search(db: Session, query: str) -> list[Word]:
        pattern = f"%{query.lower()}%"
        return (
            db.query(Word)
            .filter(
                or_(
                    func.lower(Word.english).like(pattern),
                    cast(Word.translations, String).like(pattern),
                )
            )
            .order_by(Word.frequency_rank.asc().nullslast(), Word.english.asc())
            .limit(50)
            .all()
        )

    @staticmethod
    def get_random_words(
        db: Session,
        count: int = 3,
        part_of_speech: str | None = None,
        exclude_ids: list[int] | None = None,
    ) -> list[Word]:
        query = db.query(Word)

        if part_of_speech:
            query = query.filter(Word.part_of_speech == part_of_speech)

        if exclude_ids:
            query = query.filter(Word.id.notin_(exclude_ids))

        return query.order_by(func.random()).limit(count).all()


class PhrasalVerbRepository:
    """Repository for PhrasalVerb CRUD operations."""

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        base_verb: str | None = None,
        cefr_level: str | None = None,
    ) -> tuple[list[PhrasalVerb], int]:
        query = db.query(PhrasalVerb)

        if search:
            pattern = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(PhrasalVerb.phrase).like(pattern),
                    cast(PhrasalVerb.translations, String).like(pattern),
                )
            )

        if base_verb:
            query = query.filter(func.lower(PhrasalVerb.base_verb) == base_verb.lower())

        if cefr_level:
            query = query.filter(PhrasalVerb.cefr_level == cefr_level)

        total = query.count()

        items = (
            query.order_by(
                PhrasalVerb.frequency_rank.asc().nullslast(), PhrasalVerb.phrase.asc()
            )
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return items, total

    @staticmethod
    def get_by_id(db: Session, phrasal_verb_id: int) -> PhrasalVerb | None:
        return (
            db.query(PhrasalVerb)
            .options(joinedload(PhrasalVerb.contexts))
            .filter(PhrasalVerb.id == phrasal_verb_id)
            .first()
        )

    @staticmethod
    def get_by_phrase(db: Session, phrase: str) -> PhrasalVerb | None:
        return (
            db.query(PhrasalVerb)
            .filter(func.lower(PhrasalVerb.phrase) == phrase.lower())
            .first()
        )

    @staticmethod
    def create(db: Session, data: dict) -> PhrasalVerb:
        phrasal_verb = PhrasalVerb(**data)
        db.add(phrasal_verb)
        db.commit()
        db.refresh(phrasal_verb)
        return phrasal_verb

    @staticmethod
    def delete(db: Session, phrasal_verb_id: int) -> bool:
        item = db.query(PhrasalVerb).filter(PhrasalVerb.id == phrasal_verb_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    @staticmethod
    def get_random(
        db: Session,
        count: int = 3,
        exclude_ids: list[int] | None = None,
        separable_only: bool | None = None,
    ) -> list[PhrasalVerb]:
        query = db.query(PhrasalVerb)

        if exclude_ids:
            query = query.filter(PhrasalVerb.id.notin_(exclude_ids))

        if separable_only is not None:
            query = query.filter(PhrasalVerb.is_separable == separable_only)

        return query.order_by(func.random()).limit(count).all()

    @staticmethod
    def get_by_base_verb(db: Session, base_verb: str) -> list[PhrasalVerb]:
        return (
            db.query(PhrasalVerb)
            .filter(func.lower(PhrasalVerb.base_verb) == base_verb.lower())
            .all()
        )

    @staticmethod
    def add_context(
        db: Session, phrasal_verb_id: int, context_data: dict
    ) -> PhrasalVerbContext:
        context = PhrasalVerbContext(phrasal_verb_id=phrasal_verb_id, **context_data)
        db.add(context)
        db.commit()
        db.refresh(context)
        return context


class IrregularVerbRepository:
    """Repository for IrregularVerb CRUD operations."""

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        pattern: str | None = None,
        cefr_level: str | None = None,
    ) -> tuple[list[IrregularVerb], int]:
        query = db.query(IrregularVerb)

        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(IrregularVerb.base_form).like(search_pattern),
                    func.lower(IrregularVerb.past_simple).like(search_pattern),
                    func.lower(IrregularVerb.past_participle).like(search_pattern),
                    cast(IrregularVerb.translations, String).like(search_pattern),
                )
            )

        if pattern:
            query = query.filter(IrregularVerb.verb_pattern == pattern)

        if cefr_level:
            query = query.filter(IrregularVerb.cefr_level == cefr_level)

        total = query.count()

        items = (
            query.order_by(
                IrregularVerb.frequency_rank.asc().nullslast(),
                IrregularVerb.base_form.asc(),
            )
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return items, total

    @staticmethod
    def get_by_id(db: Session, irregular_verb_id: int) -> IrregularVerb | None:
        return (
            db.query(IrregularVerb)
            .options(joinedload(IrregularVerb.contexts))
            .filter(IrregularVerb.id == irregular_verb_id)
            .first()
        )

    @staticmethod
    def get_by_base_form(db: Session, base_form: str) -> IrregularVerb | None:
        return (
            db.query(IrregularVerb)
            .filter(func.lower(IrregularVerb.base_form) == base_form.lower())
            .first()
        )

    @staticmethod
    def get_by_any_form(db: Session, form: str) -> IrregularVerb | None:
        """Find irregular verb by any of its three forms."""
        form_lower = form.lower()
        return (
            db.query(IrregularVerb)
            .filter(
                or_(
                    func.lower(IrregularVerb.base_form) == form_lower,
                    func.lower(IrregularVerb.past_simple) == form_lower,
                    func.lower(IrregularVerb.past_participle) == form_lower,
                )
            )
            .first()
        )

    @staticmethod
    def create(db: Session, data: dict) -> IrregularVerb:
        irregular_verb = IrregularVerb(**data)
        db.add(irregular_verb)
        db.commit()
        db.refresh(irregular_verb)
        return irregular_verb

    @staticmethod
    def delete(db: Session, irregular_verb_id: int) -> bool:
        item = (
            db.query(IrregularVerb).filter(IrregularVerb.id == irregular_verb_id).first()
        )
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    @staticmethod
    def get_random(
        db: Session,
        count: int = 3,
        exclude_ids: list[int] | None = None,
        pattern: str | None = None,
    ) -> list[IrregularVerb]:
        query = db.query(IrregularVerb)

        if exclude_ids:
            query = query.filter(IrregularVerb.id.notin_(exclude_ids))

        if pattern:
            query = query.filter(IrregularVerb.verb_pattern == pattern)

        return query.order_by(func.random()).limit(count).all()

    @staticmethod
    def get_by_pattern(db: Session, pattern: str) -> list[IrregularVerb]:
        """Get all verbs matching a pattern (ABC, ABB, AAA, ABA)."""
        return (
            db.query(IrregularVerb)
            .filter(IrregularVerb.verb_pattern == pattern)
            .all()
        )

    @staticmethod
    def add_context(
        db: Session, irregular_verb_id: int, context_data: dict
    ) -> IrregularVerbContext:
        context = IrregularVerbContext(
            irregular_verb_id=irregular_verb_id, **context_data
        )
        db.add(context)
        db.commit()
        db.refresh(context)
        return context
