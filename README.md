# AI-Based Alert Prioritization for SOCs

## Overview

This project applies machine learning to Security Operations Center (SOC) alert triage. A Random Forest classifier trained on the CICIDS2017 dataset reduces false positives and ranks alerts by risk score, enabling analysts to focus on genuine threats instead of manually reviewing every alert.

**Bottom line:** On a held-out test set of 427,608 network flows, the model achieved 99.91% accuracy with a false-positive rate of just 0.08% — fewer than 1 in 1,000 benign alerts is incorrectly escalated.

---

## Key Features

- Inference-only ML pipeline (production-style, no retraining required at runtime)
- Random Forest classifier with probability-based risk scoring
- Risk-ranked alert queue — highest-risk alerts surface first
- Configurable classification threshold (precision vs. recall trade-off)
- Feature importance visualization for model explainability
- Streamlit interactive dashboard for analyst triage

---

## How It Works

1. A pre-trained Random Forest model is loaded (trained on CICIDS2017)
2. Analyst uploads a CSV of alert/flow data
3. Model assigns a risk score (0–1) to each alert via `predict_proba`
4. Alerts are ranked by risk score — highest priority at the top
5. Analyst adjusts the classification threshold slider to tune precision/recall in real time
6. Dashboard displays metrics, confusion matrix, and ranked alert table

---

## Model Performance

Evaluated on a stratified 80/20 held-out test split (427,608 flows: 366,613 benign, 60,995 attack).

| Metric | Value | What It Means |
|---|---|---|
| Accuracy | **99.91%** | Only 365 of 427,608 test flows misclassified |
| Precision (Attack) | **99.51%** | ~99 of every 100 flagged alerts are true attacks |
| Recall (Attack) | **99.90%** | 99.9% of actual attacks are caught |
| F1 Score | **99.70%** | Strong balance of precision and recall |
| False Positive Rate | **0.08%** | Only 0.08% of benign flows incorrectly flagged |

### Confusion Matrix (427,608 test flows)

|  | Predicted Benign | Predicted Attack |
|---|---|---|
| **Actual Benign** | 366,312 (TN) | 301 (FP) |
| **Actual Attack** | 64 (FN) | 60,931 (TP) |

> In a SOC processing 10,000 alerts/day at a typical 85% benign rate, this model generates approximately **7 false positives per day** — compared to hundreds or thousands from legacy rule-based SIEM correlation.

---

## Feature Importance (Top 10)

The model relies on interpretable flow-level statistics. The top 10 features account for ~51% of total Gini importance.

| # | Feature | Importance | What It Captures |
|---|---|---|---|
| 1 | Fwd Packet Length Mean | 0.0900 | Average size of forward packets |
| 2 | Fwd Packet Length Max | 0.0672 | Largest forward packet observed |
| 3 | Init_Win_bytes_forward | 0.0626 | Initial TCP window size (forward) |
| 4 | Avg Fwd Segment Size | 0.0543 | Mean TCP segment size (forward) |
| 5 | Subflow Fwd Bytes | 0.0492 | Bytes per forward subflow |
| 6 | Total Length of Fwd Packets | 0.0488 | Aggregate payload size (forward) |
| 7 | Max Packet Length | 0.0389 | Largest packet in either direction |
| 8 | Init_Win_bytes_backward | 0.0378 | Initial TCP window size (backward) |
| 9 | Bwd Packet Length Min | 0.0318 | Smallest backward packet observed |
| 10 | Packet Length Variance | 0.0308 | Variability in packet sizes across the flow |

Packet-size and TCP handshake features dominate — consistent with how port scans, DoS floods, and brute-force attacks differ structurally from normal traffic.

---

## Dataset

- **CICIDS2017** (Canadian Institute for Cybersecurity)
- ~2.8 million labeled network flow records
- 14 attack categories: DoS/DDoS, brute force, web attacks, infiltration, botnet, and more
- Heavily class-imbalanced (benign traffic dominates), representative of real SOC distributions

---

## Tech Stack

- Python
- Scikit-learn (Random Forest classifier)
- Streamlit (analyst-facing dashboard)
- Pandas / NumPy
- Matplotlib

