from datetime import datetime, date, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def today() -> date:
    return datetime.now(timezone.utc).date()
