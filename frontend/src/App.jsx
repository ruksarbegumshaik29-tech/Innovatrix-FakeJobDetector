
import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [jobText, setJobText] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyMessage, setHistoryMessage] = useState("");

  // Screenshot OCR states
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState("");
  const [extractedText, setExtractedText] = useState("");
  const [ocrLoading, setOcrLoading] = useState(false);

  const API = "https://innovatrix-fakejobdetector.onrender.com";

  async function loadHistory() {
    setHistoryLoading(true);
    setHistoryMessage("");

    try {
      const response = await fetch(`${API}/history`);

      if (!response.ok) {
        throw new Error("History unavailable");
      }

      const data = await response.json();
      setHistory(data);
      setHistoryMessage("History updated successfully.");
    } catch {
      setError(
        "Backend connect avvaledu. Backend server run avutundo check cheyyi."
      );
    } finally {
      setHistoryLoading(false);
    }
  }

  async function clearHistory() {
    const confirmed = window.confirm(
      "Are you sure you want to delete all scan history?"
    );

    if (!confirmed) return;

    setError("");
    setHistoryMessage("");

    try {
      const response = await fetch(`${API}/history`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Could not clear history");
      }

      setHistory([]);
      setResult(null);
      setHistoryMessage("All scan history cleared.");
    } catch {
      setError("History clear cheyyalekapoyam. Backend check cheyyi.");
    }
  }

  function handleImageChange(event) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    const allowedTypes = ["image/png", "image/jpeg", "image/webp"];

    if (!allowedTypes.includes(file.type)) {
      setError("PNG, JPG, JPEG, or WEBP image matrame upload cheyyi.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("Image size 5 MB kanna takkuva undali.");
      return;
    }

    setError("");
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setExtractedText("");
    setResult(null);
  }

  async function extractTextFromImage() {
    if (!imageFile) {
      setError("Mundu job screenshot upload cheyyi.");
      return;
    }

    setOcrLoading(true);
    setError("");
    setHistoryMessage("");
    setExtractedText("");

    try {
      const formData = new FormData();
      formData.append("file", imageFile);

      const response = await fetch(`${API}/extract-text`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || data.error || "Text extraction failed."
        );
      }

      setExtractedText(data.text || "");

      if (!data.text?.trim()) {
        throw new Error("Screenshot nunchi readable text dorakaledu.");
      }

      setHistoryMessage(
        "Text extracted successfully! Analyze cheyyadaniki mundu review cheyyi."
      );
    } catch (err) {
      setError(
        err.message ||
          "OCR failed. Backend lo Tesseract OCR configured undho check cheyyi."
      );
    } finally {
      setOcrLoading(false);
    }
  }

  async function analyzeText(text) {
    if (!text.trim() || text.trim().length < 5) {
      setError("Please enter at least 5 characters of job description.");
      return;
    }

    setLoading(true);
    setError("");
    setHistoryMessage("");
    setResult(null);

    try {
      const response = await fetch(`${API}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_text: text.trim() }),
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        throw new Error(data.detail || data.error || "Analysis failed");
      }

      setResult(data);
      await loadHistory();
    } catch (err) {
      setError(err.message || "Could not connect to backend.");
    } finally {
      setLoading(false);
    }
  }

  async function analyzeJob(event) {
    event.preventDefault();
    await analyzeText(jobText);
  }

  async function analyzeExtractedText() {
    await analyzeText(extractedText);
  }

  function downloadReport() {
    if (!result) return;

    const report = `
INNOVATRIX - AI Career Safety
JOB ANALYSIS REPORT
----------------------------
Date: ${new Date().toLocaleString()}

Risk Level: ${result.risk_level}
Model Classification: ${result.label}
Model Fake-Job Score: ${(result.model_score * 100).toFixed(1)}%

WARNING SIGNALS:
${(result.warning_signals || [])
  .map((item) => "- " + item)
  .join("\n")}

VERIFICATION TIPS:
${(result.verification_tips || [])
  .map((item) => "- " + item)
  .join("\n")}

Notice: ${result.notice}

This is a preliminary AI assessment, not proof of fraud.
Always verify the employer independently.
`;

    const blob = new Blob([report], {
      type: "text/plain;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "INNOVATRIX_Job_Analysis_Report.txt";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    return () => {
      if (imagePreview) URL.revokeObjectURL(imagePreview);
    };
  }, [imagePreview]);

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand-mark">I</div>
        <div>
          <h2>INNOVATRIX</h2>
          <p>AI Career Safety</p>
        </div>
      </header>

      <section className="hero">
        <span className="eyebrow">YOUR CAREER. YOUR SAFETY.</span>

        <h1>
          Is that job offer <span>really genuine?</span>
        </h1>

        <p className="subtitle">
          Analyze job and internship descriptions for suspicious signals
          before you apply.
        </p>

        <form className="analyzer" onSubmit={analyzeJob}>
          <label htmlFor="job">Paste job or internship description</label>

          <textarea
            id="job"
            value={jobText}
            onChange={(event) => setJobText(event.target.value)}
            placeholder="Paste the complete job description here..."
            required
            minLength={5}
          />

          <button type="submit" disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Job →"}
          </button>
        </form>

        <section className="analyzer" style={{ marginTop: "24px" }}>
          <h2>Analyze Job Screenshot</h2>
          <p className="subtitle">
            Upload a screenshot of a job posting. OCR will extract its text
            so you can review and analyze it.
          </p>

          <label htmlFor="jobScreenshot">
            Choose screenshot (PNG, JPG, WEBP · Max 5 MB)
          </label>

          <input
            id="jobScreenshot"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={handleImageChange}
          />

          {imagePreview && (
            <div style={{ marginTop: "16px" }}>
              <p>Screenshot preview</p>
              <img
                src={imagePreview}
                alt="Uploaded job posting screenshot"
                style={{
                  display: "block",
                  maxWidth: "100%",
                  maxHeight: "350px",
                  objectFit: "contain",
                  borderRadius: "10px",
                  marginBottom: "12px",
                }}
              />

              <button
                type="button"
                onClick={extractTextFromImage}
                disabled={ocrLoading || loading}
              >
                {ocrLoading ? "Extracting Text..." : "Extract Text from Screenshot"}
              </button>
            </div>
          )}

          {extractedText && (
            <div style={{ marginTop: "20px" }}>
              <label htmlFor="extractedText">
                Extracted Text (You can edit before analyzing)
              </label>

              <textarea
                id="extractedText"
                value={extractedText}
                onChange={(event) => setExtractedText(event.target.value)}
                rows={10}
                style={{ marginTop: "8px" }}
              />

              <button
                type="button"
                onClick={analyzeExtractedText}
                disabled={loading || ocrLoading || extractedText.trim().length < 5}
              >
                {loading ? "Analyzing..." : "Analyze Extracted Text →"}
              </button>
            </div>
          )}
        </section>

        {error && <p className="error">{error}</p>}

        {result && (
          <section className="result">
            <h2>Analysis Result</h2>

            <p className={result.risk_level === "High" ? "high" : "low"}>
              {result.risk_level} Risk
            </p>

            <p>Model classification: {result.label}</p>

            <p>
              Model fake-job score:{" "}
              {(result.model_score * 100).toFixed(1)}%
            </p>

            <p className="notice">
              Higher scores indicate stronger signals associated with fake
              jobs. This score is not a guarantee of fraud.
            </p>

            <h3>Warning Signals</h3>
            <ul>
              {(result.warning_signals || []).map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>

            <h3>Verification Tips</h3>
            <ul>
              {(result.verification_tips || []).map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>

            <p className="notice">{result.notice}</p>

            <button type="button" onClick={downloadReport}>
              Download Analysis Report ↓
            </button>
          </section>
        )}

        <section className="history">
          <div className="history-heading">
            <div>
              <span className="eyebrow">YOUR ACTIVITY</span>
              <h2>Recent Scan History</h2>
            </div>

            <div className="history-actions">
              <button
                type="button"
                onClick={loadHistory}
                disabled={historyLoading}
              >
                {historyLoading ? "Refreshing..." : "Refresh History"}
              </button>

              <button
                type="button"
                onClick={clearHistory}
                disabled={historyLoading}
              >
                Clear History
              </button>
            </div>
          </div>

          {historyMessage && <p>{historyMessage}</p>}

          {history.length === 0 ? (
            <p>No scans yet. Analyze a job to see it here.</p>
          ) : (
            history.map((item) => (
              <article className="history-item" key={item.id}>
                <div>
                  <strong>
                    {item.job_text.length > 90
                      ? item.job_text.slice(0, 90) + "..."
                      : item.job_text}
                  </strong>

                  <p>{new Date(item.created_at).toLocaleString()}</p>
                </div>

                <span
                  className={item.risk_level === "High" ? "high" : "low"}
                >
                  {item.risk_level}
                </span>
              </article>
            ))
          )}
        </section>

        <p className="disclaimer">
          AI screening is preliminary. Always verify employers independently.
        </p>
      </section>
    </main>
  );
}

export default App;
