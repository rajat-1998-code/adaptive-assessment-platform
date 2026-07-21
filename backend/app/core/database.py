import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class all ORM models inherit from."""

    pass


def get_db():
    """
    FastAPI dependency that provides a database session per request,
    and guarantees it's closed afterward, even if an error occurs.

    Usage in a route:
        def some_route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Used by the readiness health check to confirm the database
    is actually reachable, not just configured.
    """
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return True
    except Exception as exc:
        logger.error("Database connection check failed: %s", exc)
        return False
