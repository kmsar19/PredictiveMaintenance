import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Predictive Maintenance API",
    description="AI-based machine failure prediction",
    version="1.2"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "predictive_maintenance_model.joblib"
DATABASE_PATH = BASE_DIR / "predictions.db"

DATABASE_URL = os.getenv("DATABASE_URL")
THRESHOLD = 0.40

model = joblib.load(MODEL_PATH)


@contextmanager
def database_connection():
    if DATABASE_URL:
        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )
    else:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row

    try:
        yield connection
    finally:
        connection.close()


def initialize_database():
    with database_connection() as connection:
        if DATABASE_URL:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    machine_type TEXT NOT NULL,
                    air_temperature DOUBLE PRECISION NOT NULL,
                    process_temperature DOUBLE PRECISION NOT NULL,
                    rotational_speed DOUBLE PRECISION NOT NULL,
                    torque DOUBLE PRECISION NOT NULL,
                    tool_wear DOUBLE PRECISION NOT NULL,
                    prediction INTEGER NOT NULL,
                    machine_status TEXT NOT NULL,
                    failure_probability DOUBLE PRECISION NOT NULL
                )
            """)
        else:
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
        "database": "PostgreSQL" if DATABASE_URL else "SQLite",
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
    timestamp = datetime.now(timezone.utc)

    with database_connection() as connection:

        values = (
            timestamp if DATABASE_URL else timestamp.isoformat(),
            data.machine_type,
            data.air_temperature,
            data.process_temperature,
            data.rotational_speed,
            data.torque,
            data.tool_wear,
            prediction,
            status,
            probability * 100
        )

        if DATABASE_URL:
            cursor = connection.execute("""
                INSERT INTO predictions (
                    timestamp, machine_type, air_temperature,
                    process_temperature, rotational_speed, torque,
                    tool_wear, prediction, machine_status,
                    failure_probability
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, values)

            prediction_id = cursor.fetchone()["id"]

        else:
            cursor = connection.execute("""
                INSERT INTO predictions (
                    timestamp, machine_type, air_temperature,
                    process_temperature, rotational_speed, torque,
                    tool_wear, prediction, machine_status,
                    failure_probability
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)

            prediction_id = cursor.lastrowid

        connection.commit()

    return {
        "id": prediction_id,
        "timestamp": timestamp.isoformat(),
        "machine_status": status,
        "failure_prediction": prediction,
        "failure_probability": round(probability * 100, 2),
        "threshold": THRESHOLD
    }


@app.get("/predictions")
def get_predictions(limit: int = 100):

    limit = max(1, min(limit, 500))

    with database_connection() as connection:

        if DATABASE_URL:
            rows = connection.execute("""
                SELECT *
                FROM predictions
                ORDER BY id DESC
                LIMIT %s
            """, (limit,)).fetchall()
        else:
            rows = connection.execute("""
                SELECT *
                FROM predictions
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)).fetchall()

    return [dict(row) for row in rows]


@app.get("/statistics")
def get_statistics():

    with database_connection() as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS total FROM predictions"
        ).fetchone()["total"]

        failures = connection.execute(
            "SELECT COUNT(*) AS failures FROM predictions WHERE prediction = 1"
        ).fetchone()["failures"]

    return {
        "total_predictions": total,
        "failure_predictions": failures,
        "normal_predictions": total - failures
    }
