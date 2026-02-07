from sqlalchemy.orm import Session
from backend.modules.learning.service import LearningService
from backend.modules.learning.models import UserWord
from backend.modules.words.models import Word, WordContext
from backend.modules.training.service import TrainingService
from backend.modules.training.exercises import (
    generate_introduction,
    generate_recognition,
    generate_recall,
    generate_context,
    generate_sentence_builder,
    generate_free_production,
    generate_listening,
)
from backend.modules.settings.service import SettingsService
from backend.shared.constants import EXERCISE_TIME_ESTIMATES
from .schemas import StartSessionResult


class StartSessionWorkflow:
    def __init__(self, db: Session):
        self.db = db
        self.learning = LearningService(db)
        self.training = TrainingService(db)
        self.settings = SettingsService(db)

    def execute(self, duration_minutes: int | None = None) -> StartSessionResult:
        settings = self.settings.get_settings()
        duration = duration_minutes or settings.session_duration_minutes
        total_seconds = duration * 60

        overdue = self._get_overdue_words()
        learning = self._get_learning_words()
        new_ids = self._get_new_words(settings.daily_new_words)

        exercises = []
        time_used = 0

        review_queue = overdue + learning
        new_queue = list(new_ids)
        review_idx = 0
        new_idx = 0
        count_since_new = 0

        while time_used < total_seconds:
            if count_since_new >= 3 and new_idx < len(new_queue):
                word_id = new_queue[new_idx]
                new_idx += 1
                count_since_new = 0
                exercise = self._build_exercise_for_new(word_id)
                if exercise:
                    est = EXERCISE_TIME_ESTIMATES.get(exercise["exercise_type"], 10)
                    time_used += est
                    exercises.append(exercise)
            elif review_idx < len(review_queue):
                uw = review_queue[review_idx]
                review_idx += 1
                count_since_new += 1
                exercise = self._build_exercise(uw)
                if exercise:
                    est = EXERCISE_TIME_ESTIMATES.get(exercise["exercise_type"], 10)
                    time_used += est
                    exercises.append(exercise)
            elif new_idx < len(new_queue):
                word_id = new_queue[new_idx]
                new_idx += 1
                count_since_new = 0
                exercise = self._build_exercise_for_new(word_id)
                if exercise:
                    est = EXERCISE_TIME_ESTIMATES.get(exercise["exercise_type"], 10)
                    time_used += est
                    exercises.append(exercise)
            else:
                break

        session = self.training.create_session(self.db)

        return StartSessionResult(
            session_id=session.id,
            exercises=[e for e in exercises],
            total_words=len(exercises),
        )

    def _get_overdue_words(self) -> list:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return (
            self.db.query(UserWord)
            .filter(UserWord.next_review_at < now)
            .filter(UserWord.mastery_level > 0)
            .order_by(UserWord.next_review_at.asc())
            .all()
        )

    def _get_learning_words(self) -> list:
        return (
            self.db.query(UserWord)
            .filter(UserWord.fsrs_state.in_([1, 3]))
            .all()
        )

    def _get_new_words(self, limit: int) -> list[int]:
        from sqlalchemy import not_
        existing = self.db.query(UserWord.word_id).subquery()
        return [
            r[0] for r in
            self.db.query(Word.id)
            .filter(Word.id.not_in(self.db.query(UserWord.word_id)))
            .order_by(Word.frequency_rank.asc())
            .limit(limit)
            .all()
        ]

    def _build_exercise(self, uw: UserWord) -> dict | None:
        word = self.db.query(Word).filter(Word.id == uw.word_id).first()
        if not word:
            return None
        return self._generate_for_level(word, uw.mastery_level)

    def _build_exercise_for_new(self, word_id: int) -> dict | None:
        word = self.db.query(Word).filter(Word.id == word_id).first()
        if not word:
            return None
        return self._generate_for_level(word, 1)

    def _generate_for_level(self, word: Word, level: int) -> dict:
        contexts = (
            self.db.query(WordContext)
            .filter(WordContext.word_id == word.id)
            .limit(3)
            .all()
        )
        distractors = self._get_distractors(word)

        word_data = {
            "word_id": word.id,
            "english": word.english,
            "transcription": word.transcription or "",
            "translations": word.translations or [],
            "part_of_speech": word.part_of_speech or "",
        }
        ctx = contexts[0] if contexts else None
        ctx_data = {
            "sentence_en": ctx.sentence_en if ctx else "",
            "sentence_ru": ctx.sentence_ru if ctx else "",
        } if ctx else {"sentence_en": "", "sentence_ru": ""}

        if level == 1:
            ex = generate_introduction(word_data, [
                {"sentence_en": c.sentence_en, "sentence_ru": c.sentence_ru or ""}
                for c in contexts
            ])
        elif level == 2:
            ex = generate_recognition(word_data, distractors)
        elif level == 3:
            ex = generate_recall(word_data)
        elif level == 4:
            ex = generate_context(word_data, ctx_data, distractors)
        elif level == 5:
            ex = generate_sentence_builder(word_data, ctx_data)
        elif level == 6:
            ex = generate_free_production(word_data)
        elif level == 7:
            ex = generate_listening(word_data, ctx_data)
        else:
            ex = generate_introduction(word_data, [
                {"sentence_en": c.sentence_en, "sentence_ru": c.sentence_ru or ""}
                for c in contexts
            ])

        return ex.model_dump() if hasattr(ex, "model_dump") else ex

    def _get_distractors(self, word: Word) -> list[str]:
        from sqlalchemy import func
        words = (
            self.db.query(Word)
            .filter(Word.id != word.id)
            .filter(Word.part_of_speech == word.part_of_speech)
            .order_by(func.random())
            .limit(3)
            .all()
        )
        result = []
        for w in words:
            if w.translations:
                result.append(w.translations[0] if isinstance(w.translations, list) else str(w.translations))
            else:
                result.append(w.english)
        return result
