# Pydantic response schemas used by the API endpoints.
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel


class ClaimOut(BaseModel):
    claim_id:         str
    patient_id:       str
    hospital_id:      str
    treatment_code:   Optional[str]
    diagnosis_code:   str
    claim_amount:     float
    approved_amount:  Optional[float]
    insurance_status: Optional[str]
    claim_date:       Optional[datetime]
    is_fraud:         bool
    fraud_score:      Optional[float]
    status:           Optional[str]

    class Config:
        from_attributes = True


class PatientOut(BaseModel):
    patient_id:     str
    first_name:     str
    last_name:      str
    gender:         Optional[str]
    state:          Optional[str]
    insurance_type: Optional[str]
    risk_score:     Optional[float]

    class Config:
        from_attributes = True


class HospitalOut(BaseModel):
    hospital_id:       str
    hospital_name:     str
    state:             Optional[str]
    hospital_type:     Optional[str]
    bed_count:         Optional[int]
    performance_score: Optional[float]

    class Config:
        from_attributes = True


class FraudAlertOut(BaseModel):
    alert_id:     int
    claim_id:     str
    patient_id:   str
    hospital_id:  str
    fraud_score:  float
    alert_reason: Optional[str]
    alert_type:   Optional[str]
    severity:     Optional[str]
    resolved:     bool
    created_at:   Optional[datetime]

    class Config:
        from_attributes = True


class CostTrendOut(BaseModel):
    summary_date:     date
    total_claims:     int
    total_amount:     float
    avg_claim_amount: float
    fraud_detected:   int


class HospitalPerformanceOut(BaseModel):
    hospital_id:       str
    hospital_name:     str
    state:             Optional[str]
    total_claims:      int
    total_amount:      float
    fraud_count:       int
    performance_score: Optional[float]


class PaginatedResponse(BaseModel):
    total: int
    page:  int
    size:  int
    items: List


class HealthCheck(BaseModel):
    status:   str
    database: str
    version:  str
