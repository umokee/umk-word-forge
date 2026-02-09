from datetime import datetime, timezone
from sqlalchemy.orm import Session

from fsrs import Scheduler, Card, Rating, State

from backend.shared.constants import (
    CONSECUTIVE_CORRECT_TO_LEVEL_UP,
    CONSECUTIVE_WRONG_TO_LEVEL_DOWN,
    LOW_STABILITY_THRESHOLD,
)
from backend.modules.learning.exceptions import WordNotInLearningError, WordAlreadyInLearningError
from backend.modules.learning.models import UserWord, UserPhrasalVerb, UserIrregularVerb
from backend.modules.learning.repository import (
    LearningRepository,
    PhrasalVerbLearningRepository,
    IrregularVerbLearningRepository,
)
from backend.modules.learning.schemas import (
    ReviewCreate,
    MasteryResult,
    LearningStatsResponse,
    UserWordResponse,
    UserWordWithWord,
    DueWordsResponse,
    PaginatedUserWords,
    UserPhrasalVerbResponse,
    UserPhrasalVerbWithPhrasal,
    PhrasalVerbReviewCreate,
    DuePhrasalVerbsResponse,
    PaginatedUserPhrasalVerbs,
    UserIrregularVerbResponse,
    UserIrregularVerbWithIrregular,
    IrregularVerbReviewCreate,
    DueIrregularVerbsResponse,
    PaginatedUserIrregularVerbs,
)
from backend.modules.words.models import Word, PhrasalVerb, IrregularVerb

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

    def initialize_word(self, db: Session, word_id: int, initial_mastery: int = 1) -> UserWord:
        """Add a word to the learning list and initialize its FSRS card.

        Args:
            db: Database session
            word_id: ID of the word to initialize
            initial_mastery: Starting mastery level (default=1 for Introduction,
                           use 2 to skip Introduction for words that passed training)
        """
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
            mastery_level=initial_mastery,
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


