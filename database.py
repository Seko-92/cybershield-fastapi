from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os # Crucial for reading the environment variable

# 1. Get the Connection URL from Environment Variables
# This is the string set in the Railway dashboard (e.g., postgresql://postgres:***@postgres.railway.internal:5432/railway)
SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL')

# 2. Engine Creation for PostgreSQL
# We check if the URL is set before trying to create the engine.
if SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        # Recommended for cloud connections to check health before use
        pool_pre_ping=True
    )
else:
    # If the URL is missing, raise a clear error immediately
    raise ValueError("DATABASE_URL environment variable is not set! Check Railway variables.")

# 3. Session and Base Configuration
# Standard configuration for SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 4. Database Session Dependency
def get_db() -> Generator:
    """
    Dependency function that yields a new database session for FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()