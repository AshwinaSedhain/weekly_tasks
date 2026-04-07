# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Replace YOUR_PASSWORD with your PostgreSQL password
DATABASE_URL = "postgresql+psycopg2://postgres:0306@localhost:5432/expense_tracker"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Create tables if they don't exist
Base.metadata.create_all(engine)
