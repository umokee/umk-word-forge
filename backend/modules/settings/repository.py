from sqlalchemy.orm import Session

from .models import UserSettings


def get_settings(db: Session) -> UserSettings:
    """Get the singleton settings row, creating it if it doesn't exist."""
    row = db.query(UserSettings).filter(UserSettings.id == 1).first()
    if not row:
        row = UserSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def update_settings(db: Session, data: dict) -> UserSettings:
    """Update settings with the provided key-value pairs."""
    row = get_settings(db)
    for key, value in data.items():
        if value is not None and hasattr(row, key):
            setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row
