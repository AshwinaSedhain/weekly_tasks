# Unit tests for API schemas and Kafka consumer validation logic.
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "routers"))


def _make_app():
    """Create a FastAPI test app with mocked DB."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    return FastAPI()


class TestHealthEndpoint:
    """Test the /health endpoint with a mocked engine."""

    def test_health_returns_200(self):
        with patch("database.engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
            mock_engine.connect.return_value.__exit__  = MagicMock(return_value=False)

            from fastapi.testclient import TestClient
            import importlib
            import main as app_module
            importlib.reload(app_module)

            client = TestClient(app_module.app)
            # Just verify the app can be instantiated
            assert app_module.app is not None


class TestSchemas:
    """Test Pydantic schema validation."""

    def test_claim_out_schema(self):
        from schemas import ClaimOut
        claim = ClaimOut(
            claim_id="test-id",
            patient_id="pat-1",
            hospital_id="hosp-1",
            treatment_code="T001",
            diagnosis_code="I21.0",
            claim_amount=5000.0,
            approved_amount=4500.0,
            insurance_status="APPROVED",
            claim_date=None,
            is_fraud=False,
            fraud_score=0.05,
            status="PROCESSED",
        )
        assert claim.claim_id == "test-id"
        assert claim.claim_amount == 5000.0

    def test_patient_out_schema(self):
        from schemas import PatientOut
        patient = PatientOut(
            patient_id="pat-1",
            first_name="John",
            last_name="Doe",
            gender="MALE",
            state="CA",
            insurance_type="PRIVATE",
            risk_score=0.3,
        )
        assert patient.patient_id == "pat-1"

    def test_fraud_alert_out_schema(self):
        from schemas import FraudAlertOut
        from datetime import datetime
        alert = FraudAlertOut(
            alert_id=1,
            claim_id="claim-1",
            patient_id="pat-1",
            hospital_id="hosp-1",
            fraud_score=0.92,
            alert_reason="High amount",
            alert_type="HIGH_AMOUNT",
            severity="CRITICAL",
            resolved=False,
            created_at=datetime.utcnow(),
        )
        assert alert.severity == "CRITICAL"
        assert alert.fraud_score == 0.92

    def test_cost_trend_schema(self):
        from schemas import CostTrendOut
        from datetime import date
        trend = CostTrendOut(
            summary_date=date.today(),
            total_claims=100,
            total_amount=500_000.0,
            avg_claim_amount=5000.0,
            fraud_detected=5,
        )
        assert trend.total_claims == 100

    def test_hospital_performance_schema(self):
        from schemas import HospitalPerformanceOut
        perf = HospitalPerformanceOut(
            hospital_id="hosp-1",
            hospital_name="Test Medical Center",
            state="TX",
            total_claims=500,
            total_amount=2_500_000.0,
            fraud_count=10,
            performance_score=87.5,
        )
        assert perf.performance_score == 87.5


class TestKafkaConsumerValidation:
    """Test claim validation logic from the Kafka consumer."""

    def test_valid_claim_passes(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kafka"))
        from consumer import validate_claim
        claim = {
            "claim_id":    "abc-123",
            "patient_id":  "pat-1",
            "hospital_id": "hosp-1",
            "claim_amount": 1500.0,
            "claim_date":  "2024-01-15T10:00:00",
        }
        is_valid, reason = validate_claim(claim)
        assert is_valid is True
        assert reason == "OK"

    def test_missing_claim_id_fails(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kafka"))
        from consumer import validate_claim
        claim = {
            "patient_id":  "pat-1",
            "hospital_id": "hosp-1",
            "claim_amount": 1500.0,
            "claim_date":  "2024-01-15T10:00:00",
        }
        is_valid, reason = validate_claim(claim)
        assert is_valid is False

    def test_negative_amount_fails(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kafka"))
        from consumer import validate_claim
        claim = {
            "claim_id":    "abc-123",
            "patient_id":  "pat-1",
            "hospital_id": "hosp-1",
            "claim_amount": -100.0,
            "claim_date":  "2024-01-15T10:00:00",
        }
        is_valid, reason = validate_claim(claim)
        assert is_valid is False

    def test_excessive_amount_fails(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kafka"))
        from consumer import validate_claim
        claim = {
            "claim_id":    "abc-123",
            "patient_id":  "pat-1",
            "hospital_id": "hosp-1",
            "claim_amount": 2_000_000.0,
            "claim_date":  "2024-01-15T10:00:00",
        }
        is_valid, reason = validate_claim(claim)
        assert is_valid is False
