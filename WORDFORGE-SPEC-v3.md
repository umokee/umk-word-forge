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
- Словарь заполняется автоматически ВСЕМИ английскими словами (10000+), от самых частотных к редким
- Система сама подаёт слова в правильном порядке — пользователь просто тренируется

**Целевой путь:** A0 → понимание носителей на YouTube/подкастах/фильмах.

### 1.1 Профиль пользователя (заложен в UX)

```
MBTI:           ISTJ
Sensing:        82% — нужно трогать, делать, видеть результат
Thinking:       80% — логика и эффективность, не "красивая подача"
Introversion:   95% — комфортнее учиться одному, без соц.элементов
Judging:        54% — предсказуемая структура, нет сюрпризов
Enneagram:      6 (Introspector) — надёжность, проверенная система
Openness:       8% — не эксперименты, а проверенные методы
Conscientiousness: 56% — средняя, нужна система которая тянет за собой
Neuroticism:    55% — нужна позитивная обратная связь, не давить за ошибки
```

### 1.2 Как профиль влияет на UX

| Черта | Что это значит для приложения |
|-------|-------------------------------|
| Sensing 82% | Каждое упражнение = действие руками (набрать, кликнуть, перетащить). Никогда "просто прочитай" |
| Thinking 80% | Показывать ПОЧЕМУ дано это упражнение, какой уровень у слова, сколько до следующего |
| Introversion 95% | Полностью автономное обучение. Нет ботов, чатов, соц.элементов |
| Judging 54% | Предсказуемая структура сессии. Пользователь знает что будет дальше |
| Enneagram 6 | Научная база видна: FSRS параметры доступны, алгоритм прозрачен |
| Neuroticism 55% | Ошибки подаются мягко. Не "НЕПРАВИЛЬНО!", а "Почти! Правильно: solve". Акцент на прогрессе |
| Low Openness | Нет рандомных "фич дня", геймификации, анимированных персонажей. Система стабильна и предсказуема |
| Conscientiousness 56% | Streak-система и напоминания мягко мотивируют. Не давят, но помогают не бросить |

### 1.3 Философия дизайна

- **Нулевой порог входа:** открыл → нажал "Тренировка" → учишься. Без регистрации, туториалов, настройки
- **Система тянет за собой:** не нужно думать "что мне учить". Приложение само знает какие слова подать и в каком порядке
- **Тактильное взаимодействие:** каждый экран требует действия. Нет пассивных экранов "прочитай и нажми далее" (кроме Level 1 — первое знакомство)
- **Прозрачная механика:** пользователь всегда видит: какой уровень у слова, когда следующее повторение, почему дано именно это упражнение
- **Позитивный фидбек:** акцент на прогрессе, не на ошибках. "Ты уже знаешь 347 слов — это 74% бытовой речи"

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
- **Google Gemini API** (free tier, 250 RPD) — единственный AI-провайдер. Модель: `gemini-2.5-flash`
  - Проверка свободных ответов (уровень 6)
  - Генерация контекстов при seed
  - Перевод слов без перевода в словаре Мюллера
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
│   │   ├── ai/                     # AI-интеграция (Gemini)
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py          # AICheckResult, AIContextResult
│   │   │   ├── service.py          # Gemini API client
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
│   │   │   ├── TrainPreview.tsx    # Превью сессии перед началом
│   │   │   ├── TrainSummary.tsx    # Итоги сессии
│   │   │   ├── Words.tsx           # Мои слова: таблица, фильтры, карточки
│   │   │   ├── Stats.tsx           # Статистика: графики, heatmap
│   │   │   ├── WordDetail.tsx      # Карточка слова: уровень, контексты, история
│   │   │   ├── Settings.tsx        # Настройки (все секции)
│   │   │   └── Onboarding.tsx      # Первый запуск (4 экрана)
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
│   │   │   │   ├── LevelDistribution.tsx
│   │   │   │   ├── DailyGoalRing.tsx       # Кольцо-прогресс дневной цели
│   │   │   │   ├── StreakBadge.tsx          # Streak с иконкой пламени
│   │   │   │   └── TierProgress.tsx         # Прогресс текущего яруса
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
    exercises_completed = Column(Integer, default=0)# Всего упражнений
    time_spent = Column(Integer, default=0)         # Секунды
    accuracy = Column(Float, default=0)             # 0-1
    streak = Column(Integer, default=0)             # Серия дней подряд
    sessions_count = Column(Integer, default=0)     # Количество сессий

    # Дневная цель
    goal_type = Column(String, default="words")     # "words" | "minutes" | "exercises"
    goal_target = Column(Integer, default=20)       # Цель на день
    goal_progress = Column(Integer, default=0)      # Текущий прогресс
    goal_completed = Column(Boolean, default=False) # Выполнена ли цель

