# Unit tests for the data generator module.
import pytest
from datetime import datetime


class TestPatientGeneration:
    def test_generates_correct_count(self, sample_patients):
        assert len(sample_patients) == 20

    def test_patient_has_required_fields(self, sample_patients):
        required = ["patient_id", "first_name", "last_name", "date_of_birth",
                    "gender", "state", "insurance_type", "risk_score"]
        for patient in sample_patients:
            for field in required:
                assert field in patient

    def test_patient_ids_are_unique(self, sample_patients):
        ids = [p["patient_id"] for p in sample_patients]
        assert len(ids) == len(set(ids))

    def test_risk_score_in_range(self, sample_patients):
        for p in sample_patients:
            assert 0.0 <= p["risk_score"] <= 1.0

    def test_insurance_type_valid(self, sample_patients):
        valid = {"MEDICARE", "MEDICAID", "PRIVATE", "UNINSURED"}
        for p in sample_patients:
            assert p["insurance_type"] in valid

    def test_gender_valid(self, sample_patients):
        valid = {"MALE", "FEMALE", "OTHER"}
        for p in sample_patients:
            assert p["gender"] in valid


class TestHospitalGeneration:
    def test_generates_correct_count(self, sample_hospitals):
        assert len(sample_hospitals) == 5

    def test_hospital_has_required_fields(self, sample_hospitals):
        required = ["hospital_id", "hospital_name", "state", "hospital_type",
                    "bed_count", "performance_score"]
        for h in sample_hospitals:
            for field in required:
                assert field in h

    def test_bed_count_positive(self, sample_hospitals):
        for h in sample_hospitals:
            assert h["bed_count"] > 0

    def test_performance_score_in_range(self, sample_hospitals):
        for h in sample_hospitals:
            assert 0.0 <= h["performance_score"] <= 100.0


class TestClaimGeneration:
    def test_generates_correct_count(self, sample_claims):
        assert len(sample_claims) == 100

    def test_claim_has_required_fields(self, sample_claims):
        required = [
            "claim_id", "patient_id", "hospital_id", "treatment_code",
            "diagnosis_code", "claim_amount", "approved_amount",
            "insurance_status", "claim_date", "is_fraud", "fraud_score",
        ]
        for claim in sample_claims:
            for field in required:
                assert field in claim

    def test_claim_ids_are_unique(self, sample_claims):
        ids = [c["claim_id"] for c in sample_claims]
        assert len(ids) == len(set(ids))

    def test_claim_amount_positive(self, sample_claims):
        for c in sample_claims:
            assert c["claim_amount"] > 0

    def test_fraud_score_in_range(self, sample_claims):
        for c in sample_claims:
            assert 0.0 <= c["fraud_score"] <= 1.0

    def test_insurance_status_valid(self, sample_claims):
        valid = {"APPROVED", "DENIED", "PENDING", "PARTIAL"}
        for c in sample_claims:
            assert c["insurance_status"] in valid

    def test_claim_date_is_parseable(self, sample_claims):
        for c in sample_claims:
            assert isinstance(c["claim_date"], str)
            datetime.fromisoformat(c["claim_date"])

    def test_patient_ids_reference_known_patients(self, sample_claims, sample_patients):
        patient_ids = {p["patient_id"] for p in sample_patients}
        for c in sample_claims:
            assert c["patient_id"] in patient_ids

    def test_hospital_ids_reference_known_hospitals(self, sample_claims, sample_hospitals):
        hospital_ids = {h["hospital_id"] for h in sample_hospitals}
        for c in sample_claims:
            assert c["hospital_id"] in hospital_ids
