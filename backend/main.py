
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import os
import sqlite3
from datetime import datetime

app = FastAPI(title="INNOVATRIX Fake Job Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "job_model.pkl")
DB_PATH = os.path.join(BASE_DIR, "scans.db")

model = joblib.load(MODEL_PATH)


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_text TEXT,
                label TEXT,
                risk_level TEXT,
                created_at TEXT
            )
        """)


init_db()


@app.get("/")
def home():
    return {"message": "INNOVATRIX backend is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(data: dict):
    job_text = data.get("job_text", "").strip()

    if not job_text:
        return {"error": "Please enter a job description."}

    prediction = int(model.predict([job_text])[0])
    probabilities = model.predict_proba([job_text])[0]
    classes = [int(c) for c in model.classes_]
    score = float(probabilities[classes.index(1)])

    if prediction == 1:
        label = "suspicious"
        risk = "High"
    else:
        label = "lower_risk"
        risk = "Lower"

    warnings = []
    warning_phrases = [
        "registration fee",
        "security deposit",
        "pay money",
        "guaranteed job",
        "no interview",
    ]

    lower_text = job_text.lower()

    for phrase in warning_phrases:
        if phrase in lower_text:
            warnings.append(
                f"Suspicious phrase detected: {phrase}"
            )

    if not warnings:
        warnings.append(
            "No listed warning phrase found. Verify the employer independently."
        )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO scans "
            "(job_text, label, risk_level, created_at) "
            "VALUES (?, ?, ?, ?)",
            (job_text, label, risk, datetime.now().isoformat()),
        )

    return {
        "label": label,
        "risk_level": risk,
        "model_score": round(score, 3),
        "warning_signals": warnings,
        "verification_tips": [
            "Check the official company careers website.",
            "Verify the recruiter email and company identity.",
            "Do not pay money to obtain a job or internship.",
        ],
        "notice": "Preliminary AI assessment only; not proof of fraud.",
    }


@app.get("/history")
def history():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, job_text, label, risk_level, created_at "
            "FROM scans ORDER BY id DESC LIMIT 20"
        ).fetchall()

    return [
        {
            "id": row[0],
            "job_text": row[1],
            "label": row[2],
            "risk_level": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]
@app.delete("/history")
def clear_history():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM scans")

    return {"message": "Scan history cleared successfully"}