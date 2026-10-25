
import io
import os
import sqlite3
from datetime import datetime

import joblib
import pytesseract
from PIL import Image, ImageOps
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware


# Windows local Tesseract path
# Render lo environment variable set cheyyachu
TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


app = FastAPI(title="INNOVATRIX Fake Job Detector")


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://innovatrix-fakejob-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "job_model.pkl")
DB_PATH = os.path.join(BASE_DIR, "scans.db")


# Load existing ML model
model = joblib.load(MODEL_PATH)


# Database initialization
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


# Home
@app.get("/")
def home():
    return {"message": "INNOVATRIX backend is running!"}


# Health check
@app.get("/health")
def health():
    return {"status": "ok"}


# Existing job analysis API
@app.post("/analyze")
def analyze(data: dict):
    job_text = data.get("job_text", "").strip()

    if not job_text:
        raise HTTPException(
            status_code=400,
            detail="Please enter a job description."
        )

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
            "No listed warning phrase found. "
            "Verify the employer independently."
        )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO scans
            (job_text, label, risk_level, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                job_text,
                label,
                risk,
                datetime.now().isoformat(),
            ),
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
        "notice": (
            "Preliminary AI assessment only; "
            "not proof of fraud."
        ),
    }


# NEW: Screenshot upload + OCR text extraction
@app.post("/extract-text")
async def extract_text_from_image(
    file: UploadFile = File(...)
):
    allowed_types = {
        "image/png",
        "image/jpeg",
        "image/webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Upload a PNG, JPG, JPEG, or WEBP screenshot."
        )

    try:
        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded image is empty."
            )

        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Image size must be 5 MB or smaller."
            )

        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image).convert("RGB")

        extracted_text = pytesseract.image_to_string(
            image,
            lang="eng"
        ).strip()

        if not extracted_text:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text found. "
                    "Try a clearer screenshot."
                )
            )

        return {
            "text": extracted_text,
            "filename": file.filename,
        }

    except HTTPException:
        raise

    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=(
                "Tesseract OCR is unavailable. "
                "Check the server OCR installation."
            )
        )

    except Exception:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not read this image. "
                "Please try another screenshot."
            )
        )

    finally:
        await file.close()


# Existing recent scan history
@app.get("/history")
def history():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT id, job_text, label, risk_level, created_at
            FROM scans
            ORDER BY id DESC
            LIMIT 20
            """
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


# Existing clear history
@app.delete("/history")
def clear_history():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM scans")

    return {
        "message": "Scan history cleared successfully"
    }
