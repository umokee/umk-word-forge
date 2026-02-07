from datetime import datetime, timezone
from sqlalchemy.orm import Session

from fsrs import Scheduler, Card, Rating, State

from backend.shared.constants import (
    CONSECUTIVE_CORRECT_TO_LEVEL_UP,
    CONSECUTIVE_WRONG_TO_LEVEL_DOWN,
    LOW_STABILITY_THRESHOLD,
)
from backend.modules.learning.exceptions import WordNotInLearningError, WordAlreadyInLearningError
from backend.modules.learning.models import UserWord
from backend.modules.learning.repository import LearningRepository
from backend.modules.learning.schemas import (
    ReviewCreate,
    MasteryResult,
    LearningStatsResponse,
    UserWordResponse,
    UserWordWithWord,
    DueWordsResponse,
    PaginatedUserWords,
)
from backend.modules.words.models import Word

_STATE_NAMES = {0: "New", 1: "Learning", 2: "Review", 3: "Relearning"}

_MIN_MASTERY = 1
_MAX_MASTERY = 7


class LearningService:

    def __init__(self) -> None:
        self._repo = LearningRepository()
        self._scheduler = Scheduler()

    # ------------------------------------------------------------------
    # Card reconstruction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _card_from_user_word(uw: UserWord) -> Card:
        """Reconstruct an FSRS Card from persisted UserWord fields."""
        card = Card()
        card.stability = uw.fsrs_stability if uw.fsrs_stability else None
        card.difficulty = uw.fsrs_difficulty if uw.fsrs_difficulty else None
        card.state = State(uw.fsrs_state) if uw.fsrs_state in (1, 2, 3) else State.Learning
        card.step = 0 if uw.fsrs_state == 0 else None
        card.last_review = uw.fsrs_last_review
        card.due = uw.next_review_at or datetime.now(timezone.utc)
        return card

    @staticmethod
    def _update_user_word_from_card(uw: UserWord, card: Card) -> None:
        """Persist FSRS Card fields back to UserWord."""
        uw.fsrs_stability = card.stability or 0
        uw.fsrs_difficulty = card.difficulty or 0
        uw.fsrs_state = card.state.value if card.state else 0
        uw.fsrs_last_review = card.last_review
        uw.next_review_at = card.due

    @staticmethod
    def _rating_enum(rating_int: int) -> Rating:
        """Convert integer rating (1-4) to FSRS Rating enum."""
        return Rating(rating_int)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize_word(self, db: Session, word_id: int) -> UserWord:
        """Add a word to the learning list and initialize its FSRS card."""
        existing = self._repo.get_user_word(db, word_id)
        if existing:
            raise WordAlreadyInLearningError(word_id)

        # Verify the word exists in the dictionary
        word = db.query(Word).filter(Word.id == word_id).first()
        if not word:
            from backend.modules.words.exceptions import WordNotFoundError
            raise WordNotFoundError(word_id)

        # Create a fresh FSRS card to get initial scheduling
        card = Card()

        user_word = self._repo.create_user_word(
            db,
            word_id=word_id,
            mastery_level=1,
            fsrs_stability=card.stability or 0,
            fsrs_difficulty=card.difficulty or 0,
            fsrs_state=0,  # New
            fsrs_last_review=None,
            next_review_at=card.due,
        )

        return user_word

    def record_review(self, db: Session, word_id: int, review: ReviewCreate) -> MasteryResult:
        """Record a review and update FSRS scheduling + mastery level."""
        user_word = self._repo.get_user_word(db, word_id)
        if not user_word:
            raise WordNotInLearningError(word_id)

        # Reconstruct FSRS Card from stored fields
        card = self._card_from_user_word(user_word)
        rating = self._rating_enum(review.rating)

        # Run FSRS scheduling
        new_card, _log = self._scheduler.review_card(card, rating)

        # Persist FSRS state back to UserWord
        self._update_user_word_from_card(user_word, new_card)

        # Track reps and lapses manually
        user_word.fsrs_reps += 1
        if rating == Rating.Again:
            user_word.fsrs_lapses += 1

        # Calculate elapsed and scheduled days
        if new_card.last_review and card.last_review:
            elapsed = (new_card.last_review - card.last_review).days
            user_word.fsrs_elapsed_days = max(elapsed, 0)
        else:
            user_word.fsrs_elapsed_days = 0

        if new_card.due and new_card.last_review:
            scheduled = (new_card.due - new_card.last_review).days
            user_word.fsrs_scheduled_days = max(scheduled, 0)
        else:
            user_word.fsrs_scheduled_days = 0

        # Update consecutive correct/wrong streaks
        if review.correct:
            user_word.consecutive_correct += 1
            user_word.consecutive_wrong = 0
        else:
            user_word.consecutive_wrong += 1
            user_word.consecutive_correct = 0

        # Apply mastery level rules
        old_level = user_word.mastery_level
        new_level = old_level

        # 3 consecutive Good/Easy -> level up
        if (
            user_word.consecutive_correct >= CONSECUTIVE_CORRECT_TO_LEVEL_UP
            and rating in (Rating.Good, Rating.Easy)
        ):
            new_level = min(old_level + 1, _MAX_MASTERY)
            user_word.consecutive_correct = 0  # Reset streak after level change

        # 2 consecutive Again -> level down
        if user_word.consecutive_wrong >= CONSECUTIVE_WRONG_TO_LEVEL_DOWN:
            new_level = max(old_level - 1, _MIN_MASTERY)
            user_word.consecutive_wrong = 0  # Reset streak after level change

        # Stability < 0.5 after a lapse -> level down by 2
        if (
            rating == Rating.Again
            and user_word.fsrs_stability < LOW_STABILITY_THRESHOLD
            and user_word.fsrs_lapses > 0
        ):
            new_level = max(old_level - 2, _MIN_MASTERY)

        user_word.mastery_level = new_level
        self._repo.update_user_word(db, user_word)

        # Save the review record
        self._repo.create_review(db, user_word.id, review)

        return MasteryResult(
            new_level=new_level,
            level_changed=new_level != old_level,
            next_review=user_word.next_review_at,
        )

    def get_due_words(self, db: Session) -> DueWordsResponse:
        """Get words that are due for review, split into overdue and learning."""
        now = datetime.now(timezone.utc)
        due_user_words = self._repo.get_due_words(db)

        overdue: list[UserWordWithWord] = []
        learning: list[UserWordWithWord] = []

        for uw in due_user_words:
            word = db.query(Word).filter(Word.id == uw.word_id).first()
            enriched = UserWordWithWord(
                id=uw.id,
                word_id=uw.word_id,
                mastery_level=uw.mastery_level,
                consecutive_correct=uw.consecutive_correct,
                consecutive_wrong=uw.consecutive_wrong,
                fsrs_stability=uw.fsrs_stability,
                fsrs_difficulty=uw.fsrs_difficulty,
                fsrs_state=uw.fsrs_state,
                fsrs_reps=uw.fsrs_reps,
                fsrs_lapses=uw.fsrs_lapses,
                next_review_at=uw.next_review_at,
                created_at=uw.created_at,
                english=word.english if word else "",
                transcription=word.transcription if word else None,
                translations=word.translations if word else [],
                part_of_speech=word.part_of_speech if word else None,
            )

            if uw.fsrs_state in (1, 3):  # Learning or Relearning
                learning.append(enriched)
            else:
                overdue.append(enriched)

        # Count new words available for introduction
        new_word_ids = self._repo.get_new_word_ids(db, limit=100)
        new_available = len(new_word_ids)

        return DueWordsResponse(
            overdue=overdue,
            learning=learning,
            new_available=new_available,
        )

    def get_learning_stats(self, db: Session) -> LearningStatsResponse:
        """Aggregate learning statistics across all user words."""
        stats = self._repo.get_learning_stats(db)
        by_level = self._repo.count_by_level(db)
        by_state_raw = self._repo.count_by_state(db)

        by_state = {
            _STATE_NAMES.get(state_int, f"Unknown({state_int})"): count
            for state_int, count in by_state_raw.items()
        }

        return LearningStatsResponse(
            total_words=stats["total_words"],
            by_level=by_level,
            by_state=by_state,
        )

    def get_user_words(
        self,
        db: Session,
        page: int = 1,
        per_page: int = 20,
        level: int | None = None,
        state: int | None = None,
    ) -> PaginatedUserWords:
        """List user's learning words with pagination and filters."""
        items, total = self._repo.get_user_words(
            db,
            page=page,
            per_page=per_page,
            level_filter=level,
            state_filter=state,
        )

        return PaginatedUserWords(
            items=[UserWordResponse.model_validate(uw) for uw in items],
            total=total,
            page=page,
            per_page=per_page,
        )

    def get_user_word(self, db: Session, word_id: int) -> UserWordWithWord:
        """Get learning details for a specific word, enriched with word data."""
        uw = self._repo.get_user_word(db, word_id)
        if not uw:
            raise WordNotInLearningError(word_id)

        word = db.query(Word).filter(Word.id == uw.word_id).first()

        return UserWordWithWord(
            id=uw.id,
            word_id=uw.word_id,
            mastery_level=uw.mastery_level,
            consecutive_correct=uw.consecutive_correct,
            consecutive_wrong=uw.consecutive_wrong,
            fsrs_stability=uw.fsrs_stability,
            fsrs_difficulty=uw.fsrs_difficulty,
            fsrs_state=uw.fsrs_state,
            fsrs_reps=uw.fsrs_reps,
            fsrs_lapses=uw.fsrs_lapses,
            next_review_at=uw.next_review_at,
            created_at=uw.created_at,
            english=word.english if word else "",
            transcription=word.transcription if word else None,
            translations=word.translations if word else [],
            part_of_speech=word.part_of_speech if word else None,
        )
