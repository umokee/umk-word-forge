# WordForge v2 — Полная спецификация для Claude Code

> Этот документ — единственный источник правды для сборки приложения.
> Следуй ему точно, не добавляй своих решений без явного указания.

---

## 1. Обзор проекта

**WordForge** — self-hosted веб-приложение для долгосрочного изучения английских слов. Разработано под кинестетика-практика (ISTJ): не пассивные карточки, а активная проработка каждого слова через 7 уровней глубины до автоматизма.

**Ключевые принципы:**
- Каждое слово проходит 7 уровней «прокачки» (от знакомства до аудирования)
- FSRS-алгоритм определяет КОГДА повторять, mastery level — КАКОЕ упражнение дать
- Один пользователь, self-hosted на локальной машине или сервере
- Тёмная тема, острые углы, без цветных эмодзи, без лишнего

**Целевой путь:** A0 → понимание носителей на YouTube/подкастах/фильмах.

---

## 2. Технологический стек

### Backend (Python)
- **Python 3.12+**
- **FastAPI** — HTTP-фреймворк
- **SQLAlchemy 2.0** — ORM (async не требуется, sync достаточно)
- **Pydantic v2** — валидация и DTOs
- **Alembic** — миграции БД
- **SQLite** — БД (один пользователь, файловая, ноль настройки)
- **py-fsrs** — Python-реализация FSRS v5 (`pip install py-fsrs`)
- **Uvicorn** — ASGI-сервер

### Frontend (TypeScript)
- **React 18** + **TypeScript**
- **Vite** — сборка
- **Tailwind CSS** — стилизация (тёмная тема, острые углы)
- **React Router v7** — маршрутизация
- **TanStack Query (React Query)** — серверное состояние и кэширование
- **Zustand** — клиентское состояние (тренировочная сессия)
- **@dnd-kit/core** — drag-and-drop (уровень 5)
- **Recharts** — графики статистики
- **Lucide React** — иконки (линейные, монохромные)

### AI / Внешние сервисы
- **Google Gemini API** (free tier, 250 RPD) — проверка свободных ответов (уровень 6), генерация контекстов
- **Groq API** (fallback, 14400 RPD) — Llama 4 Scout для резервной проверки
- **Web Speech API** — TTS в браузере (бесплатно, без API-ключей)

### Инфраструктура
- Self-hosted (локальная машина или VPS)
- SQLite файл в `/data/wordforge.db`
- Без Docker (опционально можно добавить позже)
- Без внешних БД, без Redis, без очередей

---

## 3. Архитектура: Modular Monolith

Проект следует паттерну **Modular Monolith** с **Orchestrator** (Workflows) для координации между модулями.

### 3.1 Структура проекта

