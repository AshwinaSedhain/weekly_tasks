# Endpoints to query hospitals and their performance metrics.
from typing import List
import sqlalchemy
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database import get_db
from models import Hospital, Claim
from schemas import HospitalOut, HospitalPerformanceOut

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.get("/performance", response_model=List[HospitalPerformanceOut], summary="Hospital performance ranking")
def get_hospital_performance(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Hospital.hospital_id,
            Hospital.hospital_name,
            Hospital.state,
            Hospital.performance_score,
            func.count(Claim.claim_id).label("total_claims"),
            func.sum(Claim.claim_amount).label("total_amount"),
            func.sum(func.cast(Claim.is_fraud, sqlalchemy.Integer)).label("fraud_count"),
        )
        .outerjoin(Claim, Hospital.hospital_id == Claim.hospital_id)
        .group_by(
            Hospital.hospital_id,
            Hospital.hospital_name,
            Hospital.state,
            Hospital.performance_score,
        )
        .order_by(desc(Hospital.performance_score))
        .limit(limit)
        .all()
    )
    return [
        HospitalPerformanceOut(
            hospital_id=r.hospital_id,
            hospital_name=r.hospital_name,
            state=r.state,
            total_claims=r.total_claims or 0,
            total_amount=float(r.total_amount or 0),
            fraud_count=r.fraud_count or 0,
            performance_score=float(r.performance_score or 0),
        )
        for r in rows
    ]


@router.get("/{hospital_id}", response_model=HospitalOut, summary="Get hospital by ID")
def get_hospital(hospital_id: str, db: Session = Depends(get_db)):
    hospital = db.query(Hospital).filter(Hospital.hospital_id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital


@router.get("/", response_model=List[HospitalOut], summary="List hospitals")
def list_hospitals(
    page:  int = Query(1, ge=1),
    size:  int = Query(20, ge=1, le=100),
    state: str = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Hospital)
    if state:
        query = query.filter(Hospital.state == state.upper())
    return query.offset((page - 1) * size).limit(size).all()
