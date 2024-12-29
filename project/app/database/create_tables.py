from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from project.app.models.models import Base

DATABASE_URL = "sqlite:///./sql_app.db"  # Use your database URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)
