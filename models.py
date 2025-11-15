from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


# --- User Model ---
class User(Base):
    """
    Represents a user in the CyberShield platform.
    Handles both individual and enterprise registration details.
    """
    __tablename__ = "users"

    # Core fields
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    scope = Column(String, default="individual", nullable=False)  # 'individual' or 'enterprise'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Individual fields (can be null if scope is 'enterprise')
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    mobile = Column(String, nullable=True)

    # Enterprise fields (can be null if scope is 'individual')
    company_name = Column(String, nullable=True)
    company_website = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    # Relationship to ScanReport
    reports = relationship("ScanReport", back_populates="owner")


# --- Scan Report Model ---
class ScanReport(Base):
    """
    Stores the details and results of a security scan (URL, file, or AI query).
    """
    __tablename__ = "scan_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Scan details
    scan_type = Column(String, nullable=False)  # 'url', 'file', 'ai', 'email'
    target = Column(String, nullable=False)  # The URL, filename, or AI query used for the scan

    # Result summary
    status = Column(String, nullable=False)  # e.g., 'CLEAN', 'DANGER', 'WARNING', 'SUCCESS'
    overall_summary = Column(String, nullable=False)

    # Full detailed result (stored as JSON)
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to User
    owner = relationship("User", back_populates="reports")