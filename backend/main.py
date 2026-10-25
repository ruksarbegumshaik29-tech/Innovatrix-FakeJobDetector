
import io
import os
import sqlite3
from datetime import datetime

import joblib
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware


# --------------------------------------------------
# TESSERACT OCR CONFIGURATION
# --------------------------------------------------

TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

OCR_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
OCR_MAX_DIMENSION = 1800
OCR_FIRST_TIMEOUT = 20
OCR_RETRY_TIMEOUT = 15


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(title="INNOVATRIX Fake Job Detector")


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

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


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "job_model.pkl")
DB_PATH = os.path.join(BASE_DIR, "scans.db")


# --------------------------------------------------
# LOAD MACHINE LEARNING MODEL
# --------------------------------------------------

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"ML model not found at: {MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

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


# --------------------------------------------------
# HOME ROUTE
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "INNOVATRIX backend is running!"
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# --------------------------------------------------
# JOB DESCRIPTION ANALYSIS
# --------------------------------------------------

@app.post("/analyze")
def analyze(data: dict):
    job_text = data.get("job_text", "").strip()

    if not job_text:
        raise HTTPException(
            status_code=400,
            detail="Please enter a job description."
        )

    try:
        prediction = int(model.predict([job_text])[0])

        probabilities = model.predict_proba([job_text])[0]
        classes = [int(c) for c in model.classes_]

        if 1 not in classes:
            raise HTTPException(
                status_code=500,
                detail="The ML model does not contain the suspicious class."
            )

        score = float(probabilities[classes.index(1)])

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Job analysis failed. Please try again."
        )

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


# --------------------------------------------------
# OCR IMAGE PREPROCESSING
# --------------------------------------------------

def prepare_ocr_image(image: Image.Image) -> Image.Image:
    """
    Prepare screenshots for OCR:
    - Convert to grayscale
    - Resize excessively large images
    - Improve contrast
    - Apply light sharpening
    """

    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    image.thumbnail(
        (OCR_MAX_DIMENSION, OCR_MAX_DIMENSION),
        Image.Resampling.LANCZOS,
    )

    processed = ImageOps.grayscale(image)
    processed = ImageOps.autocontrast(processed)
    processed = processed.filter(ImageFilter.SHARPEN)

    return processed


# --------------------------------------------------
# OCR TEXT EXTRACTION
# --------------------------------------------------

@app.post("/extract-text")
async def extract_text_from_image(
    file: UploadFile = File(...)
):
    allowed_types = {
        "image/png",
        "image/jpeg",
        "image/webp",
    }

    try:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Upload a PNG, JPG, JPEG, or WEBP screenshot."
                ),
            )

        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded image is empty.",
            )

        if len(image_bytes) > OCR_MAX_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Image size must be 5 MB or smaller.",
            )

        try:
            with Image.open(io.BytesIO(image_bytes)) as source:
                source.load()
                image = source.copy()

        except Exception:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid or unsupported image. "
                    "Please upload another screenshot."
                ),
            )

        processed = prepare_ocr_image(image)

        # First pass: useful for screenshots containing
        # text blocks in different positions.
        try:
            extracted_text = pytesseract.image_to_string(
                processed,
                lang="eng",
                config="--oem 3 --psm 11",
                timeout=OCR_FIRST_TIMEOUT,
            ).strip()

        except RuntimeError:
            extracted_text = ""

        # Retry only if the first pass found very little text.
        if len(extracted_text) < 15:
            try:
                retry_text = pytesseract.image_to_string(
                    processed,
                    lang="eng",
                    config="--oem 3 --psm 6",
                    timeout=OCR_RETRY_TIMEOUT,
                ).strip()

                if len(retry_text) > len(extracted_text):
                    extracted_text = retry_text

            except RuntimeError:
                pass

        if not extracted_text:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text found. "
                    "Try a clearer screenshot with larger text."
                ),
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
            ),
        )

    except Exception:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not read this image. "
                "Please try another screenshot."
            ),
        )

    finally:
        await file.close()


# --------------------------------------------------
# RECENT SCAN HISTORY
# --------------------------------------------------

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


# --------------------------------------------------
# CLEAR SCAN HISTORY
# --------------------------------------------------

@app.delete("/history")
def clear_history():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM scans")

    return {
        "message": "Scan history cleared successfully"
    }
