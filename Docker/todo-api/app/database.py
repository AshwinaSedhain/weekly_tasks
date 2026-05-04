import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# reading the database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todos.db")

# creating the database engine
engine = create_engine(
    DATABASE_URL,
    # connect_args is needed only for SQLite to allow multi-threading
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# creating a session factory for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# providing the base class for all models
Base = declarative_base()
