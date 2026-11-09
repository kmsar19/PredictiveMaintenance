
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import confusion_matrix, roc_curve, auc

# Load model and test data
model = joblib.load(
    "backend/models/predictive_maintenance_model.joblib"
)

X_test = pd.read_csv("backend/data/X_test.csv")
y_test = pd.read_csv("backend/data/y_test.csv").squeeze()

# Use the selected threshold
threshold = 0.40

probabilities = model.predict_proba(X_test)[:, 1]
predictions = (probabilities >= threshold).astype(int)

# Create output directory if needed
import os
os.makedirs("outputs", exist_ok=True)

# 1. Confusion Matrix
cm = confusion_matrix(y_test, predictions)

plt.figure(figsize=(6, 5))
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=["No Failure", "Failure"],
    yticklabels=["No Failure", "Failure"]
)
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.savefig("outputs/confusion_matrix.png", dpi=300)
plt.close()

# 2. ROC Curve
fpr, tpr, _ = roc_curve(y_test, probabilities)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(6, 5))
plt.plot(fpr, tpr, label=f"Random Forest (AUC = {roc_auc:.3f})")
plt.plot([0, 1], [0, 1], linestyle="--")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")
plt.legend()
plt.tight_layout()
plt.savefig("outputs/roc_curve.png", dpi=300)
plt.close()

# 3. Feature Importance
preprocessor = model.named_steps["preprocessor"]
classifier = model.named_steps["classifier"]

feature_names = preprocessor.get_feature_names_out()
importance = classifier.feature_importances_

importance_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importance
}).sort_values("Importance", ascending=False)

plt.figure(figsize=(9, 5))
sns.barplot(
    data=importance_df,
    x="Importance",
    y="Feature"
)
plt.title("Feature Importance - Random Forest")
plt.tight_layout()
plt.savefig("outputs/feature_importance.png", dpi=300)
plt.close()

# 4. Actual vs Predicted Distribution
comparison = pd.DataFrame({
    "Actual": y_test.value_counts().sort_index(),
    "Predicted": pd.Series(predictions).value_counts().sort_index()
}).fillna(0)

comparison.index = ["No Failure", "Failure"]

comparison.plot(kind="bar", figsize=(7, 5))
plt.title("Actual vs Predicted Failure Distribution")
plt.xlabel("Machine Status")
plt.ylabel("Number of Records")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("outputs/prediction_distribution.png", dpi=300)
plt.close()

print("All performance graphs generated successfully!")

print("\nSaved files:")
print("outputs/confusion_matrix.png")
print("outputs/roc_curve.png")
print("outputs/feature_importance.png")
print("outputs/prediction_distribution.png")