---

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

> **Note:** Model artifacts and the full CICIDS2017 dataset are not included due to size constraints. The app runs in inference mode using a pre-trained model file.

---

## Screenshots

### 1. Full Dashboard — Model Configuration & SOC Triage Summary (Threshold 0.50)

The sidebar shows the loaded Random Forest model, CICIDS2017 training dataset, and 78 input features. The main panel shows 225,745 alerts scored in a single batch with live performance metrics at the default 0.50 threshold.

<img width="1477" height="476" alt="Risk-scored alert table showing alert_id, risk_score=1, priority=Critical, predicted_label=1 columns alongside Destination Port, Flow Duration, Total Fwd/Bwd Packets, and packet length features" src="https://github.com/user-attachments/assets/c52c9c47-f34c-4c94-b48a-07a1e1db86fc" />

<img width="1841" height="771" alt="image" src="https://github.com/user-attachments/assets/d86e4409-ddd4-49f3-b7d2-edb3f6b1cfd3" />

<img width="1499" height="773" alt="Full dashboard showing model config sidebar, SOC triage summary (225,745 scored, 128,027 flagged, 127,949 critical), and performance metrics: Accuracy 0.9999, Precision 0.9999, Recall 0.9999, F1 0.9999 at threshold 0.50" src="https://github.com/user-attachments/assets/6136f505-d14b-4b54-8948-88bc7a005dfe" />

---

### 2. Threshold Tuning — Precision vs. Recall Trade-off (Threshold 0.70)

Raising the threshold from 0.50 → 0.70 tightens the alert queue: flagged alerts drop from 128,027 to 127,997 and precision reaches 1.0000, meaning zero false positives at higher confidence. This demonstrates the real-time tuning capability built into the analyst interface.

<img width="1829" height="494" alt="image" src="https://github.com/user-attachments/assets/57a75d45-28fd-46bd-b471-589fce2dd249" />

<img width="1769" height="459" alt="image" src="https://github.com/user-attachments/assets/a84826ad-49f5-4b49-904d-120f48d2c80d" />

---

### 3. Risk-Scored Alert Data

Every alert is assigned a `risk_score` (0–1) and a `priority` label (Critical / High / Medium / Low) alongside the original network flow features. The table is sortable so analysts can filter by risk tier.

<img width="187" height="503" alt="image" src="https://github.com/user-attachments/assets/5ae0df95-4368-4e65-a2c7-b6403481c52d" />

---

### 4. Top 10 Prioritized Alerts Queue + Download

The dashboard surfaces the 10 highest-risk alerts at the top of the analyst queue, with a one-click CSV export for handoff to incident response or SOAR ticketing.

<img width="1434" height="674" alt="image" src="https://github.com/user-attachments/assets/ba11e1ec-4b63-4968-975d-88bd707ce0b6" />


---

## Project Impact

| Benefit | Detail |
|---|---|
| Alert noise reduction | 0.08% FPR = fewer wasted analyst investigations per shift |
| Faster MTTR | Risk-ranked queues surface real incidents earlier |
| Talent leverage | Smaller teams handle higher alert volumes |
| Defensible posture | Every prioritization decision is backed by a probability score and interpretable features |

---

## Limitations

- **Benchmark vs. production gap** — CICIDS2017 is a controlled dataset; real enterprise traffic may show lower performance
- **Concept drift** — 2017-era attack patterns; periodic retraining on current telemetry is required
- **No real-time integration** — current prototype operates on uploaded CSVs, not streaming SIEM events
- **Per-alert explainability** — global feature importances only; SHAP-based per-alert explanations are future work

---

## Future Work

- Streaming ingestion with Splunk or Elastic (real-time scoring at SIEM-event arrival)
- SHAP-based per-alert explanations for analyst trust
- Validation on UNSW-NB15 and CSE-CIC-IDS2018 datasets
- XGBoost / LightGBM benchmark comparison
- Analyst feedback loop for continuous retraining
- MITRE ATT&CK technique mapping per alert

---

## Author

Barathram Venkatachalapathy
