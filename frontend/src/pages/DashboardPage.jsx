import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { analyzeResume, fetchDashboard } from "../api/client";
import ScoreGauge from "../components/ScoreGauge";
import "./DashboardPage.css";

export default function DashboardPage() {
  const { email, logout } = useAuth();
  const navigate = useNavigate();

  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const [analyzing, setAnalyzing] = useState(false);
  const [formError, setFormError] = useState("");

  const [candidates, setCandidates] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  const loadDashboard = useCallback(async () => {
    setLoadingList(true);
    try {
      const data = await fetchDashboard();
      setCandidates(data);
    } catch (err) {
      if (err?.response?.status === 401) {
        logout();
        navigate("/");
      }
    } finally {
      setLoadingList(false);
    }
  }, [logout, navigate]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  function handleFileChange(selected) {
    if (selected && selected.type === "application/pdf") {
      setFile(selected);
      setFormError("");
    } else {
      setFormError("Please upload a PDF resume.");
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragActive(false);
    const dropped = e.dataTransfer.files?.[0];
    handleFileChange(dropped);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");

    if (!file) {
      setFormError("Attach a resume PDF to scan.");
      return;
    }
    if (!jobDescription.trim()) {
      setFormError("Paste a job description so the scan has something to match against.");
      return;
    }

    setAnalyzing(true);
    try {
      await analyzeResume({ file, jobDescription, jobTitle });
      setFile(null);
      await loadDashboard();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setFormError(typeof detail === "string" ? detail : "Scan failed. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="dash-screen">
      <header className="dash-header">
        <div>
          <div className="dash-eyebrow mono">RESUME ANALYZER</div>
          <h1 className="dash-title">Candidate screening</h1>
        </div>
        <div className="dash-header-right">
          <span className="dash-user mono">{email}</span>
          <button className="btn-ghost" onClick={() => { logout(); navigate("/"); }}>
            Sign out
          </button>
        </div>
      </header>

      <main className="dash-grid">
        {/* --- Upload / scan panel --- */}
        <section className="panel scan-panel">
          <h2 className="panel-title">New scan</h2>
          <p className="panel-sub">
            Upload a resume and the job description it should be evaluated against.
          </p>

          <form onSubmit={handleSubmit} className="scan-form">
            <label className="field">
              <span className="field-label mono">JOB TITLE</span>
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g. Backend Engineer"
              />
            </label>

            <label className="field">
              <span className="field-label mono">JOB DESCRIPTION</span>
              <textarea
                rows={7}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the full job description here..."
              />
            </label>

            <div
              className={`dropzone ${dragActive ? "drag-active" : ""} ${file ? "has-file" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              onClick={() => document.getElementById("resume-file-input").click()}
            >
              <input
                id="resume-file-input"
                type="file"
                accept="application/pdf"
                hidden
                onChange={(e) => handleFileChange(e.target.files?.[0])}
              />
              {file ? (
                <span className="mono">{file.name}</span>
              ) : (
                <span>Drop resume PDF here, or click to browse</span>
              )}
            </div>

            {formError && <div className="form-error">{formError}</div>}

            <button type="submit" className="btn-primary" disabled={analyzing}>
              {analyzing ? "Scanning..." : "Run scan"}
            </button>
          </form>
        </section>

        {/* --- Ranked candidates --- */}
        <section className="panel results-panel">
          <div className="results-header">
            <h2 className="panel-title">Ranked candidates</h2>
            <span className="results-count mono">{candidates.length} scanned</span>
          </div>

          {loadingList ? (
            <div className="empty-state">Loading...</div>
          ) : candidates.length === 0 ? (
            <div className="empty-state">
              No candidates scanned yet. Run a scan to see ranked results here.
            </div>
          ) : (
            <ul className="candidate-list">
              {candidates.map((c, idx) => {
                const isOpen = expandedId === c.id;
                return (
                  <li
                    key={c.id}
                    className={`candidate-row ${isOpen ? "open" : ""}`}
                    onClick={() => setExpandedId(isOpen ? null : c.id)}
                  >
                    <div className="candidate-rank mono">#{idx + 1}</div>
                    <ScoreGauge score={c.job_fit_score} size={64} />
                    <div className="candidate-info">
                      <div className="candidate-name">{c.candidate_name || "Unnamed candidate"}</div>
                      <div className="candidate-meta mono">
                        {c.job_title || "—"} · {c.filename}
                      </div>
                      <div className="chip-row">
                        {c.matched_skills.slice(0, 5).map((s) => (
                          <span key={s} className="chip chip-match">{s}</span>
                        ))}
                      </div>
                    </div>

                    {isOpen && (
                      <div className="candidate-detail" onClick={(e) => e.stopPropagation()}>
                        {c.missing_skills.length > 0 && (
                          <div className="detail-block">
                            <div className="detail-label mono">GAPS</div>
                            <div className="chip-row">
                              {c.missing_skills.map((s) => (
                                <span key={s} className="chip chip-missing">{s}</span>
                              ))}
                            </div>
                          </div>
                        )}
                        {c.improvement_suggestions.length > 0 && (
                          <div className="detail-block">
                            <div className="detail-label mono">RECOMMENDATIONS</div>
                            <ul className="suggestion-list">
                              {c.improvement_suggestions.map((s, i) => (
                                <li key={i}>{s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