```
wordforge/
├── backend/
│   ├── main.py                     # Entry point, FastAPI app assembly
│   ├── core/                       # Infrastructure (НЕТ бизнес-логики)
│   │   ├── __init__.py
│   │   ├── database.py             # Engine, SessionLocal, Base, get_db()
│   │   ├── exceptions.py           # Base exception classes
│   │   ├── security.py             # Simple API key / password verification
│   │   └── config.py               # Settings (Pydantic BaseSettings)
│   ├── shared/                     # Утилиты (НЕТ бизнес-логики)
│   │   ├── __init__.py
│   │   ├── constants.py            # App-wide constants
│   │   ├── date_utils.py           # Date/time helpers
│   │   └── text_utils.py           # Levenshtein distance, text normalization
│   ├── modules/                    # Бизнес-модули (изолированные)
│   │   ├── words/                  # Словарь: слова, контексты, аудио
│   │   │   ├── __init__.py         # PUBLIC API
│   │   │   ├── models.py           # Word, WordContext, WordAudio (PRIVATE)
│   │   │   ├── schemas.py          # DTOs
│   │   │   ├── repository.py       # Data access (PRIVATE)
│   │   │   ├── service.py          # Business logic
│   │   │   ├── routes.py           # HTTP endpoints
│   │   │   └── exceptions.py       # WordNotFoundError, etc.
│   │   ├── learning/               # Обучение: FSRS, mastery, reviews
│   │   │   ├── __init__.py
│   │   │   ├── models.py           # UserWord, Review (PRIVATE)
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py          # FSRS scheduling, mastery logic
│   │   │   ├── routes.py
│   │   │   └── exceptions.py
│   │   ├── training/               # Тренировочные сессии и упражнения
│   │   │   ├── __init__.py
│   │   │   ├── models.py           # Session, SessionWord (PRIVATE)
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py          # Session generator, exercise logic
│   │   │   ├── routes.py
│   │   │   ├── exercises.py        # 7 exercise type generators (PRIVATE)
│   │   │   └── exceptions.py
│   │   ├── stats/                  # Статистика и аналитика
│   │   │   ├── __init__.py
│   │   │   ├── models.py           # DailyStats (PRIVATE)
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py          # Coverage calculation, streaks
│   │   │   ├── routes.py
│   │   │   └── exceptions.py
│   │   ├── ai/                     # AI-интеграция (Gemini, Groq)
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py          # AICheckResult, AIContextResult
│   │   │   ├── service.py          # Multi-provider with fallback
│   │   │   ├── routes.py
│   │   │   ├── prompts.py          # System prompts for each task (PRIVATE)
│   │   │   └── exceptions.py
│   │   └── settings/               # Настройки пользователя
│   │       ├── __init__.py
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── repository.py
│   │       ├── service.py
│   │       └── routes.py
│   ├── workflows/                  # Orchestrators (кросс-модульная координация)
│   │   ├── __init__.py
│   │   ├── start_session.py        # Формирование тренировочной сессии
│   │   ├── submit_answer.py        # Обработка ответа: review + mastery + stats
│   │   ├── add_word.py             # Добавление нового слова + контексты + AI
│   │   └── schemas.py              # Workflow result DTOs
│   ├── seed/                       # Начальные данные
│   │   ├── __init__.py
│   │   └── words_500.py            # 500 частотных слов с контекстами
│   └── alembic/                    # Миграции
│       ├── alembic.ini
│       └── versions/
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx                # Entry point
│   │   ├── App.tsx                 # Router setup
│   │   ├── api/                    # API client
│   │   │   ├── client.ts           # Fetch wrapper with base URL
│   │   │   ├── words.ts            # Word API calls
│   │   │   ├── learning.ts         # Learning API calls
│   │   │   ├── training.ts         # Training session API calls
│   │   │   └── stats.ts            # Stats API calls
│   │   ├── pages/                  # Route pages
│   │   │   ├── Dashboard.tsx       # Главная: статистика дня, быстрые действия
│   │   │   ├── Train.tsx           # Тренировка: упражнения
│   │   │   ├── Words.tsx           # Мои слова: таблица, фильтры, карточки
│   │   │   ├── Stats.tsx           # Статистика: графики, heatmap
│   │   │   ├── WordDetail.tsx      # Карточка слова: уровень, контексты, история
│   │   │   └── Settings.tsx        # Настройки
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Layout.tsx
│   │   │   │   └── Header.tsx
│   │   │   ├── training/
│   │   │   │   ├── ExerciseIntroduction.tsx    # Level 1
│   │   │   │   ├── ExerciseRecognition.tsx     # Level 2
│   │   │   │   ├── ExerciseRecall.tsx          # Level 3
│   │   │   │   ├── ExerciseContext.tsx         # Level 4
│   │   │   │   ├── ExerciseSentenceBuilder.tsx # Level 5
│   │   │   │   ├── ExerciseFreeProduction.tsx  # Level 6
│   │   │   │   ├── ExerciseListening.tsx       # Level 7
│   │   │   │   ├── SessionProgress.tsx
│   │   │   │   └── AnswerFeedback.tsx
│   │   │   ├── words/
│   │   │   │   ├── WordTable.tsx
│   │   │   │   ├── WordCard.tsx
│   │   │   │   └── WordFilters.tsx
│   │   │   ├── stats/
│   │   │   │   ├── DailyChart.tsx
│   │   │   │   ├── CoverageBar.tsx
│   │   │   │   ├── HeatmapCalendar.tsx
│   │   │   │   └── LevelDistribution.tsx
│   │   │   └── ui/
│   │   │       ├── Button.tsx
│   │   │       ├── Input.tsx
│   │   │       ├── Card.tsx
│   │   │       ├── Badge.tsx
│   │   │       ├── ProgressBar.tsx
│   │   │       ├── Table.tsx
│   │   │       └── Modal.tsx
│   │   ├── hooks/
│   │   │   ├── useKeyboard.ts      # Горячие клавиши (1-4 для ответов)
│   │   │   ├── useTimer.ts         # Таймер ответа
│   │   │   └── useTTS.ts           # Web Speech API wrapper
│   │   ├── stores/
│   │   │   └── trainingStore.ts    # Zustand: текущая сессия, прогресс
│   │   ├── lib/
│   │   │   └── utils.ts            # cn(), formatters, etc.
│   │   └── types/
│   │       └── index.ts            # Shared TypeScript types
│   └── public/
│       └── fonts/                  # JetBrains Mono
└── README.md
```

### 3.2 Правила архитектуры

**Модуль = чёрный ящик.** Внешний код видит только то, что экспортировано в `__init__.py`.

```python
# ✅ Правильно — импорт из __init__.py модуля
from modules.words import WordService, WordResponse

# ❌ Запрещено — лезть внутрь модуля
from modules.words.repository import WordRepository
from modules.words.models import Word
```

**Модули НЕ знают друг друга.** Вся кросс-модульная координация — через Workflows.

```python
# ❌ Запрещено — modules/learning/service.py
from modules.words import WordService  # НЕТ!

# ✅ Правильно — workflows/submit_answer.py
from modules.learning import LearningService
from modules.training import TrainingService
from modules.stats import StatsService
```

**Данные вместо зависимостей.** Модули возвращают DTOs (Pydantic models), не ORM-модели.

**FK через ID, без ORM relationships между модулями.**

```python
# modules/learning/models.py
class UserWord(Base):
    __tablename__ = "user_words"
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"))  # FK как plain integer
    # НЕ делать: word = relationship("Word")
```

### 3.3 Import Rules

