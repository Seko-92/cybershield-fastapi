from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os # Import os for potential environment variable usage

# 1. PostgreSQL Connection URL
# We hardcode the URL here for simplicity, but in production,
# it's best practice to use an environment variable (os.getenv('DATABASE_URL')).
SQLALCHEMY_DATABASE_URL = "postgresql://cybershield_user:focnMNh0UV4V0g1NnVuDbg3lVhYi7a0Q@dpg-d4bs0muuk2gs73dfqa3g-a.oregon-postgres.render.com/cybershield_db_lq1b"

# 2. Engine Creation for PostgreSQL
# We do not need the SQLite-specific 'connect_args={"check_same_thread": False}'
# We also don't need to specify 'pool_pre_ping=True' but it can sometimes help with cloud connections.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

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