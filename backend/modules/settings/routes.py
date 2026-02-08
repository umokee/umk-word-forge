from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from .schemas import SettingsResponse, SettingsUpdate
from . import service

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    return service.get_settings(db)


@router.patch("", response_model=SettingsResponse)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    return service.update_settings(db, data)
