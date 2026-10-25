
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

# File paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "fake_job_postings.csv"
MODEL_PATH = BASE_DIR / "job_model.pkl"

# Load dataset
df = pd.read_csv(DATA_PATH).fillna("")

# Select job text columns
text_columns = [
    "title",
    "company_profile",
    "description",
    "requirements",
    "benefits",
]

# Combine job details
df["job_text"] = df[text_columns].astype(str).agg(" ".join, axis=1)

X = df["job_text"]
y = df["fraudulent"].astype(int)

# Split dataset into training and testing data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

# Create ML pipeline
model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            stop_words="english",
            max_features=100000,
            ngram_range=(1, 2),
            min_df=2,
        ),
    ),
    (
        "classifier",
        LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        ),
    ),
])

# Train model
print("Training INNOVATRIX model...")
model.fit(X_train, y_train)

# Make predictions on test data
predictions = model.predict(X_test)

# Display confusion matrix
cm = confusion_matrix(y_test, predictions, labels=[0, 1])

print("\nINNOVATRIX Confusion Matrix")
print("Rows = Actual | Columns = Predicted")
print("Labels: 0 = Genuine, 1 = Fake")
print(cm)

# Display classification report
print("\nINNOVATRIX Model Evaluation")
print(
    classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["Genuine (0)", "Fake (1)"],
        zero_division=0,
    )
)

# Save trained model
joblib.dump(model, MODEL_PATH)

print(f"Trained model saved to: {MODEL_PATH}")
