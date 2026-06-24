from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# SQLite needs special connect_args; MySQL needs pool_pre_ping
_is_sqlite = settings.database_url.startswith("sqlite")

_connect_args: dict = {}
if _is_sqlite:
    _connect_args["check_same_thread"] = False
    # Ensure the SQLite directory exists (Render persistence)
    _db_path = settings.database_url.replace("sqlite:///", "")
    if not _db_path.startswith("/"):
        _db_path = str(Path(__file__).resolve().parent.parent.parent / _db_path)
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=not _is_sqlite,
)

# Enable SQLite foreign key support
if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