```
main.py          → imports everything
workflows/*      → imports modules (via __init__), core, shared
modules/X/routes → imports modules/X/*, core, shared, workflows
modules/X/service→ imports modules/X/*, core, shared
modules/X/repo   → imports modules/X/models, core/database
core/*           → imports shared, external packages
shared/*         → imports external packages only
```

### 3.4 Workflow Examples

```python
# workflows/submit_answer.py
from sqlalchemy.orm import Session
from modules.learning import LearningService, ReviewCreate, MasteryResult
from modules.training import TrainingService
from modules.stats import StatsService
from .schemas import SubmitAnswerResult

class SubmitAnswerWorkflow:
    def __init__(self, db: Session):
        self.db = db
        self.learning = LearningService(db)
        self.training = TrainingService(db)
        self.stats = StatsService(db)

    def execute(self, session_id: int, word_id: int, answer: ReviewCreate) -> SubmitAnswerResult:
        # 1. Record review and update FSRS card
        mastery = self.learning.record_review(word_id, answer)

        # 2. Update session progress
        self.training.record_session_answer(session_id, word_id, answer.correct)

        # 3. Update daily stats
        self.stats.record_review(correct=answer.correct)

        self.db.commit()

        return SubmitAnswerResult(
            mastery_level=mastery.new_level,
            level_changed=mastery.level_changed,
            next_review=mastery.next_review,
            session_progress=self.training.get_progress(session_id)
        )
```

---

## 4. Дизайн-система

### 4.1 Критические правила

1. **Тёмная тема** — единственный режим. Светлой темы нет.
2. **Острые углы** — `rounded-none` или `rounded-sm` (max 2px). Никаких `rounded-lg`, `rounded-xl`, `rounded-full`. Исключение: прогресс-бары `rounded-sm`.
3. **Без цветных эмодзи** — использовать Lucide React иконки (линейные, монохромные) или текстовые символы: →, ·, /, |, #
4. **Шрифт:** Inter (основной) + JetBrains Mono (английские слова, транскрипция, цифры, код)

### 4.2 Цветовая палитра

```
Фон основной:       #0A0A0B
Фон карточки:        #141416
Фон вторичный:       #1C1C20
Фон третичный:       #242428
Бордеры:             #2A2A30
Бордеры hover:       #3A3A42
Текст основной:      #E8E8EC
Текст вторичный:     #8B8B96
Текст третичный:     #5C5C66
Акцент основной:     #6366F1 (indigo-500)
Акцент hover:        #818CF8 (indigo-400)
Акцент muted:        rgba(99, 102, 241, 0.2)
Успех:               #22C55E
Ошибка:              #EF4444
Предупреждение:      #F59E0B
Прогресс уровней:    #6366F1 → #A78BFA → #C084FC
```

### 4.3 Tailwind компоненты

```
Карточки:         bg-[#141416] border border-[#2A2A30] rounded-sm p-4
Кнопки primary:   bg-indigo-600 hover:bg-indigo-500 text-white rounded-sm px-4 py-2
Кнопки secondary: bg-transparent border border-[#2A2A30] hover:border-[#3A3A42] text-[#E8E8EC] rounded-sm
Кнопки ghost:     bg-transparent hover:bg-[#1C1C20] text-[#8B8B96]
Input:            bg-[#1C1C20] border border-[#2A2A30] focus:border-indigo-500 text-[#E8E8EC] rounded-sm
Badge:            bg-[#1C1C20] text-[#8B8B96] rounded-sm px-2 py-0.5 text-xs font-mono
Sidebar item:     hover:bg-[#1C1C20] rounded-sm px-3 py-2
Active sidebar:   bg-indigo-600/10 text-indigo-400 border-l-2 border-indigo-500
Таблицы:          border-collapse, border-[#2A2A30], чётные строки bg-[#141416]
ProgressBar:      bg-[#1C1C20] rounded-sm h-1.5 / fill: bg-indigo-500 rounded-sm
```

### 4.4 Типографика

```
H1:    text-2xl font-bold text-[#E8E8EC] tracking-tight
H2:    text-xl font-semibold text-[#E8E8EC]
H3:    text-lg font-medium text-[#E8E8EC]
Body:  text-sm text-[#8B8B96]
Small: text-xs text-[#5C5C66]
Mono:  font-mono text-sm (для английских слов, транскрипции, цифр, статистики)
```

### 4.5 Анимации

- Переходы между экранами: fade 150ms
- Hover на кнопках: transition-colors 100ms
- Drag-and-drop: spring-анимация (CSS transitions)
- Появление карточек: slide-up 200ms
- Правильный ответ: бордер зелёный 300ms → fade
- Неправильный ответ: shake 300ms + бордер красный
- Всё должно быть быстрым и чётким, без тяжёлых анимаций

---

## 5. База данных (SQLAlchemy Models)

### 5.1 modules/words/models.py

