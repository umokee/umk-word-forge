from sqlalchemy.orm import Session

from backend.modules.words.exceptions import WordNotFoundError, WordAlreadyExistsError
from backend.modules.words.repository import WordRepository
from backend.modules.words.schemas import WordCreate, PaginatedWords, WordListResponse


class WordService:

    def __init__(self) -> None:
        self._repo = WordRepository()

    def get_words(
        self,
        db: Session,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        cefr_level: str | None = None,
        part_of_speech: str | None = None,
    ) -> PaginatedWords:
        words, total = self._repo.get_all(
            db,
            page=page,
            per_page=per_page,
            search=search,
            cefr_level=cefr_level,
            part_of_speech=part_of_speech,
        )
        return PaginatedWords(
            items=[WordListResponse.model_validate(w) for w in words],
            total=total,
            page=page,
            per_page=per_page,
        )

    def get_word(self, db: Session, word_id: int):
        word = self._repo.get_by_id(db, word_id)
        if not word:
            raise WordNotFoundError(word_id)
        return word

    def create_word(self, db: Session, word_create: WordCreate):
        existing = self._repo.get_by_english(db, word_create.english)
        if existing:
            raise WordAlreadyExistsError(word_create.english)

        word_data = word_create.model_dump()
        return self._repo.create(db, word_data)

    def delete_word(self, db: Session, word_id: int) -> None:
        deleted = self._repo.delete(db, word_id)
        if not deleted:
            raise WordNotFoundError(word_id)

    def search_words(self, db: Session, query: str):
        return self._repo.search(db, query)

    def get_distractors(self, db: Session, word_id: int, count: int = 3):
        word = self._repo.get_by_id(db, word_id)
        if not word:
            raise WordNotFoundError(word_id)

        distractors = self._repo.get_random_words(
            db,
            count=count,
            part_of_speech=word.part_of_speech,
            exclude_ids=[word_id],
        )
        return distractors