class PhrasalVerbLearningService:
    """Service for learning phrasal verbs with FSRS scheduling."""

    _MIN_MASTERY = 1
    _MAX_MASTERY = 6  # 6 exercise types for phrasal verbs

    def __init__(self) -> None:
        self._repo = PhrasalVerbLearningRepository()
        self._scheduler = Scheduler()

    @staticmethod
    def _card_from_user_phrasal_verb(upv: UserPhrasalVerb) -> Card:
        """Reconstruct an FSRS Card from persisted UserPhrasalVerb fields."""
        card = Card()
        card.stability = upv.fsrs_stability if upv.fsrs_stability else None
        card.difficulty = upv.fsrs_difficulty if upv.fsrs_difficulty else None
        card.state = State(upv.fsrs_state) if upv.fsrs_state in (1, 2, 3) else State.Learning
        card.step = 0 if upv.fsrs_state == 0 else None
        card.last_review = upv.fsrs_last_review
        card.due = upv.next_review_at or datetime.now(timezone.utc)
        return card

    @staticmethod
    def _update_user_phrasal_verb_from_card(upv: UserPhrasalVerb, card: Card) -> None:
        """Persist FSRS Card fields back to UserPhrasalVerb."""
        upv.fsrs_stability = card.stability or 0
        upv.fsrs_difficulty = card.difficulty or 0
        upv.fsrs_state = card.state.value if card.state else 0
        upv.fsrs_last_review = card.last_review
        upv.next_review_at = card.due

    def initialize_phrasal_verb(self, db: Session, phrasal_verb_id: int) -> UserPhrasalVerb:
        """Add a phrasal verb to the learning list."""
        existing = self._repo.get_user_phrasal_verb(db, phrasal_verb_id)
        if existing:
            raise WordAlreadyInLearningError(phrasal_verb_id)

        pv = db.query(PhrasalVerb).filter(PhrasalVerb.id == phrasal_verb_id).first()
        if not pv:
            from backend.modules.words.exceptions import WordNotFoundError
            raise WordNotFoundError(phrasal_verb_id)

        card = Card()

        user_pv = self._repo.create_user_phrasal_verb(
            db,
            phrasal_verb_id=phrasal_verb_id,
            mastery_level=1,
            fsrs_stability=card.stability or 0,
            fsrs_difficulty=card.difficulty or 0,
            fsrs_state=0,
            fsrs_last_review=None,
            next_review_at=card.due,
        )

        return user_pv

    def record_review(
        self, db: Session, phrasal_verb_id: int, review: PhrasalVerbReviewCreate
    ) -> MasteryResult:
        """Record a review and update FSRS scheduling + mastery level."""
        user_pv = self._repo.get_user_phrasal_verb(db, phrasal_verb_id)
        if not user_pv:
            raise WordNotInLearningError(phrasal_verb_id)

        card = self._card_from_user_phrasal_verb(user_pv)
        rating = Rating(review.rating)

        new_card, _log = self._scheduler.review_card(card, rating)
        self._update_user_phrasal_verb_from_card(user_pv, new_card)

        user_pv.fsrs_reps += 1
        if rating == Rating.Again:
            user_pv.fsrs_lapses += 1

        if new_card.last_review and card.last_review:
            elapsed = (new_card.last_review - card.last_review).days
            user_pv.fsrs_elapsed_days = max(elapsed, 0)
        else:
            user_pv.fsrs_elapsed_days = 0

        if new_card.due and new_card.last_review:
            scheduled = (new_card.due - new_card.last_review).days
            user_pv.fsrs_scheduled_days = max(scheduled, 0)
        else:
            user_pv.fsrs_scheduled_days = 0

        if review.correct:
            user_pv.consecutive_correct += 1
            user_pv.consecutive_wrong = 0
        else:
            user_pv.consecutive_wrong += 1
            user_pv.consecutive_correct = 0

        old_level = user_pv.mastery_level
        new_level = old_level

        if (
            user_pv.consecutive_correct >= CONSECUTIVE_CORRECT_TO_LEVEL_UP
            and rating in (Rating.Good, Rating.Easy)
        ):
            new_level = min(old_level + 1, self._MAX_MASTERY)
            user_pv.consecutive_correct = 0

        if user_pv.consecutive_wrong >= CONSECUTIVE_WRONG_TO_LEVEL_DOWN:
            new_level = max(old_level - 1, self._MIN_MASTERY)
            user_pv.consecutive_wrong = 0

        if (
            rating == Rating.Again
            and user_pv.fsrs_stability < LOW_STABILITY_THRESHOLD
            and user_pv.fsrs_lapses > 0
        ):
            new_level = max(old_level - 2, self._MIN_MASTERY)

        user_pv.mastery_level = new_level
        self._repo.update_user_phrasal_verb(db, user_pv)

        self._repo.create_review(
            db,
            user_phrasal_verb_id=user_pv.id,
            exercise_type=review.exercise_type,
            rating=review.rating,
            response_time_ms=review.response_time_ms,
            correct=review.correct,
        )

        return MasteryResult(
            new_level=new_level,
            level_changed=new_level != old_level,
            next_review=user_pv.next_review_at,
        )

    def get_due_phrasal_verbs(self, db: Session) -> DuePhrasalVerbsResponse:
        """Get phrasal verbs that are due for review."""
        now = datetime.now(timezone.utc)
        due_items = self._repo.get_due_phrasal_verbs(db)

        overdue: list[UserPhrasalVerbWithPhrasal] = []
        learning: list[UserPhrasalVerbWithPhrasal] = []

        for upv in due_items:
            pv = db.query(PhrasalVerb).filter(PhrasalVerb.id == upv.phrasal_verb_id).first()
            enriched = UserPhrasalVerbWithPhrasal(
                id=upv.id,
                phrasal_verb_id=upv.phrasal_verb_id,
                mastery_level=upv.mastery_level,
                consecutive_correct=upv.consecutive_correct,
                consecutive_wrong=upv.consecutive_wrong,
                fsrs_stability=upv.fsrs_stability,
                fsrs_difficulty=upv.fsrs_difficulty,
                fsrs_state=upv.fsrs_state,
                fsrs_reps=upv.fsrs_reps,
                fsrs_lapses=upv.fsrs_lapses,
                next_review_at=upv.next_review_at,
                created_at=upv.created_at,
                phrase=pv.phrase if pv else "",
                base_verb=pv.base_verb if pv else "",
                particle=pv.particle if pv else "",
                translations=pv.translations if pv else [],
                definitions=pv.definitions if pv else [],
                is_separable=pv.is_separable if pv else True,
            )

            if upv.fsrs_state in (1, 3):
                learning.append(enriched)
            else:
                overdue.append(enriched)

        new_ids = self._repo.get_new_phrasal_verb_ids(db, limit=100)
        new_available = len(new_ids)

        return DuePhrasalVerbsResponse(
            overdue=overdue,
            learning=learning,
            new_available=new_available,
        )

    def get_learning_stats(self, db: Session) -> dict:
        """Aggregate learning statistics for phrasal verbs."""
        stats = self._repo.get_learning_stats(db)
        by_level = self._repo.count_by_level(db)
        by_state_raw = self._repo.count_by_state(db)

        by_state = {
            _STATE_NAMES.get(state_int, f"Unknown({state_int})"): count
            for state_int, count in by_state_raw.items()
        }

        return {
            "total_phrasal_verbs": stats["total_phrasal_verbs"],
            "by_level": by_level,
            "by_state": by_state,
        }


