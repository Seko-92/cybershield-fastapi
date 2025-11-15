from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict

# Local Imports: **FIXED** to use absolute imports
import models
import database


# --- 1. Pydantic Schemas (Data Validation) ---

# Schema for the data received when registering an individual user
class IndividualRegister(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    mobile: str


# Schema for the data received when registering an enterprise user
class EnterpriseRegister(BaseModel):
    email: EmailStr
    company_name: str
    company_website: str
    phone: str


# Schema for the data received on the registration form
class UserCreate(BaseModel):
    scope: str  # 'individual' or 'enterprise'
    email: EmailStr
    # Optional fields to accommodate both scopes
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    phone: Optional[str] = None


# Schema for login request
class UserLogin(BaseModel):
    email: EmailStr


# Base Schema for a User Response (what the API sends back)
class User(BaseModel):
    id: int
    email: EmailStr
    scope: str

    class Config:
        orm_mode = True  # Enables reading data directly from SQLAlchemy model


# Schema for scan requests
class ScanRequest(BaseModel):
    url: Optional[str] = None
    user_id: int


class AiQueryRequest(BaseModel):
    query: str
    user_id: int


class EmailCheckRequest(BaseModel):
    email: EmailStr
    user_id: int


# Schema for reports (response)
class ScanReport(BaseModel):
    id: int
    user_id: int
    scan_type: str
    target: str
    status: str
    overall_summary: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        orm_mode = True


# --- 2. FastAPI Initialization and Middleware ---

app = FastAPI(title="CyberShield Backend API")

# Configure CORS to allow your front-end (running on http://127.0.0.1:8000)
# to make requests to the backend (which we will run on a different port, e.g., 8080).
origins = [
    "http://127.0.0.1:8000",  # The likely address of your index.html file
    "http://localhost:8000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 3. Database Startup Event ---

# This function runs once when the application starts, creating the tables
# defined in models.py if they don't already exist.
@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=database.engine)
    print("Database tables created/checked successfully.")


# --- 4. Health Check / Root Endpoint ---

@app.get("/")
def read_root():
    return {"message": "CyberShield API is running."}


# --- 5. User Registration Endpoint ---

@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(database.get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create the user object based on the scope
    if user.scope == "individual":
        db_user = models.User(
            email=user.email,
            scope=user.scope,
            first_name=user.first_name,
            last_name=user.last_name,
            mobile=user.mobile,
        )
    elif user.scope == "enterprise":
        db_user = models.User(
            email=user.email,
            scope=user.scope,
            company_name=user.company_name,
            company_website=user.company_website,
            phone=user.phone,
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid scope type")

    # Save to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- 6. User Login Endpoint ---

@app.post("/login", response_model=User)
def login_user(user: UserLogin, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


# --- 7. Scan Endpoints (Stubs) ---
# These endpoints return dummy data for now, matching the JSON structure
# the frontend expects, which is essential for testing the user dashboard flow.

@app.post("/scan")
def url_scan(request: ScanRequest, db: Session = Depends(database.get_db)):
    # Simulating a scan result
    if request.url and "malicious" in request.url.lower():
        status_text = "DANGER"
        summary = "DANGER: High threat detected by VirusTotal."

    elif request.url and "warning" in request.url.lower():
        status_text = "WARNING"
        summary = "WARNING: Suspicious activity flagged by Safe Browsing."
    else:
        status_text = "CLEAN"
        summary = "CLEAN: No immediate threats detected."

    mock_details = {
        "virustotal": {
            "status": "COMPLETED",
            "malicious_count": 5 if status_text == "DANGER" else 0,
            "harmless_count": 80,
            "results_url": "https://www.virustotal.com/gui/url/mocked/report"
        },
        "google_safe_browsing": {
            "status": "UNSAFE" if status_text == "WARNING" else "SAFE",
            "message": "Blocked for phishing." if status_text == "WARNING" else "No issues found."
        },
        "geoip": {
            "status": "success",
            "city": "Ashburn",
            "country": "US",
            "ip_address": "35.168.1.1",
            "organization": "Amazon Technologies Inc."
        }
    }

    # Save report stub
    report = models.ScanReport(
        user_id=request.user_id,
        scan_type="url",
        target=request.url or "N/A",
        status=status_text,
        overall_summary=summary,
        details=mock_details
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "status": "success",
        "url": request.url,
        "overall_summary": summary,
        "details": mock_details
    }


# IMPORTANT: Changed this to handle the file upload correctly from the frontend's FormData
@app.post("/scan-file")
async def file_scan(user_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    # In a real app, you would process the 'file' content here.
    filename = file.filename or "uploaded_file"

    status_text = "CLEAN"
    summary = "CLEAN: Mocked file scan passed successfully."

    # Simulate a danger state if the filename suggests it
    if filename.lower().endswith(('.exe', '.bat')):
        status_text = "DANGER"
        summary = "DANGER: High-risk file type detected. Mocked result."

    mock_details = {
        "virustotal": {
            "status": "COMPLETED",
            "malicious_count": 5 if status_text == "DANGER" else 0,
            "harmless_count": 75,
            "results_url": "https://www.virustotal.com/gui/file/mocked/report"
        }
    }

    report = models.ScanReport(
        user_id=user_id,
        scan_type="file",
        target=filename,
        status=status_text,
        overall_summary=summary,
        details=mock_details
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "status": "success",
        "filename": filename,
        "overall_summary": summary,
        "details": mock_details
    }


@app.post("/ai-query")
def ai_query(request: AiQueryRequest, db: Session = Depends(database.get_db)):
    summary = "SUCCESS: AI provided a detailed response."
    mock_response = (
        "The latest ransomware threats often involve double-extortion tactics, "
        "where data is not only encrypted but also stolen. Common delivery "
        "mechanisms include phishing emails and exploiting unpatched RDP ports. "
        "Always keep systems patched and use multi-factor authentication."
    )
    mock_sources = [
        {"title": "CISA Alert on Ransomware", "uri": "https://www.cisa.gov"},
        {"title": "MITRE ATT&CK Framework", "uri": "https://attack.mitre.org/"}
    ]

    report = models.ScanReport(
        user_id=request.user_id,
        scan_type="ai",
        target=request.query[:100],  # Store first 100 chars of query
        status="SUCCESS",
        overall_summary=summary,
        details={"ai_response": mock_response, "sources": mock_sources}
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "ai_response": mock_response,
        "sources": mock_sources
    }


@app.post("/check-email")
def check_email(request: EmailCheckRequest, db: Session = Depends(database.get_db)):
    email = request.email.lower()

    if "breached" in email:
        status_text = "DANGER"
        summary = "DANGER: Email found in multiple major data breaches."
        breaches = {
            "status": "DANGER",
            "breaches_found": 3,
            "breach_list": [
                {"name": "2020 Data Dump", "date": "2020-05-15", "data": "Passwords, usernames, IPs"},
                {"name": "Cloud Leak", "date": "2022-01-01", "data": "Email addresses, names"},
            ]
        }
    else:
        status_text = "CLEAN"
        summary = "CLEAN: Email not found in known public breaches."
        breaches = {
            "status": "CLEAN",
            "breaches_found": 0,
            "breach_list": [],
            "message": "Excellent! Your email was not found in any major public data breach."
        }

    report = models.ScanReport(
        user_id=request.user_id,
        scan_type="email",
        target=email,
        status=status_text,
        overall_summary=summary,
        details={"breach_check": breaches}
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "email": email,
        "overall_summary": summary,
        "details": {"breach_check": breaches}
    }


# --- 8. Admin Endpoints (Stubbed for now) ---
# We will fully implement these later, but the structure is here.

@app.get("/admin/users", response_model=List[User])
def get_admin_users(admin_key: str, db: Session = Depends(database.get_db)):
    if admin_key != "cybershield_admin_2024":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    return db.query(models.User).all()


@app.get("/admin/reports", response_model=List[ScanReport])
def get_all_reports(admin_key: str, db: Session = Depends(database.get_db)):
    if admin_key != "cybershield_admin_2024":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    return db.query(models.ScanReport).all()


@app.get("/admin/reports/user/{user_id}", response_model=List[ScanReport])
def get_user_reports(user_id: int, admin_key: str, db: Session = Depends(database.get_db)):
    if admin_key != "cybershield_admin_2024":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    reports = db.query(models.ScanReport).filter(models.ScanReport.user_id == user_id).all()
    if not reports:
        # Returning an empty list is generally better than 404 for a report list
        return []
    return reports


@app.delete("/admin/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, admin_key: str, db: Session = Depends(database.get_db)):
    if admin_key != "cybershield_admin_2024":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete associated reports first (optional, depending on database constraints, but safe)
    db.query(models.ScanReport).filter(models.ScanReport.user_id == user_id).delete(synchronize_session=False)

    # Delete the user
    db.delete(user)
    db.commit()
    return