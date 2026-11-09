
import pandas as pd
import json

df = pd.read_csv("backend/data/ai4i2020.csv")

failure = df[df["Machine failure"] == 1].iloc[0]

sample = {
    "machine_type": str(failure["Type"]),
    "air_temperature": float(failure["Air temperature [K]"]),
    "process_temperature": float(failure["Process temperature [K]"]),
    "rotational_speed": int(failure["Rotational speed [rpm]"]),
    "torque": float(failure["Torque [Nm]"]),
    "tool_wear": float(failure["Tool wear [min]"])
}

print("Known failure sample:")
print(json.dumps(sample, indent=4))
