from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass