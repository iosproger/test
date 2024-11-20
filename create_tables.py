from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Base

DATABASE_URL = "sqlite:///./test.db"  # Use your database URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)