class StreakRecord(Base):
    """Хранит рекордный streak отдельно"""
    __tablename__ = "streak_record"

    id = Column(Integer, primary_key=True, default=1)
    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)
    last_activity_date = Column(Date, nullable=True)
```

### 5.5 modules/settings/models.py

```python
class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, default=1)  # Всегда 1 (один пользователь)

    # --- Обучение ---
    daily_new_words = Column(Integer, default=10)           # Новых слов в день (1-50)
    session_duration_minutes = Column(Integer, default=15)  # Длительность сессии по умолчанию
    max_reviews_per_session = Column(Integer, default=50)   # Макс повторений за сессию
    new_words_position = Column(String, default="end")      # "start" | "middle" | "end" — где в сессии новые слова
    exercise_direction = Column(String, default="mixed")    # "en_to_ru" | "ru_to_en" | "mixed"
    show_transcription = Column(Boolean, default=True)      # Показывать IPA транскрипцию
    show_example_translation = Column(Boolean, default=True)# Показывать перевод примеров
    auto_play_audio = Column(Boolean, default=False)        # Авто-воспроизведение TTS при показе слова
    hint_delay_seconds = Column(Integer, default=10)        # Через сколько сек показать подсказку (Level 3)

    # --- Прогрессия ---
    tier_unlock_threshold = Column(Float, default=0.70)     # Порог разблокировки яруса (0.5-0.9)
    starting_tier = Column(Integer, default=1)              # Начальный ярус (1-9)
    unlock_all_tiers = Column(Boolean, default=False)       # Режим без ограничений

    # --- Интерфейс ---
    keyboard_shortcuts = Column(Boolean, default=True)      # Горячие клавиши
    show_progress_details = Column(Boolean, default=True)   # Показывать детали прогресса (FSRS параметры)
    session_end_summary = Column(Boolean, default=True)     # Показывать итоги сессии
    animation_speed = Column(String, default="normal")      # "fast" | "normal" | "slow" | "none"
    font_size = Column(String, default="normal")            # "small" | "normal" | "large"

    # --- TTS (Text-to-Speech) ---
    tts_enabled = Column(Boolean, default=True)
    tts_speed = Column(Float, default=1.0)                  # 0.5-1.5
    tts_voice = Column(String, default="default")           # Голос браузера
    tts_auto_play_exercises = Column(Boolean, default=False) # Авто-озвучка в упражнениях

    # --- Уведомления ---
    daily_reminder_enabled = Column(Boolean, default=False) # Напоминание в браузере
    daily_reminder_time = Column(String, default="09:00")   # Время напоминания

    # --- AI ---
    gemini_api_key = Column(String, nullable=True)          # Можно хранить в БД
    ai_feedback_language = Column(String, default="ru")     # "ru" | "en" — язык фидбека AI
    ai_difficulty_context = Column(String, default="simple") # "simple" | "medium" | "natural" — сложность AI-контекстов

    # --- Дневная цель ---
    daily_goal_type = Column(String, default="words")       # "words" | "minutes" | "exercises"
    daily_goal_value = Column(Integer, default=20)          # 20 слов / 10 минут / 30 упражнений
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

## 6A. Система прогрессии слов (Word Progression)

Словарь содержит ВСЕ слова (10000+), но пользователь не видит их все сразу. Система автоматически подаёт слова от самых частотных к редким, основываясь на прогрессе.

### 6A.1 Частотные ярусы (Tiers)

```
Tier 1 (A1 Foundation):    Слова 1-300     → 65% бытовой речи
Tier 2 (A1 Expansion):     Слова 301-500   → 72%
Tier 3 (A2 Foundation):    Слова 501-1000  → 80%
Tier 4 (A2 Expansion):     Слова 1001-1500 → 84%
Tier 5 (B1 Foundation):    Слова 1501-2500 → 88%
Tier 6 (B1 Expansion):     Слова 2501-3500 → 91%
Tier 7 (B2 Foundation):    Слова 3501-5000 → 95%
Tier 8 (B2 Expansion):     Слова 5001-7000 → 97%
Tier 9 (C1):               Слова 7001-10000→ 98%
```

### 6A.2 Разблокировка ярусов

Следующий ярус открывается когда **70% слов текущего яруса** достигли mastery_level ≥ 3 (Recall). Это значит пользователь не просто видел слова, а может их активно вспомнить.

