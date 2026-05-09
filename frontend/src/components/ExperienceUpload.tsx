"use client";

import { useId, useState } from "react";

type InputMode = "linkedin" | "resume";

interface Props {
  onSubmit: (payload: { mode: InputMode; text?: string; file?: File | null }) => void;
  loading: boolean;
}

export default function ExperienceUpload({ onSubmit, loading }: Props) {
  const resumeInputId = useId();
  const [mode, setMode] = useState<InputMode>("linkedin");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const canSubmit = mode === "linkedin" ? Boolean(text.trim()) : Boolean(file);

  return (
    <div className="input-stack">
      <div className="section-kicker">Profile preparation</div>
      <h2 className="card-title">Profile Input</h2>
      <p className="card-subtitle">
        Choose the profile source you already have. The backend turns either LinkedIn text or resume
        content into the same retrieval-ready representation.
      </p>
      <div className="micro-pill-row">
        <span className="micro-pill">LinkedIn paste</span>
        <span className="micro-pill">PDF / DOCX / TXT</span>
        <span className="micro-pill">Stored for later matching</span>
      </div>
      <div className="mode-toggle" role="tablist" aria-label="Profile input mode">
        <button
          type="button"
          className={`toggle-pill ${mode === "linkedin" ? "toggle-pill-active" : ""}`}
          onClick={() => setMode("linkedin")}
        >
          LinkedIn Paste
        </button>
        <button
          type="button"
          className={`toggle-pill ${mode === "resume" ? "toggle-pill-active" : ""}`}
          onClick={() => setMode("resume")}
        >
          Resume Upload
        </button>
      </div>

      {mode === "linkedin" ? (
        <>
          <label className="input-label">LinkedIn Profile Paste</label>
          <textarea
            className="textarea"
            placeholder="Paste the full LinkedIn profile text here, including About, Experience, and Skills."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="helper-copy">
            The app extracts role signals from the text and stores a reusable profile representation.
          </div>
        </>
      ) : (
        <>
          <label className="input-label">Resume Upload</label>
          <label className="upload-box">
            <input
              id={resumeInputId}
              type="file"
              className="file-input"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <div className="upload-row">
              <span className="upload-button">Choose file</span>
              <span className="upload-filename">{file ? file.name : "No file chosen"}</span>
            </div>
            <span className="upload-title">
              {file ? file.name : "Choose a PDF, DOCX, or TXT resume"}
            </span>
            <span className="upload-note">
              The backend extracts text from the file, then runs the same matching pipeline.
            </span>
          </label>
        </>
      )}
      <div className="cta-row">
        <button
          onClick={() =>
            onSubmit(mode === "linkedin" ? { mode, text } : { mode, file })
          }
          disabled={loading || !canSubmit}
          className="button button-primary"
        >
          {loading ? "Preparing profile..." : "Prepare profile"}
        </button>
        <button
          type="button"
          onClick={() => {
            setText("");
            setFile(null);
          }}
          disabled={loading || !canSubmit}
          className="button button-secondary"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
