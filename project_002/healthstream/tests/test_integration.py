# Integration tests that verify end-to-end data flow without live services.
import sys
import os
import pytest
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-generator"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "ml"))


class TestPipelineDataFlow:
    """Test the data flow from generator through validation to ML scoring."""

    def test_full_claim_pipeline(self, sample_patients, sample_hospitals):
        """Generate claims, validate them, and score for fraud."""
        from generator import generate_batch
        from fraud_model import train_model, predict_batch

        # Step 1: Generate
        claims = generate_batch(sample_patients, sample_hospitals, batch_size=50)
        assert len(claims) == 50

        # Step 2: Validate (simulate consumer validation)
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kafka"))
        from consumer import validate_claim
        valid_claims = [c for c in claims if validate_claim(c)[0]]
        assert len(valid_claims) > 0

        # Step 3: ML fraud scoring
        df = pd.DataFrame(valid_claims)
        model  = train_model(df)
        scores = predict_batch(valid_claims, model)
        assert len(scores) == len(valid_claims)
        assert all(0.0 <= s <= 1.0 for s in scores)

    def test_historical_data_generation(self, sample_patients, sample_hospitals):
        """Test historical claim generation for seeding."""
        from generator import generate_historical_claims
        claims = generate_historical_claims(
            sample_patients, sample_hospitals, days=7, claims_per_day=10
        )
        assert len(claims) == 70  # 7 days * 10 claims

        # All claims should have valid dates
        for c in claims:
            dt = datetime.fromisoformat(c["claim_date"])
            assert dt is not None

    def test_risk_scoring_pipeline(self, sample_patients, sample_claims):
        """Test patient risk scoring on generated data."""
        from risk_scorer import score_patients_bulk

        claims_by_patient = {}
        for c in sample_claims:
            pid = c["patient_id"]
            claims_by_patient.setdefault(pid, []).append(c)

        results = score_patients_bulk(sample_patients, claims_by_patient)
        assert len(results) == len(sample_patients)

        # All scores should be valid
        for r in results:
            assert 0.0 <= r["risk_score"] <= 1.0

    def test_fraud_detection_identifies_high_amounts(self, sample_patients, sample_hospitals):
        """Claims with very high amounts should tend to get higher fraud scores."""
        from generator import generate_claim
        from fraud_model import train_model, predict_fraud_score
        from datetime import datetime

        # Generate training data
        from generator import generate_batch
        train_claims = generate_batch(sample_patients, sample_hospitals, batch_size=100)
        df    = pd.DataFrame(train_claims)
        model = train_model(df)

        # Create a clearly suspicious claim
        suspicious = {
            "claim_id":         "test-suspicious",
            "patient_id":       sample_patients[0]["patient_id"],
            "hospital_id":      sample_hospitals[0]["hospital_id"],
            "treatment_code":   "T001",
            "diagnosis_code":   "I21.0",
            "claim_amount":     999_000.0,
            "approved_amount":  100.0,
            "insurance_status": "DENIED",
            "insurance_type":   "UNINSURED",
            "hospital_type":    "GENERAL",
            "claim_date":       datetime.utcnow().isoformat(),
            "is_fraud":         True,
            "fraud_score":      0.99,
            "status":           "PENDING",
        }

        score = predict_fraud_score(suspicious, model)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestDataQuality:
    """Test data quality constraints."""

    def test_no_null_claim_ids(self, sample_claims):
        for c in sample_claims:
            assert c["claim_id"] is not None
            assert len(c["claim_id"]) > 0

    def test_no_negative_amounts(self, sample_claims):
        for c in sample_claims:
            assert c["claim_amount"] > 0
            assert c["approved_amount"] >= 0

    def test_approved_amount_lte_claim_amount(self, sample_claims):
        for c in sample_claims:
            assert c["approved_amount"] <= c["claim_amount"] * 1.01  # 1% tolerance

    def test_all_claims_have_valid_treatment_codes(self, sample_claims):
        valid_codes = {f"T{str(i).zfill(3)}" for i in range(1, 16)}
        for c in sample_claims:
            assert c["treatment_code"] in valid_codes

    def test_diagnosis_codes_not_empty(self, sample_claims):
        for c in sample_claims:
            assert c["diagnosis_code"]
            assert len(c["diagnosis_code"]) >= 2
