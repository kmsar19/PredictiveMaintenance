
import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

# Load training and validation data
X_train = pd.read_csv("backend/data/X_train.csv")
X_val = pd.read_csv("backend/data/X_val.csv")

y_train = pd.read_csv("backend/data/y_train.csv").squeeze()
y_val = pd.read_csv("backend/data/y_val.csv").squeeze()

# Identify categorical and numerical columns
categorical_features = ["Type"]
numerical_features = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]"
]

# Convert machine type into numerical features
preprocessor = ColumnTransformer(
    transformers=[
        ("category", OneHotEncoder(handle_unknown="ignore"),
         categorical_features),
        ("numbers", "passthrough", numerical_features)
    ]
)

# Create the Random Forest model
model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=400,
        class_weight="balanced",
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    ))
])

# Train the model
print("Training model...")
model.fit(X_train, y_train)

# Validate the model
predictions = model.predict(X_val)
probabilities = model.predict_proba(X_val)[:, 1]

# Calculate evaluation metrics
print("\n========== VALIDATION RESULTS ==========")
print("Accuracy :", accuracy_score(y_val, predictions))
print("Precision:", precision_score(y_val, predictions, zero_division=0))
print("Recall   :", recall_score(y_val, predictions, zero_division=0))
print("F1 Score :", f1_score(y_val, predictions, zero_division=0))
print("ROC-AUC  :", roc_auc_score(y_val, probabilities))

print("\nClassification Report:")
print(classification_report(
    y_val, predictions, target_names=["No Failure", "Failure"],
    zero_division=0
))

print("\nConfusion Matrix:")
print(confusion_matrix(y_val, predictions))

# Save trained model
joblib.dump(model, "backend/models/predictive_maintenance_model.joblib")

print("\nModel saved successfully!")
