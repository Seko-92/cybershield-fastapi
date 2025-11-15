# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from sqlalchemy.orm import Session
import logging
import traceback
import time  # CRITICAL: Imported for the retry delay

# --- Database Imports ---
from database import Base, engine, get_db
# Ensure your models.py is also present in your directory
import models

# --- Core API Configuration ---

app = FastAPI()

# Configure logging to ensure output is visible in Railway logs
logging.basicConfig(level=logging.INFO)


# --- Pydantic Schemas (Place your actual schemas here) ---

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None

    # Example V1 Config (Causes non-fatal warnings)
    class Config:
        orm_mode = True


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


class ScanReport(BaseModel):
    # Example scan report fields
    url: str
    risk_score: int
    details: str


# --- Database Initialization (The critical fix) ---

@app.on_event("startup")
def startup_event():
    """
    Creates database tables if they don't exist, using a retry loop
    to handle transient database connection failures during cloud startup.
    """
    logging.info("Starting up application...")

    # Retry Configuration
    MAX_RETRIES = 5
    RETRY_DELAY = 5  # seconds

    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"Attempting connection to PostgreSQL (Attempt {attempt + 1}/{MAX_RETRIES})...")

            # CRITICAL LINE: Attempt to create tables (this is where the crash was occurring)
            Base.metadata.create_all(bind=engine)

            logging.info("Database tables created successfully! Application is ready.")
            return  # Exit the function successfully if connection is made

        except Exception as e:
            logging.error(f"DATABASE CONNECTION FAILED: {e}")

            if attempt < MAX_RETRIES - 1:
                logging.warning(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                # If all retries fail, print the full error and crash
                logging.error("=" * 60)
                logging.error("!!! FATAL DATABASE CONNECTION ERROR AFTER ALL RETRIES !!!")
                logging.error(f"Last Error: {e}")
                logging.error("--- Full Traceback ---")
                logging.error(traceback.format_exc())
                logging.error("=" * 60)

                # Re-raise the exception to ensure the service fails visibly
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Database connection failed during startup: {e}"
                )


# --- API Endpoints (Include your existing routes here) ---

@app.get("/")
def read_root():
    return {"message": "CyberShield API is running."}


@app.post("/register")
def register_user(user_data: UserCreateIndividual, db: Session = Depends(get_db)):
    # Your registration logic goes here
    return {"message": f"User {user_data.email} registration endpoint hit."}

# Add all your other routes (login, scan, get_report, etc.) here...
# Example:
# @app.get("/users/{user_id}", response_model=User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     # Logic to fetch user from DB
#     return {"id": user_id, "email": "test@example.com", "is_active": True}