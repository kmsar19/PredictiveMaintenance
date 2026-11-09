
import pandas as pd
import joblib

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

# Load the saved model
model = joblib.load(
    "backend/models/predictive_maintenance_model.joblib"
)

# Load untouched test data
X_test = pd.read_csv("backend/data/X_test.csv")
y_test = pd.read_csv("backend/data/y_test.csv").squeeze()

# Selected threshold from validation analysis
THRESHOLD = 0.40

# Predict failure probabilities
probabilities = model.predict_proba(X_test)[:, 1]

# Apply selected threshold
predictions = (probabilities >= THRESHOLD).astype(int)

# Calculate evaluation metrics
print("\n========== FINAL TEST RESULTS ==========")
print("Threshold:", THRESHOLD)
print("Accuracy :", accuracy_score(y_test, predictions))
print("Precision:", precision_score(y_test, predictions, zero_division=0))
print("Recall   :", recall_score(y_test, predictions, zero_division=0))
print("F1 Score :", f1_score(y_test, predictions, zero_division=0))
print("ROC-AUC  :", roc_auc_score(y_test, probabilities))

print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    target_names=["No Failure", "Failure"],
    zero_division=0
))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))

# Save final evaluation results
results = pd.DataFrame({
    "Actual": y_test,
    "Predicted": predictions,
    "Failure Probability": probabilities
})

results.to_csv("outputs/test_predictions.csv", index=False)

print("\nTest predictions saved to outputs/test_predictions.csv")