```python
def check_tier_unlock(current_tier: int) -> bool:
    """Проверить, можно ли открыть следующий ярус"""
    tier_words = get_words_in_tier(current_tier)
    words_at_recall = count_words_with_mastery_gte(tier_words, min_level=3)
    return words_at_recall / len(tier_words) >= 0.70
```

### 6A.3 Подача новых слов внутри яруса

Внутри открытого яруса новые слова подаются по frequency_rank (самые частые первыми), но ограничены настройкой `daily_new_words`.

```
Пользователь открывает приложение:
1. Сначала: overdue повторения (слова которые пора повторить)
2. Потом: learning слова (ещё не закрепившиеся)
3. В конце: новые слова из текущего яруса (по частоте)
```

### 6A.4 Отображение в UI

**Dashboard:**
- Текущий ярус: "Tier 3 — A2 Foundation" с прогресс-баром (67/100 слов на Recall+)
- "До следующего яруса: ещё 3 слова до Recall"
- Покрытие речи: "Ты знаешь 467 слов → 76% бытовой речи"

**Words page:**
- Вкладки по ярусам или фильтр
- Текущий ярус — развёрнут, будущие ярусы — заблокированы (locked icon)
- Каждый ярус показывает: "Tier 5: 0/1000 слов изучено" с замком

### 6A.5 Настройка (опционально)

Пользователь может в настройках:
- Изменить порог разблокировки (50-90%, default 70%)
- Разблокировать все ярусы вручную (режим "без ограничений")
- Начать с определённого яруса (если уровень не A0)

### 6A.6 Модель в БД

```python
# modules/learning/models.py — добавить
class TierProgress(Base):
    __tablename__ = "tier_progress"

    id = Column(Integer, primary_key=True)
    tier_number = Column(Integer, unique=True, index=True)  # 1-9
    unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime, nullable=True)
    words_total = Column(Integer, default=0)
    words_at_recall = Column(Integer, default=0)  # mastery >= 3
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

**AI-проверка (Gemini):**

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
Вход: available_time_minutes (от пользователя или настройки), mode ("full" | "quick" | "review_only")
Выход: SessionPlan { exercises: list[ExerciseItem], estimated_minutes: int, new_count: int, review_count: int }

1. Собрать пул слов:
   a. OVERDUE: слова где next_review_at < now() — отсортировать по просроченности (самые забытые первыми)
   b. LEARNING: слова в state=Learning или Relearning — всегда включать
   c. NEW: если mode != "review_only":
      - Слова с mastery_level=0 из ТЕКУЩЕГО РАЗБЛОКИРОВАННОГО яруса
      - Отсортировать по frequency_rank (самые частые первыми)
      - Ограничить daily_new_words лимитом (минус уже изученные сегодня)

2. Рассчитать количество:
   - ~4 секунды на Level 1-2 упражнение
   - ~10 секунд на Level 3-4
   - ~20 секунд на Level 5
   - ~30 секунд на Level 6-7
   - Набить сессию до available_time_minutes

3. Позиция новых слов (настройка new_words_position):
   - "start": новые слова в начале, потом повторения
   - "middle": чередование 3 повторения → 1 новое → 3 повторения
   - "end": сначала все повторения, потом новые слова (default)

4. Правило: не давать одно слово подряд (минимум 3 других слова между)

5. Re-queue: если слово получило "Again" — добавить его обратно через 3-5 упражнений

6. Для каждого слова: exercise_level = mastery_level
```

### 8.2 Режимы запуска

| Режим | Что включает | Когда использовать |
|-------|-------------|-------------------|
| **Полная** (full) | Overdue + Learning + New | Есть 15-30 минут |
| **Быстрая** (quick, 5 мин) | Только Overdue + Learning | Мало времени |
| **Только повторения** (review_only) | Overdue + Learning, без New | Не хочется новое, только закрепить |

### 8.3 Превью сессии (SessionPlan)

