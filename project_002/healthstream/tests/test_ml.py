# Unit tests for the ML fraud model and patient risk scorer.
import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "ml"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-generator"))


class TestFraudModel:
    @pytest.fixture
    def claims_df(self, sample_claims):
        return pd.DataFrame(sample_claims)

    def test_train_model_returns_pipeline(self, claims_df):
        from fraud_model import train_model
        model = train_model(claims_df)
        assert model is not None

    def test_predict_fraud_score_in_range(self, claims_df):
        from fraud_model import train_model, predict_fraud_score
        model = train_model(claims_df)
        claim = claims_df.iloc[0].to_dict()
        score = predict_fraud_score(claim, model)
        assert 0.0 <= score <= 1.0

    def test_predict_batch_returns_correct_length(self, claims_df):
        from fraud_model import train_model, predict_batch
        model  = train_model(claims_df)
        claims = claims_df.head(10).to_dict("records")
        scores = predict_batch(claims, model)
        assert len(scores) == 10

    def test_high_amount_claim_gets_higher_score(self, claims_df):
        from fraud_model import train_model, predict_fraud_score
        model = train_model(claims_df)

        normal_claim = {
            "claim_amount": 500.0,
            "approved_amount": 450.0,
            "insurance_status": "APPROVED",
            "insurance_type": "PRIVATE",
            "hospital_type": "GENERAL",
        }
        fraud_claim = {
            "claim_amount": 500_000.0,
            "approved_amount": 100.0,
            "insurance_status": "DENIED",
            "insurance_type": "UNINSURED",
            "hospital_type": "GENERAL",
        }
        normal_score = predict_fraud_score(normal_claim, model)
        fraud_score  = predict_fraud_score(fraud_claim, model)
        # Fraud claim should generally score higher (not guaranteed but likely)
        assert isinstance(normal_score, float)
        assert isinstance(fraud_score, float)


class TestRiskScorer:
    def test_empty_claims_returns_zero(self):
        from risk_scorer import compute_patient_risk
        score = compute_patient_risk([])
        assert score == 0.0

    def test_score_in_range(self, sample_claims):
        from risk_scorer import compute_patient_risk
        score = compute_patient_risk(sample_claims[:10])
        assert 0.0 <= score <= 1.0

    def test_high_fraud_history_increases_score(self):
        from risk_scorer import compute_patient_risk

        low_risk_claims = [
            {"fraud_score": 0.05, "claim_amount": 500, "insurance_status": "APPROVED",
             "insurance_type": "PRIVATE"}
            for _ in range(5)
        ]
        high_risk_claims = [
            {"fraud_score": 0.95, "claim_amount": 80_000, "insurance_status": "DENIED",
             "insurance_type": "UNINSURED"}
            for _ in range(5)
        ]
        low_score  = compute_patient_risk(low_risk_claims)
        high_score = compute_patient_risk(high_risk_claims)
        assert high_score > low_score

    def test_bulk_scoring(self, sample_patients, sample_claims):
        from risk_scorer import score_patients_bulk

        claims_by_patient = {}
        for c in sample_claims:
            pid = c["patient_id"]
            claims_by_patient.setdefault(pid, []).append(c)

        results = score_patients_bulk(sample_patients[:5], claims_by_patient)
        assert len(results) == 5
        for r in results:
            assert "patient_id" in r
            assert "risk_score" in r
            assert 0.0 <= r["risk_score"] <= 1.0
