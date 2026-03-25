from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL connection (Docker database)
DATABASE_URL = "postgresql://medilens:medilens123@localhost:5432/medilens_db"

# Create engine
engine = create_engine(DATABASE_URL)

# Session for database operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()