Перед началом показать пользователю план (см. секцию 15B.1):
- Сколько повторений
- Сколько новых слов
- Примерное время
- Кнопки: "Начать" / "Только повторения"

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
GET    /api/learning/words/:id       # Детали по одному слову (+ история reviews)
GET    /api/learning/due             # Слова, которые пора повторить (count + list)
GET    /api/learning/stats           # Общая статистика (всего слов, по уровням)
GET    /api/learning/tiers           # Прогресс по ярусам (все 9 ярусов)
GET    /api/learning/tiers/current   # Текущий ярус + прогресс до следующего
```

### Training

```
POST   /api/training/session/plan    # Превью сессии { duration_minutes, mode } → SessionPlan
POST   /api/training/session         # Начать сессию { duration_minutes, mode }
GET    /api/training/session/:id     # Текущая сессия (следующее упражнение)
POST   /api/training/session/:id/answer  # Отправить ответ { word_id, rating, response_time_ms, correct }
POST   /api/training/session/:id/end # Закончить сессию → SessionSummary
```

### AI

```
POST   /api/ai/check-sentence       # Проверить предложение { word, sentence }
POST   /api/ai/generate-contexts    # Сгенерировать контексты для слова
GET    /api/ai/status                # Проверить подключение Gemini API
```

### Stats

```
GET    /api/stats/dashboard          # Все данные для дашборда (одним запросом)
GET    /api/stats/daily?from=&to=    # Статистика по дням
GET    /api/stats/coverage           # Покрытие речи (процент + слов до следующего порога)
GET    /api/stats/heatmap?year=      # Данные для heatmap
GET    /api/stats/streak             # Текущий streak + рекорд
GET    /api/stats/daily-goal         # Прогресс дневной цели сегодня
```

### Settings

```
GET    /api/settings                 # Текущие настройки (все поля)
PATCH  /api/settings                 # Обновить настройки (partial update)
POST   /api/settings/export          # Экспорт прогресса → JSON
POST   /api/settings/import          # Импорт прогресса из JSON
POST   /api/settings/reset           # Сброс прогресса (с подтверждением)
```

### Onboarding

```
GET    /api/onboarding/status        # Пройден ли onboarding
POST   /api/onboarding/complete      # Сохранить результаты onboarding { level, goal, api_key? }
```

---

## 10. Страницы фронтенда

### 10.1 Dashboard (/)

Главная страница. Полный layout описан в секции 15C.

**Ключевые элементы:**
- Дневная цель (кольцо-прогресс)
- Статистика сегодня (слова, точность)
- Streak (серия дней)
- 3 кнопки тренировки (полная / быстрая / только повторения) с tooltip-превью
- Покрытие речи (прогресс-бар + число)
- Текущий ярус (прогресс + сколько до следующего)
- Распределение по уровням (7 полосок L1-L7)
- Активность за неделю (bar chart)

### 10.2 Training (/train)

Полноэкранный режим тренировки (без sidebar).

**Layout:** Прогресс-бар сверху + упражнение по центру + кнопки ответа внизу.

**Поведение:**
- Перед началом: экран-превью сессии (см. 15B.1) — сколько слов, сколько времени, какие режимы
- Показывает упражнение текущего уровня для текущего слова
- После ответа: мягкая анимация фидбека (см. 15B.5) → пауза → следующее упражнение
- Горячие клавиши: 1-4 (варианты), Enter (подтвердить), Space (TTS), Tab (подсказка), Escape (пауза)
- Прогресс-бар сверху: "7/23" + мини-статистика "✓ 6 ✗ 1" (см. 15B.2)
- Таймер ответа (скрытый, для расчёта рейтинга)
- Optimistic updates: мгновенный переход на следующее, запись ответа в фоне
- Re-queue ошибочных слов через 3-5 упражнений (см. 15B.6)
- Пауза/выход: модал с 3 вариантами (см. 15B.3)
- По завершении: экран-саммари (см. 15B.4)

### 10.3 Words (/words)

**Layout:** Таблица со всеми изучаемыми словами + вкладки по ярусам.

**Вкладки ярусов сверху:**
- "Tier 1 · A1 (287/300)" / "Tier 2 · A1+ (156/200)" / "Tier 3 · A2 🔒" / ...
- Текущий ярус — активный, будущие — с замком
- Разблокированные но не текущие — доступны для просмотра

**Колонки таблицы:** Слово (mono) | Перевод | Уровень (badge 1-7, цвет по уровню) | Стабильность (FSRS, прогресс-бар) | Следующее повторение (относительное: "через 2 дня") | Ранг (#)

**Фильтры:** По уровню (0-7), по состоянию (new/learning/review/mastered), поиск по слову/переводу, сортировка по колонкам

**Клик по строке → WordDetail:** Карточка слова с полной информацией, контекстами, историей ответов, графиком FSRS stability.

### 10.4 Stats (/stats)

- График слов/день за последние 30 дней (Recharts area chart)
- Heatmap календарь за год (как GitHub contributions)
- Точность по уровням (bar chart)
- Покрытие речи (progress bar с процентом)
- Общая статистика: всего слов, изучено, в процессе, забыто

### 10.5 Settings (/settings)

Организована в секции с чёткими заголовками. Все изменения сохраняются мгновенно (auto-save с debounce 500ms).

**Секция: Обучение**
- Новых слов в день: slider (1-50, default 10) + число рядом
- Длительность сессии по умолчанию: selector (5 / 10 / 15 / 20 / 30 мин)
- Макс повторений за сессию: slider (10-100, default 50)
- Направление упражнений: radio (EN→RU / RU→EN / Смешанное)
- Где в сессии новые слова: radio (В начале / В середине / В конце)
- Задержка подсказки (Level 3): slider (5-30 сек, default 10)

**Секция: Прогрессия**
- Текущий ярус: показать номер + прогресс-бар
- Порог разблокировки: slider (50-90%, default 70%)
- Начальный ярус: selector (для тех кто не A0)
- Кнопка "Разблокировать все ярусы" (toggle)

**Секция: Дневная цель**
- Тип цели: radio (Слова / Минуты / Упражнения)
- Значение: slider + число (20 слов / 10 минут / 30 упражнений)

**Секция: Интерфейс**
- Горячие клавиши: toggle (default ON)
- Размер шрифта: radio (Маленький / Обычный / Крупный)
- Скорость анимаций: radio (Быстро / Обычно / Медленно / Без анимаций)
- Показывать детали прогресса: toggle (FSRS параметры на карточке слова)
- Итоги после сессии: toggle (default ON)

**Секция: Отображение слов**
- Показывать транскрипцию: toggle (default ON)
- Показывать перевод примеров: toggle (default ON)
- Авто-воспроизведение аудио: toggle (default OFF)

**Секция: TTS (Озвучка)**
- TTS включён: toggle (default ON)
- Скорость речи: slider (0.5-1.5, default 1.0) с кнопкой "Прослушать"
- Голос: dropdown (доступные голоса из Web Speech API)
- Авто-озвучка в упражнениях: toggle (default OFF)

**Секция: AI (Gemini)**
- API ключ: password input + кнопка "Проверить" (тестовый запрос)
- Язык фидбека: radio (Русский / English)
- Сложность контекстов: radio (Простые A1-A2 / Средние B1 / Естественные B2+)
- Статус: badge "Подключён" (зелёный) или "Не настроен" (серый)

**Секция: Данные**
- Экспорт прогресса: кнопка → JSON файл
- Импорт прогресса: кнопка → загрузить JSON
- Сброс прогресса: кнопка с подтверждением (красная)
- Пересеять словарь: кнопка → перезапуск seed с новыми параметрами

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

### 12.1 Gemini-only провайдер

```python
class AIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def check_sentence(self, word: str, translation: str, sentence: str) -> AICheckResult:
        """Проверка предложения пользователя (Level 6)"""
        prompt = self._build_check_prompt(word, translation, sentence)
        response = self._call_gemini(prompt)
        return AICheckResult.model_validate_json(response)

    def generate_contexts(self, word: str, pos: str, count: int = 3) -> list[AIContextResult]:
        """Генерация примеров предложений для слова"""
        prompt = self._build_context_prompt(word, pos, count)
        response = self._call_gemini(prompt)
        return [AIContextResult.model_validate(ctx) for ctx in json.loads(response)]

    def batch_translate(self, words: list[str]) -> dict[str, list[str]]:
        """Батч-перевод слов (для seed)"""
        prompt = self._build_translate_prompt(words)
        response = self._call_gemini(prompt)
        return json.loads(response)

    def _call_gemini(self, prompt: str) -> str:
        """Вызов Gemini API с retry"""
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json"
            }
        }
        response = httpx.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
