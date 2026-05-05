from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    '''Base class for all SQLAlchemy ORM models.'''
    pass


def get_db() -> Generator[Session, None, None]:
    '''FastAPI dependency that provides a database session for one request.'''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
