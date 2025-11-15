# main.py

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from sqlalchemy.orm import Session
import logging
import traceback

# --- Database Imports ---
from database import Base, engine, get_db
import models

# --- Core API Configuration ---
# You can ignore the Pydantic/FastAPI warnings related to deprecated V1 syntax for now.
# They are non-fatal.

# NOTE: The dependency functions are omitted here for brevity but should be included 
# if your original file contains them. Assuming they were in your original main.py.

app = FastAPI()

# Configure logging to ensure output is visible in Railway logs
logging.basicConfig(level=logging.INFO)


# --- Pydantic Schemas (Place your actual schemas here) ---
# Ensure you update these to Pydantic V2 syntax later if needed, but they are fine for now.

class UserBase(BaseModel):
    # Add your user fields here
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None

    # Example V1 Config (Causes warnings but works)
    class Config:
        orm_mode = True  # Use from_attributes = True in Pydantic V2


class UserCreateIndividual(UserBase):
    scope: str = "individual"


class UserCreateEnterprise(UserBase):
    scope: str = "enterprise"
    company_name: str
    company_website: str
    phone: str


class User(UserBase):
    id: int
    is_active: bool


# --- Database Initialization (The critical fix) ---

@app.on_event("startup")
def startup_event():
    """
    Creates database tables if they don't exist.
    Includes error handling to catch and log database connection failures.
    """
    logging.info("Starting up application...")

    # CRITICAL: Wrap the database initialization in a try/except block
    try:
        logging.info("Attempting to connect to PostgreSQL and create tables...")

        # This is the line that causes the fatal crash if the connection fails
        Base.metadata.create_all(bind=engine)

        logging.info("Database tables created successfully!")

    except Exception as e:
        # If the connection or creation fails, we print the full error
        logging.error("=" * 60)
        logging.error("!!! FATAL DATABASE CONNECTION ERROR !!!")
        logging.error(f"Error Message: {e}")

        # Print the full stack trace for detailed debugging
        logging.error("--- Full Traceback ---")
        logging.error(traceback.format_exc())
        logging.error("=" * 60)

        # Re-raise the exception to ensure the service fails visibly in Railway
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed during startup: {e}"
        )


# --- API Endpoints (Place your existing routes here) ---

@app.get("/")
def read_root():
    return {"message": "CyberShield API is running."}


@app.post("/register")
def register_user(user_data: UserCreateIndividual, db: Session = Depends(get_db)):
    # Your registration logic goes here
    # Use user_data.email, user_data.first_name, etc.
    return {"message": f"User {user_data.email} registered (DB status will show if successful)"}

# Add all your other routes (login, scan, get_report, etc.) here...logging