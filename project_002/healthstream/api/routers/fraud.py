# Endpoints to query fraud alerts and statistics.
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database import get_db
from models import FraudAlert
from schemas import FraudAlertOut

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


@router.get("/detection", response_model=List[FraudAlertOut], summary="Recent fraud alerts")
def get_fraud_alerts(
    limit:    int           = Query(50, ge=1, le=500),
    severity: Optional[str] = Query(None),
    resolved: Optional[bool]= Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(FraudAlert)
    if severity:
        query = query.filter(FraudAlert.severity == severity.upper())
    if resolved is not None:
        query = query.filter(FraudAlert.resolved == resolved)
    return query.order_by(desc(FraudAlert.created_at)).limit(limit).all()


@router.get("/stats", summary="Fraud statistics")
def get_fraud_stats(db: Session = Depends(get_db)):
    total_alerts = db.query(func.count(FraudAlert.alert_id)).scalar() or 0
    unresolved   = db.query(func.count(FraudAlert.alert_id)).filter(FraudAlert.resolved == False).scalar() or 0

    by_severity = (
        db.query(FraudAlert.severity, func.count(FraudAlert.alert_id).label("count"))
        .group_by(FraudAlert.severity)
        .all()
    )
    by_type = (
        db.query(FraudAlert.alert_type, func.count(FraudAlert.alert_id).label("count"))
        .group_by(FraudAlert.alert_type)
        .all()
    )

    return {
        "total_alerts":    total_alerts,
        "unresolved":      unresolved,
        "resolution_rate": round((total_alerts - unresolved) / max(total_alerts, 1) * 100, 2),
        "by_severity":     {r.severity: r.count for r in by_severity},
        "by_type":         {r.alert_type: r.count for r in by_type},
    }


@router.get("/high-risk-claims", response_model=List[FraudAlertOut], summary="High-risk unresolved alerts")
def get_high_risk_claims(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(FraudAlert)
        .filter(
            FraudAlert.severity.in_(["HIGH", "CRITICAL"]),
            FraudAlert.resolved == False,
        )
        .order_by(desc(FraudAlert.fraud_score))
        .limit(limit)
        .all()
    )
