
import pandas as pd
import joblib

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# Load trained model and validation data
model = joblib.load(
    "backend/models/predictive_maintenance_model.joblib"
)

X_val = pd.read_csv("backend/data/X_val.csv")
y_val = pd.read_csv("backend/data/y_val.csv").squeeze()

# Get failure probabilities
probabilities = model.predict_proba(X_val)[:, 1]

# Compare different thresholds
thresholds = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

print("\n========== THRESHOLD ANALYSIS ==========")

for threshold in thresholds:
    predictions = (probabilities >= threshold).astype(int)

    precision = precision_score(
        y_val, predictions, zero_division=0
    )
    recall = recall_score(
        y_val, predictions, zero_division=0
    )
    f1 = f1_score(
        y_val, predictions, zero_division=0
    )

    tn, fp, fn, tp = confusion_matrix(
        y_val, predictions, labels=[0, 1]
    ).ravel()

    print(f"\nThreshold: {threshold:.2f}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1-score:  {f1:.3f}")
    print(f"True positives: {tp}")
    print(f"False alarms:   {fp}")
    print(f"Missed failures:{fn}")
