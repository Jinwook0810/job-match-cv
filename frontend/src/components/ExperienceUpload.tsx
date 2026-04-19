"use client";

import { useState } from "react";

interface Props {
  onSubmit: (experience: string) => void;
  loading: boolean;
}

export default function ExperienceUpload({ onSubmit, loading }: Props) {
  const [text, setText] = useState("");

  return (
    <div>
      <h2 className="card-title">Profile Input</h2>
      <p className="card-subtitle">
        Paste the full LinkedIn page text. The backend strips out noise, extracts hiring-relevant
        signals, and uses that summary for retrieval.
      </p>
      <label className="input-label">LinkedIn Profile Paste</label>
      <textarea
        className="textarea"
        placeholder="Paste the full LinkedIn profile text here, including About, Experience, and Skills."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <div className="cta-row">
        <button
          onClick={() => onSubmit(text)}
          disabled={loading || !text.trim()}
          className="button button-primary"
        >
          {loading ? "Finding matches..." : "Find matching jobs"}
        </button>
        <button
          type="button"
          onClick={() => setText("")}
          disabled={loading || !text.trim()}
          className="button button-secondary"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
