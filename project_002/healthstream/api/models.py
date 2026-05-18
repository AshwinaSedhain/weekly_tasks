# ORM models that map to the PostgreSQL warehouse tables.
from datetime import datetime
from sqlalchemy import (
    Column, String, Numeric, Boolean, Integer,
    DateTime, Date, Text, ForeignKey,
)
from database import Base


class Patient(Base):
    __tablename__ = "patients"

    patient_id     = Column(String(36), primary_key=True)
    first_name     = Column(String(100))
    last_name      = Column(String(100))
    date_of_birth  = Column(Date)
    gender         = Column(String(10))
    state          = Column(String(50))
    insurance_type = Column(String(50))
    risk_score     = Column(Numeric(5, 2))
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow)


class Hospital(Base):
    __tablename__ = "hospitals"

    hospital_id       = Column(String(36), primary_key=True)
    hospital_name     = Column(String(200))
    state             = Column(String(50))
    hospital_type     = Column(String(50))
    bed_count         = Column(Integer)
    accreditation     = Column(String(50))
    performance_score = Column(Numeric(5, 2))
    created_at        = Column(DateTime, default=datetime.utcnow)


class Claim(Base):
    __tablename__ = "claims"

    claim_id         = Column(String(36), primary_key=True)
    patient_id       = Column(String(36), ForeignKey("patients.patient_id"))
    hospital_id      = Column(String(36), ForeignKey("hospitals.hospital_id"))
    treatment_code   = Column(String(20))
    diagnosis_code   = Column(String(20))
    claim_amount     = Column(Numeric(12, 2))
    approved_amount  = Column(Numeric(12, 2))
    insurance_status = Column(String(30))
    claim_date       = Column(DateTime)
    processed_date   = Column(DateTime)
    is_fraud         = Column(Boolean, default=False)
    fraud_score      = Column(Numeric(5, 4))
    status           = Column(String(20))
    created_at       = Column(DateTime, default=datetime.utcnow)


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    alert_id     = Column(Integer, primary_key=True, autoincrement=True)
    claim_id     = Column(String(36), ForeignKey("claims.claim_id"))
    patient_id   = Column(String(36), ForeignKey("patients.patient_id"))
    hospital_id  = Column(String(36), ForeignKey("hospitals.hospital_id"))
    fraud_score  = Column(Numeric(5, 4))
    alert_reason = Column(Text)
    alert_type   = Column(String(50))
    severity     = Column(String(20))
    resolved     = Column(Boolean, default=False)
    created_at   = Column(DateTime, default=datetime.utcnow)
    resolved_at  = Column(DateTime)


class AnalyticsSummary(Base):
    __tablename__ = "analytics_summary"

    summary_id       = Column(Integer, primary_key=True, autoincrement=True)
    summary_date     = Column(Date, unique=True)
    total_claims     = Column(Integer)
    total_amount     = Column(Numeric(15, 2))
    approved_claims  = Column(Integer)
    denied_claims    = Column(Integer)
    fraud_detected   = Column(Integer)
    avg_claim_amount = Column(Numeric(12, 2))
    created_at       = Column(DateTime, default=datetime.utcnow)
