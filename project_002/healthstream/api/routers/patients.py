# Endpoints to query patients and their claim history.
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import Patient, Claim
from schemas import PatientOut

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/high-risk", response_model=List[PatientOut], summary="High-risk patients")
def get_high_risk_patients(
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    limit:     int   = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return (
        db.query(Patient)
        .filter(Patient.risk_score >= threshold)
        .order_by(desc(Patient.risk_score))
        .limit(limit)
        .all()
    )


@router.get("/{patient_id}", response_model=PatientOut, summary="Get patient by ID")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/{patient_id}/claims", response_model=List, summary="Get patient claims")
def get_patient_claims(
    patient_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    claims = (
        db.query(Claim)
        .filter(Claim.patient_id == patient_id)
        .order_by(desc(Claim.claim_date))
        .limit(limit)
        .all()
    )
    return [
        {
            "claim_id":         c.claim_id,
            "claim_amount":     float(c.claim_amount or 0),
            "insurance_status": c.insurance_status,
            "claim_date":       c.claim_date.isoformat() if c.claim_date else None,
            "is_fraud":         c.is_fraud,
            "fraud_score":      float(c.fraud_score or 0),
        }
        for c in claims
    ]


@router.get("/", response_model=List[PatientOut], summary="List patients")
def list_patients(
    page:  int = Query(1, ge=1),
    size:  int = Query(20, ge=1, le=100),
    state: str = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Patient)
    if state:
        query = query.filter(Patient.state == state.upper())
    return query.offset((page - 1) * size).limit(size).all()