```python
class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True)
    english = Column(String, nullable=False, unique=True, index=True)
    transcription = Column(String)              # IPA: /sɒlv/
    part_of_speech = Column(String)             # noun, verb, adj, adv, etc.
    translations = Column(JSON)                 # ["решать", "разрешать"]
    frequency_rank = Column(Integer)            # Частотный ранг (1 = самое частое)
    cefr_level = Column(String)                 # A1, A2, B1, B2, C1, C2

    # Relationships (within module)
    contexts = relationship("WordContext", back_populates="word", cascade="all,delete")

class WordContext(Base):
    __tablename__ = "word_contexts"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    sentence_en = Column(String, nullable=False)    # "I need to solve this problem."
    sentence_ru = Column(String)                     # "Мне нужно решить эту проблему."
    source = Column(String)                          # YouTube video title / URL
    difficulty = Column(Integer, default=1)          # 1=easy, 2=medium, 3=hard

    word = relationship("Word", back_populates="contexts")
```

### 5.2 modules/learning/models.py

```python
class UserWord(Base):
    __tablename__ = "user_words"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, unique=True, index=True)

    # Mastery
    mastery_level = Column(Integer, default=0)      # 0-7
    consecutive_correct = Column(Integer, default=0) # Для повышения уровня
    consecutive_wrong = Column(Integer, default=0)   # Для понижения уровня

    # FSRS Card State
    fsrs_stability = Column(Float, default=0)
    fsrs_difficulty = Column(Float, default=0)
    fsrs_elapsed_days = Column(Integer, default=0)
    fsrs_scheduled_days = Column(Integer, default=0)
    fsrs_reps = Column(Integer, default=0)
    fsrs_lapses = Column(Integer, default=0)
    fsrs_state = Column(Integer, default=0)          # 0=New, 1=Learning, 2=Review, 3=Relearning
    fsrs_last_review = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=func.now())

    # Relationships within module
    reviews = relationship("Review", back_populates="user_word", cascade="all,delete")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_word_id = Column(Integer, ForeignKey("user_words.id"), nullable=False)

    exercise_type = Column(Integer)          # 1-7 (тип упражнения / уровень)
    rating = Column(Integer)                 # 1=Again, 2=Hard, 3=Good, 4=Easy
    response_time_ms = Column(Integer)       # Время ответа в мс
    correct = Column(Boolean)

    created_at = Column(DateTime, default=func.now())

    user_word = relationship("UserWord", back_populates="reviews")
```

### 5.3 modules/training/models.py

```python
class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)

    words_reviewed = Column(Integer, default=0)
    words_new = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
```

### 5.4 modules/stats/models.py

```python
class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, index=True)

    words_reviewed = Column(Integer, default=0)
    words_learned = Column(Integer, default=0)     # Новые слова в этот день
    time_spent = Column(Integer, default=0)         # Секунды
    accuracy = Column(Float, default=0)             # 0-1
    streak = Column(Integer, default=0)             # Серия дней подряд
```

### 5.5 modules/settings/models.py

```python
class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, default=1)  # Всегда 1 (один пользователь)
    daily_new_words = Column(Integer, default=10)
    session_duration_minutes = Column(Integer, default=15)
    preferred_exercises = Column(JSON, default=list)     # [] = все включены
    tts_enabled = Column(Boolean, default=True)
    tts_speed = Column(Float, default=1.0)
    keyboard_shortcuts = Column(Boolean, default=True)
```

---

## 6. FSRS Алгоритм

### 6.1 Библиотека

```bash
pip install py-fsrs
```

### 6.2 Интеграция (modules/learning/service.py)

```python
from fsrs import FSRS, Card, Rating

f = FSRS()

# При первом знакомстве со словом
card = Card()

# После каждого ответа
# rating: Rating.Again (1) | Rating.Hard (2) | Rating.Good (3) | Rating.Easy (4)
card, review_log = f.review_card(card, Rating.Good)

# card содержит:
# - card.due: datetime — когда следующее повторение
# - card.stability: float
# - card.difficulty: float
# - card.elapsed_days: int
# - card.scheduled_days: int
# - card.reps: int
# - card.lapses: int
# - card.state: State (New=0, Learning=1, Review=2, Relearning=3)
```

### 6.3 Связь FSRS ↔ Mastery Levels

FSRS управляет **КОГДА** показывать слово. Mastery level определяет **КАКОЕ** упражнение:

```
Level 0: Не изучено (слово в словаре, но не начато)
Level 1: Знакомство — показ карточки (Introduction)
Level 2: Узнавание — выбор перевода из 4 вариантов (Recognition)
Level 3: Вспоминание — набрать слово по-английски (Recall)
Level 4: Контекст — предложение с пропуском (Context Fill)
Level 5: Конструктор — собрать предложение из слов (Sentence Builder)
Level 6: Производство — написать своё предложение, AI проверит (Free Production)
Level 7: Распознавание — услышать и написать слово (Listening)
```

### 6.4 Правила повышения/понижения

```
Повышение (+1 level):
  3 подряд ответа "Good" или "Easy" на текущем уровне

Понижение (-1 level):
  2 подряд ответа "Again" на текущем уровне

Понижение (-2 levels):
  FSRS stability < 0.5 после lapse

Минимальный уровень: 1 (после знакомства нельзя вернуться в 0)
Максимальный уровень: 7
```

---

## 7. Семь типов упражнений

### Level 1: Знакомство (Introduction)

**Экран:**
- Слово крупно: `text-3xl font-bold font-mono`
- Транскрипция: `/sɒlv/`
- Иконка звука (TTS)
- Переводы: "решать, разрешать"
- Часть речи: `verb`
- 3 примера в контексте — целевое слово выделено `text-indigo-400 font-medium`
- Перевод каждого примера: `text-xs text-[#5C5C66]`

