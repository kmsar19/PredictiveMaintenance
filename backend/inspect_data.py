import pandas as pd

# Load dataset
df = pd.read_csv("backend/data/ai4i2020.csv")

print("\n========== DATASET OVERVIEW ==========")
print("Shape:", df.shape)

print("\n========== COLUMN NAMES ==========")
for column in df.columns:
    print(column)

print("\n========== DATA TYPES ==========")
print(df.dtypes)

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum())

print("\n========== DUPLICATE RECORDS ==========")
print(df.duplicated().sum())

print("\n========== MACHINE FAILURE DISTRIBUTION ==========")
print(df["Machine failure"].value_counts())

print("\n========== FAILURE PERCENTAGE ==========")
print(df["Machine failure"].value_counts(normalize=True) * 100)

print("\n========== MACHINE TYPE DISTRIBUTION ==========")
print(df["Type"].value_counts())