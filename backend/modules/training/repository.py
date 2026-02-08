from sqlalchemy.orm import Session

from backend.shared.date_utils import utc_now
from .models import TrainingSession
from .exceptions import SessionNotFoundError


def create_session(db: Session) -> TrainingSession:
    session = TrainingSession()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: int) -> TrainingSession:
    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
    ).first()
    if not session:
        raise SessionNotFoundError(session_id)
    return session


def update_session(db: Session, session_id: int, data: dict) -> TrainingSession:
    session = get_session(db, session_id)
    for key, value in data.items():
        if hasattr(session, key):
            setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session


def end_session(db: Session, session_id: int) -> TrainingSession:
    session = get_session(db, session_id)
    now = utc_now()
    session.ended_at = now
    if session.started_at:
        delta = now - session.started_at
        session.duration_seconds = int(delta.total_seconds())
    db.commit()
    db.refresh(session)
    return session


def get_recent_sessions(db: Session, limit: int = 10) -> list[TrainingSession]:
    return (
        db.query(TrainingSession)
        .order_by(TrainingSession.started_at.desc())
        .limit(limit)
        .all()
    )
