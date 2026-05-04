# Configuring the database and managing sessions using SQLAlchemy with SQLite.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./tasks.db"

# Creating the SQLAlchemy engine with SQLite
# Setting check_same_thread to False since FastAPI runs across multiple threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Providing a database session per request and closing it automatically when done
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
