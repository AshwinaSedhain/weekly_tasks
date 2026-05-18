# Shared fixtures available to all test files.
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-generator"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "ml"))

os.environ.setdefault("DB_HOST",     "localhost")
os.environ.setdefault("DB_PORT",     "5432")
os.environ.setdefault("DB_NAME",     "healthstream_test")
os.environ.setdefault("DB_USER",     "healthstream")
os.environ.setdefault("DB_PASSWORD", "healthstream123")


@pytest.fixture(scope="session")
def sample_patients():
    from generator import generate_patients
    return generate_patients(n=20)


@pytest.fixture(scope="session")
def sample_hospitals():
    from generator import generate_hospitals
    return generate_hospitals(n=5)


@pytest.fixture(scope="session")
def sample_claims(sample_patients, sample_hospitals):
    from generator import generate_batch
    return generate_batch(sample_patients, sample_hospitals, batch_size=100)