```

### 12.2 Обработка ошибок

```python
# Если API недоступен — упражнение Level 6 деградирует:
# Вместо AI-проверки показать: "AI недоступен. Сравни своё предложение с примером:"
# + показать правильный контекст из WordContext
# Рейтинг: пользователь сам оценивает (кнопки Again/Hard/Good/Easy)
```

### 12.3 Лимиты

```
Gemini 2.5 Flash free tier: 250 RPD (requests per day)
Средний расход: 3-5 запросов/день (только Level 6 упражнения)
Запас: ~50x от потребности одного пользователя
```

### 12.4 Промпты

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

Словарь заполняется **полностью автоматически** из бесплатных open-source источников. При первом запуске скрипт собирает **ВСЕ** слова (10000+) от самых частых к редким. Пользователю не нужно ничего вводить — система сама подаёт слова в правильном порядке через ярусы (см. секцию 6A).

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

def seed_database(word_count: int = 10000):
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
# Первый запуск — скачивает данные и заполняет БД (10000 слов, ~5-10 минут)
python -m backend.seed

# С параметрами
python -m backend.seed --count 15000     # Ещё больше слов
python -m backend.seed --count 3000      # Только топ-3000 (быстрее)
python -m backend.seed --skip-ai         # Без Gemini (только Mueller dict для переводов)
python -m backend.seed --force           # Перезаписать существующие
python -m backend.seed --enrich          # Дообогатить: AI-переводы + AI-контексты для слов без данных
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

Расчёт: 10000 слов ÷ 100 слов на запрос = 100 запросов к Gemini. Бесплатный лимит 250 RPD — укладывается за 1 день с запасом.

---

## 14. Onboarding (первый запуск)

При первом открытии приложения (нет данных в БД) — показать минимальный onboarding:

### Экран 1: "Добро пожаловать в WordForge"
- Краткое описание (2 предложения): "Изучай английские слова через активную практику. Система сама подберёт что учить и когда повторять."
- Кнопка "Начать" →

### Экран 2: Начальный уровень
- "Какой у тебя уровень английского?"
- 4 кнопки: "Нулевой (A0)" / "Начальный (A1)" / "Базовый (A2)" / "Средний (B1+)"
- По выбору — устанавливается starting_tier в настройках:
  - A0 → Tier 1 (слова 1-300)
  - A1 → Tier 2 (слова 301-500, Tier 1 разблокирован)
  - A2 → Tier 4 (слова 1001-1500, Tiers 1-3 разблокированы)
  - B1+ → Tier 6 (слова 2501-3500, Tiers 1-5 разблокированы)

### Экран 3: Дневная цель
- "Сколько времени в день готов уделять?"
- 3 кнопки: "5 минут" / "15 минут" / "30 минут"
- Устанавливает session_duration_minutes и daily_new_words:
  - 5 мин → 5 новых слов, сессия 5 мин
  - 15 мин → 10 новых слов, сессия 15 мин
  - 30 мин → 20 новых слов, сессия 30 мин

### Экран 4: Gemini API (опционально)
- "Для продвинутых упражнений нужен бесплатный ключ Gemini API"
- Инструкция: "1. Зайди на aistudio.google.com → 2. Get API key → 3. Вставь сюда"
- Input для ключа + кнопка "Проверить"
- Кнопка "Пропустить (настрою позже)" — Level 6 будет работать без AI (деградация)

→ После onboarding — сразу Dashboard с кнопкой "Начать первую тренировку"

**Важно:** Onboarding = максимум 4 экрана, каждый с одним действием. Никаких длинных туториалов — ISTJ хочет сразу к делу.

---

## 15. Keyboard Navigation (горячие клавиши)

Полная навигация с клавиатуры — для ISTJ это критично: предсказуемые, быстрые действия.

### 15.1 Глобальные

```
Ctrl+T          → Начать тренировку (/train)
Ctrl+D          → Dashboard (/)
Ctrl+W          → Мои слова (/words)
Ctrl+S          → Статистика (/stats)
Ctrl+,          → Настройки (/settings)
Escape          → Выйти из тренировки / закрыть модал
```

### 15.2 В тренировке

```
1, 2, 3, 4      → Выбрать вариант ответа (Level 2, 4)
Enter            → Подтвердить ввод / "Got it" (Level 1) / Следующее упражнение
Space            → Прослушать слово (TTS)
Tab              → Показать подсказку (Level 3)
Backspace        → Убрать последнее слово из конструктора (Level 5)
Escape           → Завершить сессию (с подтверждением)
```

### 15.3 После ответа (ручная оценка)

```
1 = Again (не помню)
2 = Hard (трудно)
3 = Good (нормально)
4 = Easy (легко)
```

### 15.4 Индикация

В правом нижнем углу экрана тренировки — полупрозрачная подсказка клавиш для текущего типа упражнения. Исчезает после 5 сессий (пользователь уже запомнил).

---

## 15A. Дневная цель и мотивация

### 15A.1 Дневная цель

На Dashboard — круговой прогресс-индикатор дневной цели:

```
Тип цели (настраивается):
- "Слова": повторить/выучить N слов (default 20)
- "Минуты": потратить N минут на тренировку (default 10)
- "Упражнения": выполнить N упражнений (default 30)
```

Визуально: кольцо-прогресс (indigo) + число "14/20 слов" по центру. При выполнении — кольцо заполняется + мягкая анимация "completed".

### 15A.2 Streak (серия дней)

- Считается автоматически: если сегодня выполнена хотя бы 1 тренировка → streak +1
- Отображение: на Dashboard рядом с целью — "12 дней подряд"
- Иконка: пламя (Lucide `Flame`) monochrome, не цветная
- Если пропущен день — streak сбрасывается. Без драмы, просто число обнуляется
- Максимальный streak за всё время тоже показывается: "Рекорд: 34 дня"

### 15A.3 Мотивационные сообщения (для Neuroticism 55%)

Подаются мягко, без восклицательных знаков и без давления:

```
После завершения сессии:
- "Ты повторил 23 слова. 3 новых слова добавлены."
- "Точность сегодня: 87%. На 4% лучше чем вчера."
- "Ещё 6 слов — и дневная цель выполнена."