**Действие:** Прочитал → "Got it" → UserWord создаётся с masteryLevel=1, FSRS card инициализируется.

---

### Level 2: Узнавание (Recognition)

**Экран:**
- Слово: `text-2xl font-bold font-mono`
- "Выбери правильный перевод:"
- 4 варианта (сетка 2×2): 1 правильный + 3 дистрактора (того же уровня и части речи)
- Горячие клавиши: 1, 2, 3, 4

**После ответа:**
- Правильно: бордер → зелёный, 500ms
- Неправильно: выбранный → красный, правильный → зелёный, показать контекст, 1500ms

**Рейтинг (авто):** correct && fast (<3s) = Easy, correct = Good, incorrect = Again

**Вариация:** Иногда показывать перевод → выбрать английское слово (обратное направление, ~30% случаев)

---

### Level 3: Вспоминание (Recall)

**Экран:**
- Перевод крупно: "решать"
- Часть речи: `verb`
- Поле ввода: placeholder "Напиши по-английски..."
- Подсказка (через 10 сек или кнопка): первая буква "s_____"
- Кнопка "Показать ответ"

**Проверка:**
- Case-insensitive, trim
- Levenshtein distance ≤ 1 для слов > 4 букв → "Почти! Правильно: solve" (rated Hard)
- Показать ответ → rated Again

**Рейтинг:** correct && fast (<5s) = Easy, correct = Good, typo = Hard, wrong/skip = Again

---

### Level 4: Контекст (Context Fill)

**Экран:**
- Предложение с пропуском: "I need to _____ this problem before tomorrow."
- Перевод предложения под ним
- Варианты: 4 кнопки (для простого режима) или поле ввода (для сложного)
- Горячие клавиши: 1-4 или Enter

**Логика:** Использовать контексты из WordContext. Пропуск = целевое слово. Дистракторы = слова той же части речи.

---

### Level 5: Конструктор (Sentence Builder)

**Экран:**
- Перевод предложения: "Мне нужно решить эту проблему до завтра."
- Перемешанные слова-плашки: ["this", "I", "solve", "to", "need", "problem", "before", "tomorrow"]
- Зона для сборки (drop zone) сверху
- Drag-and-drop (@dnd-kit/core) или клик по слову для добавления

**Проверка:** Точное совпадение с оригиналом (case-insensitive). Допускать мелкие вариации порядка если смысл сохраняется? Нет — точный порядок.

**Рейтинг:** correct && fast (<15s) = Easy, correct = Good, 1-2 ошибки = Hard, >2 ошибок = Again

---

### Level 6: Свободное производство (Free Production)

**Экран:**
- Слово: `text-2xl font-bold font-mono` + перевод
- Задание: "Напиши своё предложение с этим словом"
- Большое поле ввода (textarea)
- Кнопка "Проверить" (отправляет на AI)

**AI-проверка (Gemini/Groq):**

```
Промпт: "Пользователь изучает английское слово '{word}' ({translation}).
Он написал предложение: '{sentence}'.
Проверь: 1) грамматика, 2) правильное использование слова, 3) естественность.
Ответь JSON: {
  "correct": bool,
  "grammar_ok": bool,
  "word_usage_ok": bool,
  "natural": bool,
  "feedback_ru": "краткий фидбек на русском",
  "corrected": "исправленное предложение или null"
}"
```

**Debounce:** 500ms перед отправкой.

**Рейтинг:** correct + natural = Easy, correct = Good, minor issues = Hard, wrong usage = Again

---

### Level 7: Распознавание на слух (Listening)

**Экран:**
- Кнопка "Прослушать" (TTS проигрывает предложение с целевым словом)
- Кнопка "Повторить" для повторного прослушивания
- Поле ввода: "Напиши услышанное слово"
- Скорость TTS: настраиваемая (0.7 — 1.2)

**Проверка:** Точное совпадение целевого слова (case-insensitive). Допускать Levenshtein ≤ 1.

**Рейтинг:** correct && first listen = Easy, correct = Good, after repeat = Hard, wrong = Again

---

## 8. Формирование тренировочной сессии

### 8.1 Алгоритм (workflows/start_session.py)

```
Вход: available_time_minutes (от пользователя или настройки)
Выход: ordered list of (word_id, exercise_level)

1. Собрать пул слов:
   a. OVERDUE: слова где next_review_at < now() — отсортировать по просроченности (самые забытые первыми)
   b. LEARNING: слова в state=Learning или Relearning — всегда включать
   c. NEW: слова с mastery_level=0, до daily_new_words лимита — отсортировать по frequency_rank

2. Рассчитать количество:
   - ~4 секунды на Level 1-2 упражнение
   - ~10 секунд на Level 3-4
   - ~20 секунд на Level 5
   - ~30 секунд на Level 6-7
   - Набить сессию до available_time_minutes

3. Порядок в сессии:
   - Чередовать: 2-3 повторения → 1 новое → 2-3 повторения → 1 новое
   - Не давать одно слово подряд (минимум 3 других слова между)

4. Для каждого слова: exercise_level = mastery_level (текущий уровень = тип упражнения)
```

