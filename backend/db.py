import os
from sqlmodel import create_engine, Session

# PostgreSQL connection string
# postgresql+psycopg2://postgres:root@localhost:5432/emotion_playlist

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(
    DATABASE_URL,
    echo=False,          # set True only when debugging SQL
    pool_pre_ping=True   # avoids stale connections
)

def get_session():
    """
    Returns a new SQLModel session.
    Caller is responsible for closing it.
    """
    return Session(engine)
