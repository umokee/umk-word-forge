from sqlalchemy.orm import Session

from .schemas import SettingsResponse, SettingsUpdate
from . import repository


def get_settings(db: Session) -> SettingsResponse:
    """Retrieve current user settings."""
    row = repository.get_settings(db)
    return SettingsResponse.model_validate(row)


def update_settings(db: Session, data: SettingsUpdate) -> SettingsResponse:
    """Update user settings with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    row = repository.update_settings(db, update_data)
    return SettingsResponse.model_validate(row)