### 8.2 Быстрый режим (5 минут)

Только overdue и learning. Без новых слов. Фокус на удержание.

### 8.3 Полный режим (15-30 минут)

Overdue + learning + новые слова. Полная тренировка.

---

## 9. API Endpoints

### Words

```
GET    /api/words                    # Список слов (с пагинацией, фильтрами)
GET    /api/words/:id                # Одно слово с контекстами
POST   /api/words                    # Добавить слово вручную
DELETE /api/words/:id                # Удалить слово
GET    /api/words/search?q=          # Поиск по английскому/русскому
```

### Learning

```
GET    /api/learning/words           # Мои изучаемые слова (с mastery, FSRS state)
GET    /api/learning/words/:id       # Детали по одному слову
GET    /api/learning/due             # Слова, которые пора повторить
GET    /api/learning/stats           # Общая статистика (всего слов, по уровням)
```

### Training

```
POST   /api/training/session         # Начать сессию { duration_minutes }
GET    /api/training/session/:id     # Текущая сессия (следующее упражнение)
POST   /api/training/session/:id/answer  # Отправить ответ { word_id, rating, response_time_ms, correct }
POST   /api/training/session/:id/end # Закончить сессию
```

### AI

```
POST   /api/ai/check-sentence       # Проверить предложение { word, sentence }
POST   /api/ai/generate-contexts    # Сгенерировать контексты для слова
```

### Stats

```
GET    /api/stats/dashboard          # Данные для дашборда
GET    /api/stats/daily?from=&to=    # Статистика по дням
GET    /api/stats/coverage           # Покрытие речи
GET    /api/stats/heatmap?year=      # Данные для heatmap
```

### Settings

```
GET    /api/settings                 # Текущие настройки
PATCH  /api/settings                 # Обновить настройки
```

---

## 10. Страницы фронтенда

### 10.1 Dashboard (/)

Главная страница после входа.

**Layout:** Sidebar слева (постоянный) + основная область.

**Содержимое:**
- Серия дней подряд (streak) + дата последнего занятия
- Сегодня: слов повторено / новых изучено / точность
- Кнопка "Начать тренировку" (крупная, indigo-600)
- Быстрая тренировка (5 мин) / Полная тренировка (15 мин) / Кастом
- График за неделю (Recharts: bar chart — слова/день)
- Распределение по уровням (7 полосок: level 1-7, сколько слов на каждом)
- Покрытие речи: "Ты знаешь 247 слов → покрываешь 72% бытовой речи"

### 10.2 Training (/train)

Полноэкранный режим тренировки (без sidebar).

**Layout:** Прогресс-бар сверху + упражнение по центру + кнопки ответа внизу.

**Поведение:**
- Показывает упражнение текущего уровня для текущего слова
- После ответа: анимация фидбека → пауза → следующее упражнение
- Горячие клавиши: 1-4 (варианты), Enter (подтвердить), Esc (выйти)
- Таймер ответа (скрытый, для расчёта рейтинга)
- Optimistic updates: мгновенный переход на следующее, запись ответа в фоне
- По завершении: экран-саммари (слов повторено, новых, точность, время)

### 10.3 Words (/words)

**Layout:** Таблица со всеми изучаемыми словами.

**Колонки:** Слово (mono) | Перевод | Уровень (badge 1-7) | Стабильность (FSRS) | Следующее повторение | Добавлено

**Фильтры:** По уровню (1-7), по состоянию (new/learning/review), поиск, сортировка

**Клик по строке → WordDetail:** Карточка слова с полной информацией, контекстами, историей ответов.

### 10.4 Stats (/stats)

- График слов/день за последние 30 дней (Recharts area chart)
- Heatmap календарь за год (как GitHub contributions)
- Точность по уровням (bar chart)
- Покрытие речи (progress bar с процентом)
- Общая статистика: всего слов, изучено, в процессе, забыто

### 10.5 Settings (/settings)

- Новых слов в день: input number (default 10)
- Длительность сессии: input number (default 15 мин)
- TTS: вкл/выкл + скорость (slider 0.7-1.2)
- Горячие клавиши: вкл/выкл
- Gemini API Key: input (сохраняется в .env или в настройках)
- Groq API Key: input (fallback)

---

## 11. Формула покрытия речи

```python
def calculate_coverage(known_words_count: int) -> dict:
    """
    Основано на частотных списках английского языка.
    Top 100 слов = ~50% разговорной речи
    Top 300 = ~65%
    Top 1000 = ~80%
    Top 3000 = ~90%
    Top 5000 = ~95%
    Top 10000 = ~98%
    """
    thresholds = [
        (100, 50), (300, 65), (500, 72), (1000, 80),
        (2000, 86), (3000, 90), (5000, 95), (10000, 98)
    ]
    # Интерполяция между порогами
    ...
```

Показывать пользователю: "Ты знаешь {N} слов → покрываешь {X}% бытовой речи"

---

## 12. AI Integration (modules/ai/service.py)

### 12.1 Multi-provider с fallback

