from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import sqlite3
from datetime import datetime, timezone

app = FastAPI(
    title="Predictive Maintenance API",
    description="AI-based machine failure prediction",
    version="1.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

MODEL_PATH = "backend/models/predictive_maintenance_model.joblib"
DATABASE_PATH = "backend/predictions.db"
THRESHOLD = 0.40

model = joblib.load(MODEL_PATH)


# Create the database and table automatically
def initialize_database():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                machine_type TEXT NOT NULL,
                air_temperature REAL NOT NULL,
                process_temperature REAL NOT NULL,
                rotational_speed REAL NOT NULL,
                torque REAL NOT NULL,
                tool_wear REAL NOT NULL,
                prediction INTEGER NOT NULL,
                machine_status TEXT NOT NULL,
                failure_probability REAL NOT NULL
            )
        """)
        connection.commit()


initialize_database()


class MachineData(BaseModel):
    machine_type: str = Field(pattern="^[LMH]$")
    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float


@app.get("/")
def home():
    return {
        "message": "Predictive Maintenance API is running",
        "model": "Random Forest",
        "status": "Active"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict(data: MachineData):

    input_data = pd.DataFrame([{
        "Type": data.machine_type,
        "Air temperature [K]": data.air_temperature,
        "Process temperature [K]": data.process_temperature,
        "Rotational speed [rpm]": data.rotational_speed,
        "Torque [Nm]": data.torque,
        "Tool wear [min]": data.tool_wear
    }])

    probability = float(model.predict_proba(input_data)[0][1])
    prediction = int(probability >= THRESHOLD)

    status = "Failure Risk" if prediction == 1 else "Normal"
    timestamp = datetime.now(timezone.utc).isoformat()

    # Save prediction permanently in SQLite
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute("""
            INSERT INTO predictions (
                timestamp,
                machine_type,
                air_temperature,
                process_temperature,
                rotational_speed,
                torque,
                tool_wear,
                prediction,
                machine_status,
                failure_probability
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            data.machine_type,
            data.air_temperature,
            data.process_temperature,
            data.rotational_speed,
            data.torque,
            data.tool_wear,
            prediction,
            status,
            probability * 100
        ))

        prediction_id = cursor.lastrowid
        connection.commit()

    return {
        "id": prediction_id,
        "timestamp": timestamp,
        "machine_status": status,
        "failure_prediction": prediction,
        "failure_probability": round(probability * 100, 2),
        "threshold": THRESHOLD
    }


@app.get("/predictions")
def get_predictions(limit: int = 100):

    limit = max(1, min(limit, 500))

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT *
            FROM predictions
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [dict(row) for row in rows]


@app.get("/statistics")
def get_statistics():

    with sqlite3.connect(DATABASE_PATH) as connection:
        total = connection.execute(
            "SELECT COUNT(*) FROM predictions"
        ).fetchone()[0]

        failures = connection.execute(
            "SELECT COUNT(*) FROM predictions WHERE prediction = 1"
        ).fetchone()[0]

    return {
        "total_predictions": total,
        "failure_predictions": failures,
        "normal_predictions": total - failures
    }
