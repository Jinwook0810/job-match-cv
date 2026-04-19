"use client";

interface Props {
  guide: string;
  loading: boolean;
}

export default function CVGuide({ guide, loading }: Props) {
  if (!guide && !loading) {
    return (
      <div>
        <h2 className="card-title">Tailored CV Guide</h2>
        <p className="card-subtitle">
          The generated guide will summarize what to emphasize, what gaps to handle carefully, and how
          to rewrite the resume for the chosen job posting.
        </p>
        <div className="guide-box guide-empty">Choose one of the recommended jobs to generate the guide.</div>
      </div>
    );
  }

  if (loading) {
    return <div className="guide-box guide-empty">Generating CV guide...</div>;
  }

  return (
    <div>
      <h2 className="card-title">Tailored CV Guide</h2>
      <p className="card-subtitle">
        This is generated from the selected job description plus the structured profile extracted from
        the LinkedIn paste.
      </p>
      <div className="guide-box">{guide}</div>
    </div>
  );
}
