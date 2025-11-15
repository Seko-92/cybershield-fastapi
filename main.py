# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from sqlalchemy.orm import Session
import logging
import traceback
import time
from fastapi.staticfiles import StaticFiles  # <-- NEW IMPORT

# --- Database Imports (Ensure these files are in your repo) ---
from database import Base, engine, get_db
import models

# --- Core API Configuration ---

app = FastAPI(
    title="CyberShield API",
    description="Backend service for the CyberShield application.",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# --- Database Initialization Logic (CRITICAL for startup) ---
# This ensures tables are created when the application starts
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
                time.sleep(2) # Wait 2 seconds before retrying
            else:
                logging.error("Failed to connect to the database after multiple retries.")
                raise # Re-raise exception if all retries fail

# ----------------------------------------------------
# --- YOUR API ENDPOINTS (MUST GO BEFORE app.mount) ---
# ----------------------------------------------------

# Health Check / Status Route
@app.get("/api/status")
def get_api_status():
    return {"message": "CyberShield API is running and ready to serve data."}

# Example API Route - REPLACE WITH YOUR ACTUAL ROUTES
# @app.get("/api/users", response_model=List[schemas.User])
# def read_users(db: Session = Depends(get_db)):
#     # Logic to fetch users from database
#     return db_users

# --------------------------------------------------
# --- SERVE STATIC FRONT-END (MUST BE THE LAST ROUTE) ---
# --------------------------------------------------

# This mounts the current directory (".") as the static files location.
# Any request that doesn't match an API route above will be checked
# against the files in the root folder.
# 'html=True' ensures that a request to "/" automatically serves index.html.
app.mount(
    "/",
    StaticFiles(directory=".", html=True),
    name="static"
)