```python
class AIService:
    def __init__(self):
        self.providers = [
            {"name": "gemini", "url": "https://generativelanguage.googleapis.com/...", "model": "gemini-2.5-flash"},
            {"name": "groq", "url": "https://api.groq.com/...", "model": "llama-4-scout"},
        ]

    async def check_sentence(self, word: str, translation: str, sentence: str) -> AICheckResult:
        for provider in self.providers:
            try:
                return await self._call(provider, prompt)
            except (RateLimitError, TimeoutError):
                continue
        raise AllProvidersFailedError()
```

### 12.2 Промпты

**Проверка предложения (Level 6):**
```
Пользователь изучает английское слово '{word}' ({translation}).
Предложение пользователя: '{sentence}'.
Проверь грамматику и использование слова.
Ответь ТОЛЬКО JSON: {"correct": bool, "feedback_ru": "...", "corrected": "..." или null}
```

**Генерация контекстов (при добавлении слова):**
```
Сгенерируй 3 примера предложений с английским словом '{word}' ({part_of_speech}).
Уровень сложности: A1-A2.
Ответь ТОЛЬКО JSON: [{"en": "...", "ru": "...", "difficulty": 1}]
```

---

## 13. Автоматическое заполнение словаря

Словарь заполняется **автоматически** из бесплатных open-source источников. Пользователю не нужно вводить слова вручную — при первом запуске скрипт собирает полный словарь от самых частых слов к редким.

### 13.1 Источники данных

| Данные | Источник | Лицензия | Формат |
|--------|----------|----------|--------|
| Частотный ранг | `wordfreq` (Python library) | MIT | pip install wordfreq |
| IPA транскрипция | `ipa-dict` (open-dict-data/ipa-dict) | MIT | JSON/CSV с GitHub |
| Переводы EN→RU | Словарь Мюллера (mueller-dict) + Gemini batch | Public domain + Free tier | CSV + API |
| Часть речи | spaCy (`en_core_web_sm`) | MIT | pip install spacy |
| Примеры предложений | Tatoeba project (tatoeba.org) | CC BY 2.0 | CSV пары EN-RU |
| CEFR уровень | Определяется по частотному рангу (эвристика) | — | Вычисляемый |

### 13.2 Скрипт seed (backend/seed/)

```
backend/seed/
├── __init__.py
├── main.py                  # Точка входа: python -m backend.seed
├── sources/
│   ├── frequency.py         # wordfreq: получить топ-N слов по частоте
│   ├── ipa.py               # ipa-dict: загрузить IPA транскрипции
│   ├── translations.py      # Mueller dict + Gemini fallback для переводов
│   ├── pos_tagger.py        # spaCy: определить часть речи
│   ├── sentences.py         # Tatoeba: найти примеры предложений
│   └── cefr.py              # Эвристика: ранг → CEFR уровень
├── data/                    # Кэш скачанных данных
│   ├── ipa_en_us.json       # IPA словарь (скачивается при первом запуске)
│   ├── mueller_dict.csv     # Словарь Мюллера
│   └── tatoeba_en_ru.csv    # Пары предложений EN-RU
└── config.py                # Настройки: сколько слов, какие источники
```

### 13.3 Алгоритм заполнения

```python
# seed/main.py — упрощённая логика

def seed_database(word_count: int = 5000):
    """
    1. Получить топ-N английских слов по частоте
    2. Для каждого слова собрать данные из всех источников
    3. Записать в БД
    """

    # Шаг 1: Частотный список
    from wordfreq import top_n_list
    words = top_n_list('en', word_count)
    # Результат: ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', ...]

    # Шаг 2: IPA транскрипция
    ipa_dict = load_ipa_dict()  # Скачать ipa-dict JSON при первом запуске
    # ipa_dict['solve'] → '/sɑːlv/'

    # Шаг 3: Переводы
    translations = load_mueller_dict()  # Основной источник
    # Для слов без перевода — батч-запрос к Gemini (по 100 слов за раз)
    missing = [w for w in words if w not in translations]
    if missing:
        ai_translations = batch_translate_with_gemini(missing)
        translations.update(ai_translations)

    # Шаг 4: Часть речи (spaCy)
    pos_tags = get_pos_tags(words)  # {'solve': 'verb', 'problem': 'noun', ...}

    # Шаг 5: Примеры предложений (Tatoeba)
    sentences = load_tatoeba_pairs()
    # Для каждого слова найти 2-3 предложения где оно встречается

    # Шаг 6: CEFR уровень (эвристика по рангу)
    # Ранг 1-500 → A1, 501-1500 → A2, 1501-3000 → B1,
    # 3001-5000 → B2, 5001-8000 → C1, 8001+ → C2

    # Шаг 7: Записать в БД
    for rank, word in enumerate(words, 1):
        db_word = Word(
            english=word,
            transcription=ipa_dict.get(word),
            part_of_speech=pos_tags.get(word),
            translations=translations.get(word, []),
            frequency_rank=rank,
            cefr_level=rank_to_cefr(rank),
        )
        # + WordContext для каждого найденного предложения
```

### 13.4 Запуск

```bash
# Первый запуск — скачивает данные и заполняет БД (~5000 слов)
python -m backend.seed

# С параметрами
python -m backend.seed --count 10000      # Больше слов
python -m backend.seed --count 1000       # Только топ-1000
python -m backend.seed --skip-ai          # Без Gemini (только Mueller dict)
python -m backend.seed --force            # Перезаписать существующие
```

