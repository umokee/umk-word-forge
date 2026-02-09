from sqlalchemy.orm import Session
from backend.modules.learning.service import LearningService
from backend.modules.learning.schemas import ReviewCreate
from backend.modules.training.service import TrainingService
from backend.modules.stats.service import StatsService
from backend.modules.words.models import Word
from backend.shared.text_utils import normalize_text, levenshtein_distance, get_translations
from .schemas import SubmitAnswerResult


class SubmitAnswerWorkflow:
    def __init__(self, db: Session):
        self.db = db
        self.learning = LearningService(db)
        self.training = TrainingService(db)
        self.stats = StatsService(db)

    def execute(
        self,
        session_id: int,
        word_id: int,
        answer: str,
        exercise_type: int,
        response_time_ms: int,
    ) -> SubmitAnswerResult:
        word = self.db.query(Word).filter(Word.id == word_id).first()
        if not word:
            return SubmitAnswerResult(
                correct=False, rating=1, correct_answer="",
                mastery_level=0, level_changed=False,
            )

        correct, rating, correct_answer = self._evaluate(
            word, answer, exercise_type, response_time_ms
        )

        review = ReviewCreate(
            exercise_type=exercise_type,
            rating=rating,
            response_time_ms=response_time_ms,
            correct=correct,
        )

        try:
            mastery = self.learning.record_review(self.db, word_id, review)
        except Exception:
            self.learning.initialize_word(self.db, word_id)
            mastery = self.learning.record_review(self.db, word_id, review)

        self.training.record_answer(
            self.db, session_id,
            {"word_id": word_id, "correct": correct}
        )

        self.stats.record_review(self.db, correct=correct)

        self.db.commit()

        feedback = None
        if not correct:
            translations = get_translations(word)
            feedback = f"Correct: {word.english} — {', '.join(translations)}"

        return SubmitAnswerResult(
            correct=correct,
            rating=rating,
            correct_answer=correct_answer,
            feedback=feedback,
            mastery_level=mastery.new_level,
            level_changed=mastery.level_changed,
            next_review=mastery.next_review,
        )

    def _evaluate(
        self, word: Word, answer: str, exercise_type: int, response_time_ms: int
    ) -> tuple[bool, int, str]:
        translations = get_translations(word)
        correct_answer = word.english
        normalized_answer = normalize_text(answer)

        if exercise_type == 1:
            return True, 3, correct_answer

        if exercise_type == 2:
            correct_translation = translations[0] if translations else ""
            is_correct = (
                normalized_answer == normalize_text(correct_translation)
                or normalized_answer == normalize_text(word.english)
            )
            if is_correct and response_time_ms < 3000:
                return True, 4, correct_translation
            elif is_correct:
                return True, 3, correct_translation
            else:
                return False, 1, correct_translation

        if exercise_type == 3:
            dist = levenshtein_distance(normalized_answer, normalize_text(word.english))
            if dist == 0:
                if response_time_ms < 5000:
                    return True, 4, word.english
                return True, 3, word.english
            elif dist <= 1 and len(word.english) > 4:
                return True, 2, word.english
            else:
                return False, 1, word.english

        if exercise_type == 4:
            is_correct = normalized_answer == normalize_text(word.english)
            if is_correct and response_time_ms < 5000:
                return True, 4, word.english
            elif is_correct:
                return True, 3, word.english
            else:
                return False, 1, word.english

        if exercise_type == 5:
            is_correct = normalized_answer == normalize_text(answer)
            if response_time_ms < 15000:
                return is_correct, 4 if is_correct else 1, correct_answer
            return is_correct, 3 if is_correct else 1, correct_answer

        if exercise_type == 6:
            return True, 3, correct_answer

        if exercise_type == 7:
            dist = levenshtein_distance(normalized_answer, normalize_text(word.english))
            if dist == 0:
                return True, 4, word.english
            elif dist <= 1:
                return True, 3, word.english
            else:
                return False, 1, word.english

        return False, 1, correct_answer
