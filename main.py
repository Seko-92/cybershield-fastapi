# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Union
from sqlalchemy.orm import Session
import logging
import traceback
import time
from fastapi.staticfiles import StaticFiles

# --- Database Imports ---
from database import Base, engine, get_db
import models  # Imports your SQLAlchemy models


# --- Pydantic Schemas (Data Validation) ---

# 1. Base User Schema (used for all user data)
class UserBase(BaseModel):
    email: EmailStr
    scope: str = Field(..., description="Must be 'individual' or 'enterprise'")


# 2. Individual User Registration Schema
class UserRegisterIndividual(UserBase):
    first_name: str
    last_name: str
    mobile: str


# 3. Enterprise User Registration Schema
class UserRegisterEnterprise(UserBase):
    company_name: str
    company_website: str
    phone: str


# Use a Union to accept either registration type (FastAPI/Pydantic automatically validates the 'scope' field)
UserRegister = Union[UserRegisterIndividual, UserRegisterEnterprise]


# 4. User Output Schema (what the API returns after login/registration)
class UserOut(BaseModel):
    id: int
    email: EmailStr
    scope: str

    class Config:
        from_attributes = True


# 5. Login Schema (only requires email)
class UserLogin(BaseModel):
    email: EmailStr


# 6. Scan Input Schema
class ScanInput(BaseModel):
    url: str
    user_id: int


# --- Core API Configuration ---

app = FastAPI(
    title="CyberShield API",
    description="Backend service for the CyberShield application.",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(level=logging.INFO)


# --- Database Initialization Logic (CRITICAL for startup) ---
def create_db_tables():
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting connection to PostgreSQL (Attempt {attempt + 1}/{max_retries})...")
            create_db_tables()
            logging.info("Database tables created successfully! Application is ready.")
            break
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logging.error("Failed to connect to the database after multiple retries.")
                raise


# ----------------------------------------------------
# --- YOUR API ENDPOINTS (MUST GO BEFORE app.mount) ---
# ----------------------------------------------------

# Health Check / Status Route
@app.get("/api/status")
def get_api_status():
    return {"message": "CyberShield API is running and ready to serve data."}


## --- 1. Registration Endpoint ---
@app.post("/api/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Convert Pydantic model to dict for SQLAlchemy model creation
    user_dict = user_data.model_dump(exclude_unset=True)

    # Create the User object
    db_user = models.User(**user_dict)

    # Save to database
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        logging.error(f"Database error during registration: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save user data.")

    return db_user


## --- 2. Login Endpoint ---
@app.post("/api/login", response_model=UserOut)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == login_data.email).first()

    if db_user is None:
        # Note: In a real app, you'd check a password/token too. Here we rely on email lookup.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return db_user


## --- 3. Scan Endpoint ---
@app.post("/api/scan")
def handle_scan(scan_input: ScanInput, db: Session = Depends(get_db)):
    # 1. Basic User Check
    db_user = db.query(models.User).filter(models.User.id == scan_input.user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User ID invalid.")

    # 2. Perform Mock Scan (Replace with actual security API calls)

    # Simple logic to simulate scan results based on the URL text for demonstration
    if "malicious" in scan_input.url.lower() or "phish" in scan_input.url.lower():
        overall_summary = "DANGER: High risk detected."
        status_result = "DANGER"
        vt_malicious = 7
        gsb_status = "UNSAFE"
    elif "test" in scan_input.url.lower() or "example" in scan_input.url.lower():
        overall_summary = "WARNING: Unverified site, proceed with caution."
        status_result = "WARNING"
        vt_malicious = 0
        gsb_status = "SAFE"
    else:
        overall_summary = "CLEAN: No immediate threats detected."
        status_result = "CLEAN"
        vt_malicious = 0
        gsb_status = "SAFE"

    scan_details = {
        "virustotal": {
            "status": "Completed",
            "malicious_count": vt_malicious,
            "harmless_count": 80,
            "results_url": f"https://mock-vt.com/report/{scan_input.url}"
        },
        "google_safe_browsing": {
            "status": gsb_status,
            "message": f"URL check status: {gsb_status}"
        }
    }

    # 3. Save Scan Report
    report = models.ScanReport(
        user_id=scan_input.user_id,
        scan_type="url",
        target=scan_input.url,
        status=status_result,
        overall_summary=overall_summary,
        details=scan_details  # SQLAlchemy's JSON type handles this dict
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    # 4. Return formatted response expected by script.js
    return {
        "url": scan_input.url,
        "overall_summary": overall_summary,
        "details": scan_details
    }


# --------------------------------------------------
# --- SERVE STATIC FRONT-END (MUST BE THE LAST ROUTE) ---
# --------------------------------------------------

app.mount(
    "/",
    StaticFiles(directory=".", html=True),
    name="static"
)