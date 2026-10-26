            detail="Job analysis failed. Please try again.",
        )

    if prediction == 1:
        label = "suspicious"
        risk = "High"
    else:
        label = "lower_risk"
        risk = "Lower"

    warning_phrases = [
        "registration fee",
        "security deposit",
        "pay money",
        "guaranteed job",
        "no interview",
    ]

    lower_text = job_text.lower()

    warnings = [
        f"Suspicious phrase detected: {phrase}"
        for phrase in warning_phrases
        if phrase in lower_text
    ]

    if not warnings:
        warnings.append(
            "No listed warning phrase found. "
            "Verify the employer independently."
        )

    try:
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
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not save scan history.",
        )

    return {
        "label": label,
        "risk_level": risk,
        "model_score": round(score, 3),
        "warning_signals": warnings,
        "verification_tips": [
            "Check the official company careers website.",
            "Verify the recruiter email and company identity.",
            "Never pay money to obtain a job or internship.",
        ],
        "notice": (
            "Preliminary AI assessment only; "
            "not proof of fraud."
        ),
    }


# ==================================================
# OCR IMAGE PREPROCESSING
# ==================================================

def prepare_ocr_image(image: Image.Image) -> Image.Image:
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


# ==================================================
# EXTRACT TEXT FROM SCREENSHOT
# ==================================================

@app.post("/extract-text")
async def extract_text_from_image(
    file: UploadFile = File(...),
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
                    "Upload a PNG, JPG, JPEG, "
                    "or WEBP screenshot."
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
            with Image.open(
                io.BytesIO(image_bytes)
            ) as source:
                source.load()
                image = source.copy()

        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid image. Please upload "
                    "a clear screenshot."
                ),
            )

        processed = prepare_ocr_image(image)

        # Temporary diagnostic logs for Render OCR troubleshooting.
        print("OCR IMAGE SIZE:", image.size, flush=True)
        print("OCR PROCESSED SIZE:", processed.size, flush=True)
        print("TESSERACT PATH:", pytesseract.pytesseract.tesseract_cmd, flush=True)
        try:
            print("TESSERACT VERSION:", pytesseract.get_tesseract_version(), flush=True)
        except Exception as exc:
            print("TESSERACT VERSION ERROR:", repr(exc), flush=True)

        extracted_text = ""