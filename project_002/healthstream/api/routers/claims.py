# Endpoints to fetch and filter claims.
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import Claim
from schemas import ClaimOut, PaginatedResponse

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.get("/latest", response_model=List[ClaimOut], summary="Get latest claims")
def get_latest_claims(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return db.query(Claim).order_by(desc(Claim.claim_date)).limit(limit).all()


@router.get("/{claim_id}", response_model=ClaimOut, summary="Get claim by ID")
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.get("/", response_model=PaginatedResponse, summary="List claims with filters")
def list_claims(
    page:             int           = Query(1, ge=1),
    size:             int           = Query(20, ge=1, le=100),
    insurance_status: Optional[str] = None,
    is_fraud:         Optional[bool]= None,
    hospital_id:      Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Claim)
    if insurance_status:
        query = query.filter(Claim.insurance_status == insurance_status.upper())
    if is_fraud is not None:
        query = query.filter(Claim.is_fraud == is_fraud)
    if hospital_id:
        query = query.filter(Claim.hospital_id == hospital_id)

    total = query.count()
    items = query.order_by(desc(Claim.claim_date)).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(total=total, page=page, size=size, items=items)
