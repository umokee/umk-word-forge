from sqlalchemy.orm import Session
from backend.modules.words.service import WordService
from backend.modules.words.schemas import WordCreate
from backend.modules.words.models import WordContext
from backend.modules.learning.service import LearningService
from backend.modules.ai.service import ai_service
from .schemas import AddWordResult


class AddWordWorkflow:
    def __init__(self, db: Session):
        self.db = db
        self.words = WordService(db)
        self.learning = LearningService(db)

    async def execute(self, word_create: WordCreate) -> AddWordResult:
        word = self.words.create_word(self.db, word_create)

        self.learning.initialize_word(self.db, word.id)

        contexts_generated = 0
        if ai_service:
            try:
                result = await ai_service.generate_contexts(
                    word.english, word_create.part_of_speech or "noun"
                )
                for ctx in result.contexts:
                    context = WordContext(
                        word_id=word.id,
                        sentence_en=ctx.get("en", ""),
                        sentence_ru=ctx.get("ru", ""),
                        difficulty=ctx.get("difficulty", 1),
                        source="ai-generated",
                    )
                    self.db.add(context)
                    contexts_generated += 1
            except Exception:
                pass

        self.db.commit()

        return AddWordResult(
            word_id=word.id,
            english=word.english,
            added_to_learning=True,
            contexts_generated=contexts_generated,
        )
