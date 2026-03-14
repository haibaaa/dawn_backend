from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Supabase Postgres engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
Base = declarative_base()


# Dependency to get a DB session in your routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
