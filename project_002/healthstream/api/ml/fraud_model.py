# Train a RandomForest classifier to detect fraudulent claims.
import os
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

MODEL_PATH = Path(os.getenv("MODEL_PATH", "/tmp/fraud_model.pkl"))

INSURANCE_STATUS_MAP = {"APPROVED": 0, "DENIED": 1, "PENDING": 2, "PARTIAL": 3}
INSURANCE_TYPE_MAP   = {"MEDICARE": 0, "MEDICAID": 1, "PRIVATE": 2, "UNINSURED": 3}
HOSPITAL_TYPE_MAP    = {"GENERAL": 0, "SPECIALTY": 1, "TEACHING": 2, "CRITICAL_ACCESS": 3}

FEATURE_COLS = [
    "claim_amount",
    "approved_amount",
    "approval_ratio",
    "insurance_status_enc",
    "insurance_type_enc",
    "hospital_type_enc",
]


def _encode_features(df: pd.DataFrame) -> pd.DataFrame:
    # Convert categorical columns to numeric and add the approval ratio.
    df = df.copy()
    df["approval_ratio"] = (
        df["approved_amount"] / df["claim_amount"].replace(0, np.nan)
    ).fillna(0)

    ins_status = df["insurance_status"] if "insurance_status" in df.columns else pd.Series(["PENDING"] * len(df))
    ins_type   = df["insurance_type"]   if "insurance_type"   in df.columns else pd.Series(["PRIVATE"]  * len(df))
    hosp_type  = df["hospital_type"]    if "hospital_type"    in df.columns else pd.Series(["GENERAL"]  * len(df))

    df["insurance_status_enc"] = ins_status.map(INSURANCE_STATUS_MAP).fillna(2)
    df["insurance_type_enc"]   = ins_type.map(INSURANCE_TYPE_MAP).fillna(2)
    df["hospital_type_enc"]    = hosp_type.map(HOSPITAL_TYPE_MAP).fillna(0)
    return df


def train_model(claims_df: pd.DataFrame) -> Pipeline:
    # Encode features, split data, fit the pipeline, and save the model to disk.
    df = _encode_features(claims_df)

    if "is_fraud" not in df.columns:
        raise ValueError("claims_df must contain 'is_fraud' column")

    X = df[FEATURE_COLS].fillna(0)
    y = df["is_fraud"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y if y.sum() >= 2 else None,
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])

    pipeline.fit(X_train, y_train)

    y_pred  = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    try:
        auc = roc_auc_score(y_test, y_proba)
        logger.info("Fraud model trained, AUC: %.4f", auc)
    except ValueError:
        logger.info("Fraud model trained, AUC not available (single class in test split)")
    logger.info("\n%s", classification_report(y_test, y_pred, zero_division=0))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    logger.info("Model saved to %s", MODEL_PATH)

    return pipeline


def load_model() -> Pipeline:
    # Load the saved model from disk, or return None if it does not exist.
    if not MODEL_PATH.exists():
        logger.warning("No fraud model found at %s", MODEL_PATH)
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def predict_fraud_score(claim: Dict[str, Any], model: Pipeline) -> float:
    # Return the fraud probability for a single claim dictionary.
    df    = pd.DataFrame([claim])
    df    = _encode_features(df)
    X     = df[FEATURE_COLS].fillna(0)
    proba = model.predict_proba(X)[0][1]
    return round(float(proba), 4)


def predict_batch(claims: List[Dict[str, Any]], model: Pipeline) -> List[float]:
    # Return fraud probabilities for a list of claim dictionaries.
    df = pd.DataFrame(claims)
    df = _encode_features(df)
    X  = df[FEATURE_COLS].fillna(0)
    return [round(float(p), 4) for p in model.predict_proba(X)[:, 1]]
