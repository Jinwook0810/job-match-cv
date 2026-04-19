"use client";

import { useState } from "react";
import CVGuide from "@/components/CVGuide";
import ExperienceUpload from "@/components/ExperienceUpload";
import JobMatches from "@/components/JobMatches";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  salary_min: string;
  salary_max: string;
  url: string;
  category?: string;
  description?: string;
  score: number;
}

export default function Home() {
  const [matchedJobs, setMatchedJobs] = useState<Job[]>([]);
  const [cvGuide, setCvGuide] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [searchText, setSearchText] = useState("");
  const [matchError, setMatchError] = useState("");
  const [cvError, setCvError] = useState("");
  const [matchLoading, setMatchLoading] = useState(false);
  const [cvLoading, setCvLoading] = useState(false);

  async function handleMatch(text: string) {
    setMatchedJobs([]);
    setCvGuide("");
    setSessionId(null);
    setSearchText("");
    setMatchError("");
    setCvError("");
    setMatchLoading(true);

    try {
      const res = await fetch(`${API}/match/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ experience: text, n_results: 5 }),
      });

      if (!res.ok) {
        const payload = await res.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to fetch job matches");
      }

      const data = await res.json();
      setSessionId(data.session_id ?? null);
      setSearchText(data.search_text ?? "");
      setMatchedJobs(data.matches || []);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to fetch job matches";
      setMatchError(message);
    } finally {
      setMatchLoading(false);
    }
  }

  async function handleSelectJob(job: Job) {
    if (!sessionId) {
      return;
    }

    setCvGuide("");
    setCvError("");
    setCvLoading(true);

    try {
      const selectionRes = await fetch(`${API}/match/select`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, job }),
      });

      if (!selectionRes.ok) {
        const payload = await selectionRes.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to record selection");
      }

      const res = await fetch(`${API}/cv/guide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, job }),
      });

      if (!res.ok) {
        const payload = await res.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to generate CV guide");
      }

      const data = await res.json();
      setCvGuide(data.guide || "");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to generate CV guide";
      setCvError(message);
    } finally {
      setCvLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="panel hero-main">
          <div className="eyebrow">LinkedIn in, roles out, resume tailored</div>
          <h1>Paste a profile. Get jobs worth applying to.</h1>
          <p>
            This workflow extracts job-relevant signals from a LinkedIn page, finds the best matching
            roles from the live job store, and turns the chosen posting into a targeted CV rewrite plan.
          </p>
          <div className="hero-stats">
            <div className="stat-card">
              <span className="stat-label">Step 1</span>
              <span className="stat-value">Extract</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Step 2</span>
              <span className="stat-value">Match</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Step 3</span>
              <span className="stat-value">Tailor</span>
            </div>
          </div>
        </div>

        <aside className="panel hero-side">
          <div>
            <h2 className="side-title">What the user does</h2>
            <ol className="side-list">
              <li>Copy the full LinkedIn profile page text.</li>
              <li>Paste it into the input panel.</li>
              <li>Review 5 matched roles.</li>
              <li>Pick one role and generate the CV guide.</li>
            </ol>
          </div>
          <div className="side-note">
            Every recommendation session and job selection is stored so you can later analyze clicks,
            improve ranking, or build a proper recommender on top.
          </div>
        </aside>
      </section>

      <section className="workspace">
        <div className="panel card">
          <ExperienceUpload onSubmit={handleMatch} loading={matchLoading} />
          {searchText && (
            <div className="match-summary">
              <strong>Search summary used for semantic matching:</strong> {searchText}
            </div>
          )}
          {matchError && <div className="error">{matchError}</div>}
          <div className="status">
            Backend API: <strong>{API}</strong>
          </div>
        </div>

        <div className="panel card">
          <JobMatches jobs={matchedJobs} onSelectJob={handleSelectJob} />
          {cvError && <div className="error">{cvError}</div>}
          <CVGuide guide={cvGuide} loading={cvLoading} />
        </div>
      </section>
    </main>
  );
}
