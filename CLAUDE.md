# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WordForge is a self-hosted English vocabulary learning application using FSRS spaced repetition with 7 progressive mastery levels. Single-user, dark theme, supports 10,000+ words with AI-powered context generation.

## Development Commands

### Backend (Python/FastAPI)
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Seed database (first time, or to add more words)
python -m backend.seed --count 500

# Run development server (port 8000)
uvicorn backend.main:app --reload --port 8000

# Apply database migrations
cd backend && alembic upgrade head
```

### Frontend (React/TypeScript/Vite)
```bash
cd frontend

# Install dependencies
npm install

# Development server (port 5173, proxies /api to localhost:8001)
npm run dev

# Build for production
npm run build
```

**Note:** The Vite config proxies `/api` to port 8001, but the backend typically runs on 8000. Adjust as needed.

## Architecture

### Backend Structure (`backend/`)
```
backend/
├── core/               # Database, config, base exceptions
├── modules/            # Feature modules (modular monolith pattern)
│   ├── words/          # Dictionary management (Word, WordContext models)
│   ├── learning/       # User progress (UserWord, Review, FSRS tracking)
│   ├── training/       # Session orchestration, exercise generation
│   ├── stats/          # Dashboard statistics
│   ├── settings/       # User preferences (43 settings)
│   └── ai/             # Google Gemini integration
├── shared/             # Utilities (text normalization, date handling)
├── seed/               # Database seeding from word frequency lists
├── workflows/          # Orchestration layer for complex operations
└── alembic/            # Database migrations
```

Each module follows: `models.py` → `repository.py` → `service.py` → `schemas.py` → `routes.py`

### Frontend Structure (`frontend/src/`)
```
src/
├── api/          # API client layer (apiFetch wrapper)
├── components/   # Reusable components (ui/, training/, stats/)
├── pages/        # Route pages (Dashboard, Train, Words, Settings, Stats)
├── stores/       # Zustand state (trainingStore for session management)
├── hooks/        # Custom hooks (useKeyboard, useTTS, useTimer)
├── types/        # TypeScript interfaces (Exercise, UserWord, Settings)
└── lib/          # Utilities
```

### Key Data Flow

**Training Session:**
1. `POST /api/training/session` creates session with exercises
2. Backend selects words: overdue → learning/relearning → new (respects daily limits)
3. Generates exercises based on mastery level (1-7 = exercise types 1-7)
4. New words get multiple exercises (types 1,2,3,4)

**Answer Processing:**
1. `POST /api/training/session/{id}/answer` evaluates answer
2. Levenshtein distance ≤1 accepted as typo (still correct)
3. FSRS rating calculated (1=Again, 2=Hard, 3=Good, 4=Easy)
4. Updates mastery level if consecutive_correct threshold reached

### Database

SQLite at `data/wordforge.db`. Key tables:
- `words`, `word_contexts` - Dictionary
- `user_words`, `reviews` - Learning progress with FSRS fields
- `training_sessions`, `daily_training_sessions` - Session tracking
- `phrasal_verbs`, `irregular_verbs` - Special word types (each with own progress tables)
- `user_settings` - 43 user preferences

### API Routes

Main endpoints:
- `/api/words` - Dictionary CRUD
- `/api/learning/due` - Words due for review
- `/api/training/session` - Create/manage training sessions
- `/api/training/session/{id}/answer` - Submit answers
- `/api/training/daily-status` - Daily completion status per category
- `/api/stats/dashboard` - Statistics data
- `/api/settings` - User preferences
- `/api/ai/check-sentence` - AI sentence validation

## Key Implementation Details

**Exercise Types (mastery levels 1-7):**
1. Introduction - Show word, translation, context
2. Recognition - Multiple choice (select translation)
3. Recall - Type the translation
4. Context - Gap fill with options
5. Sentence Builder - Arrange scrambled words
6. Free Production - Write sentence using word
7. Listening - Hear word, type it

**FSRS Integration:**
- Uses `fsrs` Python library (v6)
- Parameters stored in UserWord: stability, difficulty, elapsed_days, scheduled_days, state
- next_review_at calculated after each review

**AI Features (optional, requires GEMINI_API_KEY):**
- Context generation for exercises
- Word enrichment (collocations, phrasal verbs, usage notes)
- Sentence validation for free production
- Function words get special treatment (usage rules, comparisons, common errors)

**Function Words:**
Words with `word_category = "function"` or `"preposition"` (like "the", "a", "to") get rich context instead of translations. Check `context_service.py` for the special handling.

## Configuration

Environment variables (in `.env` or system):
```
DATABASE_URL=sqlite:///data/wordforge.db
GEMINI_API_KEY=sk-xxx  # Optional
CORS_ORIGINS=http://localhost:5173
DEBUG=False
```

## Migrations

After modifying models, create/run migrations:
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

Or use standalone scripts like `migrate_002.py` for production deployment.
