from sqlalchemy import func, or_, cast, String
from sqlalchemy.orm import Session, joinedload

from backend.modules.words.models import Word, WordContext


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