class IrregularVerbLearningService:
    """Service for learning irregular verbs with FSRS scheduling."""

    _MIN_MASTERY = 1
    _MAX_MASTERY = 6  # 6 exercise types for irregular verbs

    def __init__(self) -> None:
        self._repo = IrregularVerbLearningRepository()
        self._scheduler = Scheduler()

    @staticmethod
    def _card_from_user_irregular_verb(uiv: UserIrregularVerb) -> Card:
        """Reconstruct an FSRS Card from persisted UserIrregularVerb fields."""
        card = Card()
        card.stability = uiv.fsrs_stability if uiv.fsrs_stability else None
        card.difficulty = uiv.fsrs_difficulty if uiv.fsrs_difficulty else None
        card.state = State(uiv.fsrs_state) if uiv.fsrs_state in (1, 2, 3) else State.Learning
        card.step = 0 if uiv.fsrs_state == 0 else None
        card.last_review = uiv.fsrs_last_review
        card.due = uiv.next_review_at or datetime.now(timezone.utc)
        return card

    @staticmethod
    def _update_user_irregular_verb_from_card(uiv: UserIrregularVerb, card: Card) -> None:
        """Persist FSRS Card fields back to UserIrregularVerb."""
        uiv.fsrs_stability = card.stability or 0
        uiv.fsrs_difficulty = card.difficulty or 0
        uiv.fsrs_state = card.state.value if card.state else 0
        uiv.fsrs_last_review = card.last_review
        uiv.next_review_at = card.due

    def initialize_irregular_verb(self, db: Session, irregular_verb_id: int) -> UserIrregularVerb:
        """Add an irregular verb to the learning list."""
        existing = self._repo.get_user_irregular_verb(db, irregular_verb_id)
        if existing:
            raise WordAlreadyInLearningError(irregular_verb_id)

        iv = db.query(IrregularVerb).filter(IrregularVerb.id == irregular_verb_id).first()
        if not iv:
            from backend.modules.words.exceptions import WordNotFoundError
            raise WordNotFoundError(irregular_verb_id)

        card = Card()

        user_iv = self._repo.create_user_irregular_verb(
            db,
            irregular_verb_id=irregular_verb_id,
            mastery_level=1,
            fsrs_stability=card.stability or 0,
            fsrs_difficulty=card.difficulty or 0,
            fsrs_state=0,
            fsrs_last_review=None,
            next_review_at=card.due,
        )

        return user_iv

    def record_review(
        self, db: Session, irregular_verb_id: int, review: IrregularVerbReviewCreate
    ) -> MasteryResult:
        """Record a review and update FSRS scheduling + mastery level."""
        user_iv = self._repo.get_user_irregular_verb(db, irregular_verb_id)
        if not user_iv:
            raise WordNotInLearningError(irregular_verb_id)

        card = self._card_from_user_irregular_verb(user_iv)
        rating = Rating(review.rating)

        new_card, _log = self._scheduler.review_card(card, rating)
        self._update_user_irregular_verb_from_card(user_iv, new_card)

        user_iv.fsrs_reps += 1
        if rating == Rating.Again:
            user_iv.fsrs_lapses += 1

        if new_card.last_review and card.last_review:
            elapsed = (new_card.last_review - card.last_review).days
            user_iv.fsrs_elapsed_days = max(elapsed, 0)
        else:
            user_iv.fsrs_elapsed_days = 0

        if new_card.due and new_card.last_review:
            scheduled = (new_card.due - new_card.last_review).days
            user_iv.fsrs_scheduled_days = max(scheduled, 0)
        else:
            user_iv.fsrs_scheduled_days = 0

        if review.correct:
            user_iv.consecutive_correct += 1
            user_iv.consecutive_wrong = 0
        else:
            user_iv.consecutive_wrong += 1
            user_iv.consecutive_correct = 0

        old_level = user_iv.mastery_level
        new_level = old_level

        if (
            user_iv.consecutive_correct >= CONSECUTIVE_CORRECT_TO_LEVEL_UP
            and rating in (Rating.Good, Rating.Easy)
        ):
            new_level = min(old_level + 1, self._MAX_MASTERY)
            user_iv.consecutive_correct = 0

        if user_iv.consecutive_wrong >= CONSECUTIVE_WRONG_TO_LEVEL_DOWN:
            new_level = max(old_level - 1, self._MIN_MASTERY)
            user_iv.consecutive_wrong = 0

        if (
            rating == Rating.Again
            and user_iv.fsrs_stability < LOW_STABILITY_THRESHOLD
            and user_iv.fsrs_lapses > 0
        ):
            new_level = max(old_level - 2, self._MIN_MASTERY)

        user_iv.mastery_level = new_level
        self._repo.update_user_irregular_verb(db, user_iv)

        self._repo.create_review(
            db,
            user_irregular_verb_id=user_iv.id,
            exercise_type=review.exercise_type,
            rating=review.rating,
            response_time_ms=review.response_time_ms,
            correct=review.correct,
        )

        return MasteryResult(
            new_level=new_level,
            level_changed=new_level != old_level,
            next_review=user_iv.next_review_at,
        )

    def get_due_irregular_verbs(self, db: Session) -> DueIrregularVerbsResponse:
        """Get irregular verbs that are due for review."""
        now = datetime.now(timezone.utc)
        due_items = self._repo.get_due_irregular_verbs(db)

        overdue: list[UserIrregularVerbWithIrregular] = []
        learning: list[UserIrregularVerbWithIrregular] = []

        for uiv in due_items:
            iv = db.query(IrregularVerb).filter(IrregularVerb.id == uiv.irregular_verb_id).first()
            enriched = UserIrregularVerbWithIrregular(
                id=uiv.id,
                irregular_verb_id=uiv.irregular_verb_id,
                mastery_level=uiv.mastery_level,
                consecutive_correct=uiv.consecutive_correct,
                consecutive_wrong=uiv.consecutive_wrong,
                fsrs_stability=uiv.fsrs_stability,
                fsrs_difficulty=uiv.fsrs_difficulty,
                fsrs_state=uiv.fsrs_state,
                fsrs_reps=uiv.fsrs_reps,
                fsrs_lapses=uiv.fsrs_lapses,
                next_review_at=uiv.next_review_at,
                created_at=uiv.created_at,
                base_form=iv.base_form if iv else "",
                past_simple=iv.past_simple if iv else "",
                past_participle=iv.past_participle if iv else "",
                translations=iv.translations if iv else [],
                verb_pattern=iv.verb_pattern if iv else "",
                transcription_base=iv.transcription_base if iv else None,
                transcription_past=iv.transcription_past if iv else None,
                transcription_participle=iv.transcription_participle if iv else None,
            )

            if uiv.fsrs_state in (1, 3):
                learning.append(enriched)
            else:
                overdue.append(enriched)

        new_ids = self._repo.get_new_irregular_verb_ids(db, limit=100)
        new_available = len(new_ids)

        return DueIrregularVerbsResponse(
            overdue=overdue,
            learning=learning,
            new_available=new_available,
        )

    def get_learning_stats(self, db: Session) -> dict:
        """Aggregate learning statistics for irregular verbs."""
        stats = self._repo.get_learning_stats(db)
        by_level = self._repo.count_by_level(db)
        by_state_raw = self._repo.count_by_state(db)

        by_state = {
            _STATE_NAMES.get(state_int, f"Unknown({state_int})"): count
            for state_int, count in by_state_raw.items()
        }

        return {
            "total_irregular_verbs": stats["total_irregular_verbs"],
            "by_level": by_level,
            "by_state": by_state,
        }
