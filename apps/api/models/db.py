import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime

DATABASE_URL = os.getenv("DATABASE_URL","postgresql+psycopg://postgres:postgres@localhost:5432/remedy")

class Base(DeclarativeBase):
    pass

def get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Minimal mixin
class TimeID(Base):
    __abstract__ = True
    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
