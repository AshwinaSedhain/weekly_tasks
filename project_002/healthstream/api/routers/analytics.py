# Endpoints for cost trends, platform summary, and breakdowns.
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database import get_db
from models import AnalyticsSummary, Claim
from schemas import CostTrendOut

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/cost-trends", response_model=List[CostTrendOut], summary="Daily cost trends")
def get_cost_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(AnalyticsSummary)
        .order_by(desc(AnalyticsSummary.summary_date))
        .limit(days)
        .all()
    )
    return [
        CostTrendOut(
            summary_date=r.summary_date,
            total_claims=r.total_claims or 0,
            total_amount=float(r.total_amount or 0),
            avg_claim_amount=float(r.avg_claim_amount or 0),
            fraud_detected=r.fraud_detected or 0,
        )
        for r in reversed(rows)
    ]


@router.get("/summary", summary="Overall platform summary")
def get_summary(db: Session = Depends(get_db)):
    total_claims = db.query(func.count(Claim.claim_id)).scalar() or 0
    total_amount = db.query(func.sum(Claim.claim_amount)).scalar() or 0
    avg_amount   = db.query(func.avg(Claim.claim_amount)).scalar() or 0
    fraud_count  = db.query(func.count(Claim.claim_id)).filter(Claim.is_fraud == True).scalar() or 0
    pending      = db.query(func.count(Claim.claim_id)).filter(Claim.status == "PENDING").scalar() or 0

    return {
        "total_claims":   total_claims,
        "total_amount":   round(float(total_amount), 2),
        "avg_amount":     round(float(avg_amount), 2),
        "fraud_count":    fraud_count,
        "fraud_rate":     round(fraud_count / max(total_claims, 1) * 100, 2),
        "pending_claims": pending,
    }


@router.get("/diagnosis-breakdown", summary="Claims by diagnosis code")
def get_diagnosis_breakdown(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Claim.diagnosis_code,
            func.count(Claim.claim_id).label("count"),
            func.sum(Claim.claim_amount).label("total_amount"),
        )
        .group_by(Claim.diagnosis_code)
        .order_by(desc("count"))
        .limit(limit)
        .all()
    )
    return [
        {
            "diagnosis_code": r.diagnosis_code,
            "count":          r.count,
            "total_amount":   float(r.total_amount or 0),
        }
        for r in rows
    ]


@router.get("/insurance-breakdown", summary="Claims by insurance status")
def get_insurance_breakdown(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Claim.insurance_status,
            func.count(Claim.claim_id).label("count"),
            func.sum(Claim.claim_amount).label("total_amount"),
        )
        .group_by(Claim.insurance_status)
        .order_by(desc("count"))
        .all()
    )
    return [
        {
            "insurance_status": r.insurance_status,
            "count":            r.count,
            "total_amount":     float(r.total_amount or 0),
        }
        for r in rows
    ]