### 13.5 Зависимости для seed

```
wordfreq>=3.0        # Частотные списки
spacy>=3.0           # POS tagging
# + python -m spacy download en_core_web_sm
```

### 13.6 Дообогащение через AI (опционально)

После базового seed можно запустить дообогащение:

```bash
python -m backend.seed --enrich
```

Это отправит батч-запросы к Gemini для:
- Слов без перевода в Mueller dict → AI перевод
- Слов с < 2 контекстами → AI генерация примеров предложений
- Добавление дополнительных значений/синонимов

Расчёт: 5000 слов ÷ 100 слов на запрос = 50 запросов к Gemini. Бесплатный лимит 250 RPD — укладывается за 1 день с запасом.

---

## 14. Порядок разработки (фазы для Claude Code)

### Фаза 1: Фундамент
1. Backend: FastAPI + SQLAlchemy + SQLite + Alembic setup
2. Core: database.py, config.py, exceptions.py, security.py
3. Shared: constants.py, date_utils.py, text_utils.py
4. Frontend: Vite + React + TypeScript + Tailwind setup
5. UI компоненты: Button, Input, Card, Badge, ProgressBar, Table, Modal
6. Layout: Sidebar + основная область
7. Дизайн-система: тёмная тема, цвета, шрифты

### Фаза 2: Словарь
8. Module words: models, schemas, repository, service, routes
9. Seed система: скрипт автоматического заполнения (wordfreq + ipa-dict + Mueller + Tatoeba + spaCy)
10. Запуск seed: `python -m backend.seed --count 5000`
11. Frontend: страница Words (таблица, фильтры, поиск)
12. Frontend: WordDetail (карточка слова)

### Фаза 3: Ядро обучения
12. Module learning: models, schemas, repository, service (FSRS integration), routes
13. Module training: models, schemas, repository, service (session generator), routes
14. Workflow: start_session, submit_answer
15. Frontend: страница Train (все 7 типов упражнений)
16. Горячие клавиши (1-4, Enter, Esc)

### Фаза 4: AI и продвинутые упражнения
17. Module ai: service (Gemini + Groq), prompts, routes
18. Level 5: Sentence Builder с drag-and-drop
19. Level 6: Free Production + AI проверка
20. Level 7: Listening + Web Speech API TTS

### Фаза 5: Аналитика
21. Module stats: models, schemas, repository, service, routes
22. Frontend: Dashboard
23. Frontend: Stats (графики, heatmap)
24. Покрытие речи

### Фаза 6: Полировка
25. Module settings: models, routes
26. Frontend: Settings
27. Анимации и переходы
28. Адаптивность (responsive)
29. Error handling, loading states

---

## 15. Важные технические примечания

1. **py-fsrs**: `pip install py-fsrs` — Python FSRS v5 реализация. ВСЕ операции с FSRS на сервере.
2. **wordfreq**: `pip install wordfreq` — частотные списки для 40+ языков. Используется для seed и покрытия речи.
3. **spaCy**: `pip install spacy && python -m spacy download en_core_web_sm` — POS tagging для определения части речи.
4. **ipa-dict**: Скачать JSON с github.com/open-dict-data/ipa-dict — IPA транскрипции.
5. **Drag-and-drop**: `@dnd-kit/core` — НЕ react-dnd (устарел).
6. **Графики**: Recharts — легковесный, хорошо работает с React.
7. **TTS**: Web Speech API в браузере. Без серверных API.
8. **Все английские слова, цифры, транскрипция**: отображать `font-mono` (JetBrains Mono).
9. **Debounce** свободного ввода перед отправкой на AI: 500ms.
10. **Optimistic updates** для кнопок ответа (Again/Hard/Good/Easy): мгновенный переход, запись в фоне.
11. **SQLite**: файл `data/wordforge.db`. Создавать директорию при первом запуске.
12. **CORS**: Настроить в FastAPI для localhost (фронт на :5173, бэк на :8000).
13. **Один пользователь**: Без регистрации. Простой API key в .env или вообще без аутентификации для localhost.
14. **Без Docker**: Запуск через `uvicorn backend.main:app` + `npm run dev`.
15. **Hot reload**: Uvicorn с `--reload` для бэка, Vite HMR для фронта.
16. **Seed**: Команда `python -m backend.seed` — автоматическое заполнение 5000+ слов из open-source источников.

---

## 16. Environment Variables (.env)

```env
# Database
DATABASE_URL=sqlite:///data/wordforge.db

# AI Providers
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key

# Security (optional for localhost)
API_KEY=your-optional-api-key

# App
CORS_ORIGINS=http://localhost:5173
DEBUG=true
```

---

## 17. Запуск проекта

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm    # Модель для POS tagging
alembic upgrade head
python -m seed                             # Автозаполнение словаря (~5000 слов)
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # http://localhost:5173
```

### requirements.txt (backend)

```
fastapi>=0.110
uvicorn>=0.27
sqlalchemy>=2.0
alembic>=1.13
pydantic>=2.0
pydantic-settings>=2.0
py-fsrs>=1.0
wordfreq>=3.0
spacy>=3.7
httpx>=0.27
python-dotenv>=1.0
```
