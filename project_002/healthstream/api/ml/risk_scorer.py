# Compute a composite risk score for a patient based on their claim history.
import logging
from typing import Dict, Any, List

import pandas as pd

logger = logging.getLogger(__name__)


def compute_patient_risk(patient_claims: List[Dict[str, Any]]) -> float:
    # Score is weighted across claim frequency, fraud history, denial rate,
    # average claim size, high-value claim proportion, and insurance status.
    if not patient_claims:
        return 0.0

    df = pd.DataFrame(patient_claims)

    n_claims       = len(df)
    avg_fraud      = df["fraud_score"].mean()      if "fraud_score"      in df.columns else 0.0
    denial_rate    = (df["insurance_status"] == "DENIED").mean() if "insurance_status" in df.columns else 0.0
    avg_amount     = df["claim_amount"].mean()      if "claim_amount"     in df.columns else 0.0
    high_value_pct = (df["claim_amount"] > 50_000).mean() if "claim_amount" in df.columns else 0.0
    uninsured      = (df.get("insurance_type", pd.Series([])) == "UNINSURED").any()

    score = (
        min(n_claims / 20, 1.0)          * 0.15
        + avg_fraud                       * 0.40
        + denial_rate                     * 0.20
        + min(avg_amount / 100_000, 1.0)  * 0.10
        + high_value_pct                  * 0.10
        + (0.05 if uninsured else 0.0)
    )

    return round(min(score, 1.0), 4)


def score_patients_bulk(
    patients: List[Dict],
    claims_by_patient: Dict[str, List[Dict]],
) -> List[Dict[str, Any]]:
    # Score each patient in the list using their associated claims.
    results = []
    for patient in patients:
        pid   = patient["patient_id"]
        score = compute_patient_risk(claims_by_patient.get(pid, []))
        results.append({"patient_id": pid, "risk_score": score})
    return results
