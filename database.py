from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os # Necessary to read environment variables

# 1. PostgreSQL Connection URL
# CRITICAL FIX: Use the environment variable set in the Railway dashboard.
# Railway automatically populates the DATABASE_URL variable with the correct
# internal connection string (e.g., postgresql://postgres:***@postgres.railway.internal:5432/railway).
# It falls back to None if the variable is not set.
SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL')

# Optional: Add a fallback for local testing if you don't use environment vars locally
# if not SQLALCHEMY_DATABASE_URL:
#     SQLALCHEMY_DATABASE_URL = "sqlite:///./local_test.db"

# 2. Engine Creation for PostgreSQL
# We add pool_pre_ping=True for stability on cloud connections.
if SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True
    )
else:
    # If the URL is missing (e.g., during testing), raise an error
    raise ValueError("DATABASE_URL environment variable is not set!")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 3. Database Session Dependency
def get_db() -> Generator:
    """
    Dependency function that yields a new database session and closes it afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()