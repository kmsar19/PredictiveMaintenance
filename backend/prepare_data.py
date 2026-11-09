
import pandas as pd
from sklearn.model_selection import train_test_split

# Load dataset
df = pd.read_csv("backend/data/ai4i2020.csv")

# Target column
target = "Machine failure"

# Remove identifiers and failure-subtype columns
columns_to_drop = [
    "UDI",
    "Product ID",
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF"
]

X = df.drop(columns=columns_to_drop)
y = df[target]

# Split: 80% training, 20% temporary
X_train, X_temp, y_train, y_temp = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Split temporary data equally into validation and testing
X_val, X_test, y_val, y_test = train_test_split(
    X_temp,
    y_temp,
    test_size=0.50,
    random_state=42,
    stratify=y_temp
)

# Save the prepared datasets
X_train.to_csv("backend/data/X_train.csv", index=False)
X_val.to_csv("backend/data/X_val.csv", index=False)
X_test.to_csv("backend/data/X_test.csv", index=False)

y_train.to_csv("backend/data/y_train.csv", index=False)
y_val.to_csv("backend/data/y_val.csv", index=False)
y_test.to_csv("backend/data/y_test.csv", index=False)

# Display results
print("========== DATA PREPARATION COMPLETE ==========")
print("Training records:", len(X_train))
print("Validation records:", len(X_val))
print("Testing records:", len(X_test))

print("\nFailure distribution:")
print("Training:\n", y_train.value_counts())
print("Validation:\n", y_val.value_counts())
print("Testing:\n", y_test.value_counts())

print("\nInput features:")
print(list(X.columns))
