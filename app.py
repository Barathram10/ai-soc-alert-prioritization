import json
from pathlib import Path
from typing import List, Optional, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

st.set_page_config(page_title="AI-Based Alert Prioritization (SOC)", layout="wide")

ARTIFACT_DIR = Path("artifacts")
MODEL_PATH = ARTIFACT_DIR / "model.joblib"
FEATURES_PATH = ARTIFACT_DIR / "feature_columns.json"
THRESHOLD_PATH = ARTIFACT_DIR / "threshold.json"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"

HELPER_COLUMNS = {
    "risk_score",
    "y_pred",
    "y_pred_optimized",
    "y_pred_rf",
    "predicted_label",
    "priority",
    "alert_id",
}
LIKELY_LABEL_COLUMNS = ["Label", "label", "y_true", "actual_label", "Actual Label", "target", "class"]


@st.cache_resource
def load_model(model_path: Path):
    return joblib.load(model_path)


@st.cache_data
def load_json(json_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def artifacts_exist() -> List[str]:
    missing = []
    for path in [MODEL_PATH, FEATURES_PATH, THRESHOLD_PATH]:
        if not path.exists():
            missing.append(str(path))
    return missing


def normalize_binary_label(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()
    missing_like = {"", "nan", "none", "null", "na", "n/a"}
    mapping = {
        "benign": 0,
        "normal": 0,
        "0": 0,
        "false": 0,
        "attack": 1,
        "malicious": 1,
        "anomaly": 1,
        "1": 1,
        "true": 1,
    }
    mapped = s.map(mapping)
    numeric = pd.to_numeric(series, errors="coerce")

    labels = mapped.copy()
    labels = labels.fillna(numeric)
    attack_text = labels.isna() & ~s.isin(missing_like)
    labels.loc[attack_text] = 1
    return labels


def prepare_features(df: pd.DataFrame, feature_columns: List[str]) -> Tuple[pd.DataFrame, dict]:
    working_df = df.copy()
    working_df.columns = working_df.columns.astype(str).str.strip()

    numeric_df = working_df.select_dtypes(include=[np.number]).copy()
    numeric_df.replace([np.inf, -np.inf], np.nan, inplace=True)

    present_features = [c for c in feature_columns if c in numeric_df.columns]
    missing_features = [c for c in feature_columns if c not in numeric_df.columns]
    extra_numeric = [c for c in numeric_df.columns if c not in feature_columns and c not in HELPER_COLUMNS]

    for col in missing_features:
        numeric_df[col] = np.nan

    X = numeric_df[feature_columns].copy()
    diagnostics = {
        "present_features": present_features,
        "missing_features": missing_features,
        "extra_numeric": extra_numeric,
        "row_count": len(X),
    }
    return X, diagnostics


def get_final_estimator(model):
    if hasattr(model, "steps") and model.steps:
        return model.steps[-1][1]
    if hasattr(model, "named_steps") and model.named_steps:
        try:
            last_step_name = list(model.named_steps.keys())[-1]
            return model.named_steps[last_step_name]
        except Exception:
            pass
    return model


def get_feature_importance(model, feature_columns: List[str], metadata: Optional[dict] = None) -> Optional[pd.Series]:
    estimator = get_final_estimator(model)

    if hasattr(estimator, "feature_importances_"):
        return pd.Series(estimator.feature_importances_, index=feature_columns).sort_values(ascending=False)

    if hasattr(estimator, "coef_"):
        coef = np.ravel(estimator.coef_)
        return pd.Series(np.abs(coef), index=feature_columns).sort_values(ascending=False)

    if metadata and isinstance(metadata.get("top_10_features"), dict):
        return pd.Series(metadata["top_10_features"]).sort_values(ascending=False)

    return None


def detect_default_label_column(df: pd.DataFrame) -> str:
    for col in LIKELY_LABEL_COLUMNS:
        if col in df.columns:
            return col
    return "None"


def render_metrics(y_true: pd.Series, preds: pd.Series) -> None:
    st.subheader("Performance Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accuracy", f"{accuracy_score(y_true, preds):.4f}")
    m2.metric("Precision", f"{precision_score(y_true, preds, zero_division=0):.4f}")
    m3.metric("Recall", f"{recall_score(y_true, preds, zero_division=0):.4f}")
    m4.metric("F1 Score", f"{f1_score(y_true, preds, zero_division=0):.4f}")


def reset_scoring_state() -> None:
    for key in ["scored", "ranked", "preds", "uploaded_name", "uploaded_df", "diagnostics", "threshold_used"]:
        if key in st.session_state:
            del st.session_state[key]


st.title("AI-Based Alert Prioritization (SOC)")
st.caption("Inference-only mode: upload new alerts, score them with a pre-trained model, and review prioritized results.")

missing = artifacts_exist()
if missing:
    st.error(
        "Missing model artifacts. Before running this app, place these files inside an `artifacts/` folder next to the app: "
        + ", ".join(missing)
    )
    st.stop()

model = load_model(MODEL_PATH)
feature_columns = load_json(FEATURES_PATH)
threshold_config = load_json(THRESHOLD_PATH)
default_threshold = float(threshold_config.get("threshold", 0.5))
metadata = load_json(METADATA_PATH) if METADATA_PATH.exists() else {}

if "scored" not in st.session_state:
    st.session_state.scored = False

with st.sidebar:
    st.header("Model Configuration")
    st.write(f"**Loaded model:** {metadata.get('model_name', 'Pretrained model')}")
    st.write(f"**Training dataset:** {metadata.get('dataset', 'Historical CICIDS2017 data')}")
    st.write(f"**Feature count:** {len(feature_columns)}")
    threshold = st.slider("Decision threshold", 0.1, 0.9, default_threshold, 0.05)
    st.caption("Lower threshold increases recall.")
    st.caption("Higher threshold increases precision.")

uploaded_file = st.file_uploader("Upload new alert dataset (CSV)", type=["csv"])

if uploaded_file is not None:
    if st.session_state.get("uploaded_name") != uploaded_file.name:
        reset_scoring_state()
        df = pd.read_csv(uploaded_file)
        X_infer, diagnostics = prepare_features(df, feature_columns)
        st.session_state.uploaded_name = uploaded_file.name
        st.session_state.uploaded_df = df
        st.session_state.X_infer = X_infer
        st.session_state.diagnostics = diagnostics
    else:
        df = st.session_state.uploaded_df
        X_infer = st.session_state.X_infer
        diagnostics = st.session_state.diagnostics

    st.subheader("Uploaded Dataset Preview")
    st.dataframe(df.head())

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows uploaded", diagnostics["row_count"])
    col2.metric("Matched training features", len(diagnostics["present_features"]))
    col3.metric("Missing training features", len(diagnostics["missing_features"]))

    with st.expander("Schema diagnostics"):
        st.write("**Missing training features filled with NaN:**")
        st.write(diagnostics["missing_features"] if diagnostics["missing_features"] else "None")
        st.write("**Extra numeric columns ignored for scoring:**")
        st.write(diagnostics["extra_numeric"] if diagnostics["extra_numeric"] else "None")

    default_label_col = detect_default_label_column(df)
    label_options = ["None"] + list(df.columns)
    default_index = label_options.index(default_label_col) if default_label_col in label_options else 0
    actual_label_col = st.selectbox(
        "Actual label column for evaluation",
        options=label_options,
        index=default_index,
        key="actual_label_col",
        help="If your uploaded CSV contains the true label column, metrics will be calculated automatically after scoring.",
    )

    if st.button("Score Alerts"):
        try:
            proba_output = model.predict_proba(X_infer)
        except Exception as exc:
            st.error(f"Prediction failed: {exc}")
            st.stop()

        if proba_output.shape[1] < 2:
            st.error("The loaded model did not return binary class probabilities.")
            st.stop()

        probs = proba_output[:, 1]
        preds = (probs >= threshold).astype(int)

        ranked = df.copy()
        ranked.insert(0, "alert_id", np.arange(1, len(ranked) + 1))
        ranked["risk_score"] = probs
        ranked["predicted_label"] = preds
        ranked["priority"] = pd.cut(
            ranked["risk_score"],
            bins=[-0.01, 0.40, 0.65, 0.85, 1.0],
            labels=["Low", "Medium", "High", "Critical"],
        )
        ranked = ranked.sort_values(by="risk_score", ascending=False).reset_index(drop=True)
        ranked["alert_id"] = np.arange(1, len(ranked) + 1)

        st.session_state.scored = True
        st.session_state.ranked = ranked
        st.session_state.preds = preds
        st.session_state.threshold_used = threshold

    if st.session_state.get("scored", False):
        ranked = st.session_state.ranked
        preds = st.session_state.preds
        threshold_used = st.session_state.threshold_used

        st.subheader("SOC Triage Summary")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Scored alerts", len(ranked))
        s2.metric("Alerts flagged", int((ranked["predicted_label"] == 1).sum()))
        s3.metric("Critical alerts", int((ranked["priority"] == "Critical").sum()))
        s4.metric("Threshold used", f"{threshold_used:.2f}")

        if actual_label_col != "None" and actual_label_col in df.columns:
            y_true = normalize_binary_label(df[actual_label_col])
            preds_series = pd.Series(preds, index=df.index)
            valid_labels = y_true.notna()

            if valid_labels.any():
                render_metrics(y_true[valid_labels].astype(int), preds_series[valid_labels].astype(int))
                if not valid_labels.all():
                    st.caption(
                        f"Metrics calculated on {int(valid_labels.sum())} rows with usable labels; "
                        f"{int((~valid_labels).sum())} rows were skipped."
                    )
            else:
                st.warning(
                    f"No usable binary labels were found in `{actual_label_col}`. "
                    "Expected values such as 0/1, true/false, benign/attack, or normal/malicious."
                )
        else:
            metrics_meta = metadata.get("metrics_at_optimized_threshold") if isinstance(metadata, dict) else None
            if isinstance(metrics_meta, dict):
                st.subheader("Stored Model Performance Metrics")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Accuracy", f"{metrics_meta.get('accuracy', 0):.4f}")
                m2.metric("Precision", f"{metrics_meta.get('precision', 0):.4f}")
                m3.metric("Recall", f"{metrics_meta.get('recall', 0):.4f}")
                m4.metric("F1 Score", f"{metrics_meta.get('f1', 0):.4f}")

        st.subheader("Top 10 Prioritized Alerts")
        preferred_cols = [c for c in ["alert_id", "risk_score", "priority", "predicted_label"] if c in ranked.columns]
        remaining_cols = [c for c in ranked.columns if c not in preferred_cols]
        st.dataframe(ranked[preferred_cols + remaining_cols].head(10), use_container_width=True)

        csv_bytes = ranked.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download scored alerts",
            data=csv_bytes,
            file_name="scored_alerts.csv",
            mime="text/csv",
        )

        importance = get_feature_importance(model, feature_columns, metadata)
        if importance is not None:
            st.subheader("Feature Importance / Model Explainability")
            top = importance.head(10).sort_values(ascending=True)
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.barh(top.index, top.values)
            ax.set_title("Top 10 Important Features")
            ax.set_xlabel("Importance Score")
            st.pyplot(fig)

        if metadata:
            with st.expander("Stored model metadata"):
                st.json(metadata)