При длинном streak:
- "15 дней подряд. Стабильность работает."

После перерыва (не давить!):
- "С возвращением. У тебя 12 слов ждут повторения."
- НЕ: "Ты пропустил 3 дня! Твой прогресс под угрозой!"
```

---

## 15B. Комфорт тренировки (UX для ISTJ)

### 15B.1 Предсказуемость сессии

Перед началом тренировки — показать план:

```
┌─────────────────────────────────────┐
│  Тренировка · ~15 мин               │
│                                     │
│  Повторения:  18 слов               │
│  Новые слова: 5 слов                │
│  ─────────────────────              │
│  Итого:       23 упражнения         │
│                                     │
│  [Начать]   [Только повторения]     │
└─────────────────────────────────────┘
```

Пользователь видит ЧТО его ждёт до начала. Может выбрать "Только повторения" (без новых слов) если мало времени.

### 15B.2 Прогресс внутри сессии

Сверху экрана:
- Progress bar: заполняется по мере прохождения упражнений
- Текст: "7 / 23" (текущее / всего)
- Мини-статистика: "✓ 6  ✗ 1" (правильно / ошибки в текущей сессии)

### 15B.3 Пауза и выход

- Кнопка паузы (или Escape) → модал: "Приостановить тренировку?"
  - "Продолжить" / "Завершить и сохранить" / "Отменить (не сохранять)"
- При "Завершить и сохранить" — все уже данные ответы записываются, непройденные упражнения остаются в очереди

### 15B.4 Итоги сессии

После завершения — экран-саммари (если включён в настройках):

```
┌─────────────────────────────────────┐
│  Сессия завершена                    │
│                                     │
│  Время:        12 мин 34 сек        │
│  Слов повторено: 18                  │
│  Новых слов:     5                   │
│  Точность:       87%                │
│  Streak:         12 дней            │
│                                     │
│  Дневная цель:  ████████░░ 80%      │
│                                     │
│  [На главную]  [Ещё тренировка]     │
└─────────────────────────────────────┘
```

### 15B.5 Фидбек при ответах (для Neuroticism 55%)

Правильный ответ:
- Бордер карточки → #22C55E (зелёный) на 400ms
- Мягкий fade-переход к следующему

Неправильный ответ:
- Бордер карточки → #EF4444 (красный) на 300ms
- Показать правильный ответ: "Правильно: solve" (без "ОШИБКА!")
- Показать контекст/пример для закрепления
- Пауза 1500ms → следующее упражнение
- Слово будет показано снова через 2-3 упражнения в этой же сессии (re-queue)

Частичный ответ (Levenshtein ≤ 1):
- Бордер → #F59E0B (жёлтый)
- "Почти! Правильно: solve" (мягкий тон)

### 15B.6 Re-queue ошибочных слов

Если пользователь ответил "Again" на слово — это слово добавляется обратно в очередь текущей сессии (через 3-5 других упражнений). Это даёт шанс закрепить прямо сейчас, не ждать следующего дня.

---

## 15C. Расширенная страница Dashboard

### Layout

```
┌──────────────────────────────────────────────────┐
│  Sidebar                                          │
│  ────────                                         │
│  WordForge                                        │
│                                                   │
│  ▸ Dashboard         ← active                     │
│  ▸ Тренировка                                     │
│  ▸ Мои слова                                      │
│  ▸ Статистика                                     │
│  ▸ Настройки                                      │
│                                                   │
│  ─── внизу ───                                    │
│  Streak: 12 дней                                  │
│  Слов изучено: 347                                │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  Main Area                                        │
│                                                   │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐            │
│  │ Дневная │ │ Сегодня │ │ Streak   │            │
│  │ цель    │ │ 14 слов │ │ 12 дней  │            │
│  │ ◐ 70%   │ │ 91% точ │ │ рек: 34  │            │
│  └─────────┘ └─────────┘ └──────────┘            │
│                                                   │
│  ┌──────────────────────────────────────┐         │
│  │  [■■■ Начать тренировку · 15 мин ■■■] │       │
│  │  [Быстрая · 5 мин]  [Только повтор.] │       │
│  └──────────────────────────────────────┘         │
│                                                   │
│  ┌─── Покрытие речи ────────────────────┐         │
│  │  ████████████░░░░░░  74%              │         │
│  │  347 слов → покрываешь 74% речи       │         │
│  │  До 80%: ещё 153 слова                │         │
│  └──────────────────────────────────────┘         │
│                                                   │
│  ┌─── Текущий ярус ─────────────────────┐         │
│  │  Tier 3 · A2 Foundation               │         │
│  │  ████████████░░  72% (216/300 слов)   │         │
│  │  До разблокировки Tier 4: 6 слов      │         │
│  └──────────────────────────────────────┘         │
│                                                   │
│  ┌─── Распределение по уровням ─────────┐         │
│  │  L1 ██░░░░  12                        │         │
│  │  L2 ████░░  34                        │         │
│  │  L3 ██████  67                        │         │
│  │  L4 ████░░  45                        │         │
│  │  L5 ███░░░  28                        │         │
│  │  L6 ██░░░░  15                        │         │
│  │  L7 █░░░░░  8                         │         │
│  └──────────────────────────────────────┘         │
│                                                   │
│  ┌─── Активность за неделю (bar chart) ─┐         │
│  │  Пн  Вт  Ср  Чт  Пт  Сб  Вс         │         │
│  │  ██  ██  ██  ░░  ██  ██  ░░           │         │
│  └──────────────────────────────────────┘         │
└──────────────────────────────────────────────────┘
```

### Кнопки тренировки (ключевая область)

3 варианта запуска:
1. **"Начать тренировку · 15 мин"** — полная сессия (повторения + новые), крупная кнопка indigo-600
2. **"Быстрая · 5 мин"** — только overdue повторения, маленькая кнопка secondary
3. **"Только повторения"** — без новых слов, маленькая кнопка secondary

При наведении на каждую кнопку — tooltip показывает: "18 повторений + 5 новых слов" / "12 повторений" / "18 повторений, без новых"

---

## 16. Порядок разработки (фазы для Claude Code)

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
10. Запуск seed: `python -m backend.seed --count 10000`
11. Frontend: страница Words (таблица, фильтры, поиск)
12. Frontend: WordDetail (карточка слова)

### Фаза 3: Ядро обучения
12. Module learning: models, schemas, repository, service (FSRS integration), routes
13. Module training: models, schemas, repository, service (session generator), routes
14. Workflow: start_session, submit_answer
15. Frontend: страница Train (все 7 типов упражнений)
16. Горячие клавиши (1-4, Enter, Esc)

### Фаза 4: AI и продвинутые упражнения
17. Module ai: service (Gemini), prompts, routes
18. Level 5: Sentence Builder с drag-and-drop
19. Level 6: Free Production + AI проверка
20. Level 7: Listening + Web Speech API TTS

### Фаза 5: Аналитика и Dashboard
21. Module stats: models, schemas, repository, service, routes
22. Frontend: Dashboard (полный layout с целью, streak, покрытием, ярусом)
23. Frontend: Stats (графики, heatmap, покрытие речи)
24. Дневная цель: модель + UI (кольцо-прогресс)
25. Streak система

### Фаза 6: Настройки и Onboarding
26. Module settings: полная модель (все 30+ настроек), routes
27. Frontend: Settings (все секции)
28. Onboarding (4 экрана при первом запуске)
29. Экспорт/импорт прогресса

### Фаза 7: Полировка
30. Keyboard navigation (глобальные + в тренировке)
31. Анимации и переходы
32. Адаптивность (responsive)
33. Error handling, loading states, empty states
34. Мотивационные сообщения и мягкий фидбек
35. Tooltips для кнопок тренировки

---

## 17. Важные технические примечания

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
16. **Seed**: Команда `python -m backend.seed` — автоматическое заполнение 10000+ слов из open-source источников.

---

## 18. Environment Variables (.env)

```env
# Database
DATABASE_URL=sqlite:///data/wordforge.db

# AI
GEMINI_API_KEY=your-gemini-key      # Получить на aistudio.google.com

# Security (optional for localhost)
API_KEY=your-optional-api-key

# App
CORS_ORIGINS=http://localhost:5173
DEBUG=true
```

---

## 19. Запуск проекта

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm    # Модель для POS tagging
alembic upgrade head
python -m seed                             # Автозаполнение словаря (10000+ слов, ~5-10 мин)
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
