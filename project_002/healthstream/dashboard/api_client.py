# Fetch data from the FastAPI backend with short-lived caching.
import logging
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from config import API_BASE_URL

logger  = logging.getLogger(__name__)
TIMEOUT = 10


def _get(endpoint: str, params: Optional[Dict] = None) -> Any:
    # Make a GET request and return parsed JSON, or None on failure.
    try:
        resp = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the API service running?")
        return None
    except Exception as exc:
        logger.error("API error %s: %s", endpoint, exc)
        return None


@st.cache_data(ttl=30)
def get_summary() -> Dict:
    return _get("/analytics/summary") or {}


@st.cache_data(ttl=60)
def get_cost_trends(days: int = 30) -> List[Dict]:
    return _get("/analytics/cost-trends", {"days": days}) or []


@st.cache_data(ttl=30)
def get_latest_claims(limit: int = 50) -> List[Dict]:
    return _get("/claims/latest", {"limit": limit}) or []


@st.cache_data(ttl=60)
def get_fraud_alerts(limit: int = 50, severity: Optional[str] = None) -> List[Dict]:
    params = {"limit": limit}
    if severity:
        params["severity"] = severity
    return _get("/fraud/detection", params) or []


@st.cache_data(ttl=60)
def get_fraud_stats() -> Dict:
    return _get("/fraud/stats") or {}


@st.cache_data(ttl=60)
def get_hospital_performance(limit: int = 20) -> List[Dict]:
    return _get("/hospitals/performance", {"limit": limit}) or []


@st.cache_data(ttl=60)
def get_high_risk_patients(threshold: float = 0.7, limit: int = 50) -> List[Dict]:
    return _get("/patients/high-risk", {"threshold": threshold, "limit": limit}) or []


@st.cache_data(ttl=60)
def get_diagnosis_breakdown(limit: int = 10) -> List[Dict]:
    return _get("/analytics/diagnosis-breakdown", {"limit": limit}) or []


@st.cache_data(ttl=60)
def get_insurance_breakdown() -> List[Dict]:
    return _get("/analytics/insurance-breakdown") or []


def get_health() -> Dict:
    return _get("/health") or {"status": "unknown", "database": "unknown"}
