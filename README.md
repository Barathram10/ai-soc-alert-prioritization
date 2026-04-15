# 🔐 AI-Based Alert Prioritization for SOC

## 📌 Overview

This project uses machine learning to improve alert prioritization in Security Operations Centers (SOC).
The goal is to reduce false positives and help analysts focus on high-risk alerts instead of manually reviewing all alerts.

---

## 🚀 Key Features

* ✅ Inference-only ML pipeline (production-style)
* ✅ Random Forest-based alert scoring
* ✅ Risk-based alert prioritization
* ✅ Threshold tuning for precision vs recall trade-off
* ✅ Feature importance visualization (explainability)
* ✅ Streamlit interactive dashboard

---

## 🧠 How It Works

1. A pre-trained model is loaded (trained on CICIDS2017 dataset)
2. User uploads new alert data (CSV)
3. Model generates probability-based risk scores
4. Alerts are prioritized based on risk
5. Analysts focus on top-ranked alerts

---

## 📊 Dataset

* CICIDS2017 (Intrusion Detection Dataset)
* Contains real-world network traffic with attack and benign labels

---

## 🛠️ Tech Stack

* Python
* Scikit-learn
* Streamlit
* Pandas / NumPy
* Matplotlib

---

## ▶️ How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## ⚠️ Notes

* This repository uses an inference-only approach.
* Model artifacts and datasets are not included due to size constraints.

---

## 📸 Screenshots

<img width="1477" height="476" alt="image" src="https://github.com/user-attachments/assets/c52c9c47-f34c-4c94-b48a-07a1e1db86fc" />

<img width="1497" height="819" alt="image" src="https://github.com/user-attachments/assets/6d1a65d4-48da-4cd3-8281-ad93002fdd5c" />

<img width="1500" height="788" alt="image" src="https://github.com/user-attachments/assets/7ea9ba64-a3da-4dff-9fa3-769def31f989" />

<img width="1499" height="773" alt="image" src="https://github.com/user-attachments/assets/6136f505-d14b-4b54-8948-88bc7a005dfe" />


---

## 🎯 Project Impact

This system demonstrates how AI can be integrated into SOC workflows to:

* Reduce alert fatigue
* Improve detection efficiency
* Prioritize high-risk threats

---

## 👤 Author

Barathram Venkatachalapathy
