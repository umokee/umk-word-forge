# WordForge v2

Self-hosted web application for learning English vocabulary through 7 progressive mastery levels with FSRS spaced repetition.

## Quick Start

### Backend
```bash
pip install -r backend/requirements.txt
python -m backend.seed --count 500    # Populate dictionary
uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

## Architecture

- **Backend**: Python/FastAPI, SQLAlchemy, SQLite, FSRS v5
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **AI**: Google Gemini + Groq fallback for sentence checking

See `WORDFORGE-SPEC-v2(1).md` for the full specification.
