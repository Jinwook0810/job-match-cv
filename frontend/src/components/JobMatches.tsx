"use client";

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

interface Props {
  jobs: Job[];
  onSelectJob: (job: Job) => void;
}

export default function JobMatches({ jobs, onSelectJob }: Props) {
  if (!jobs.length) {
    return (
      <div>
        <h2 className="card-title">Recommended Jobs</h2>
        <p className="card-subtitle">
          Once a profile is matched, the top roles will appear here with direct links and a CV guide
          trigger for the selected job.
        </p>
        <div className="guide-box guide-empty">No matches yet. Paste a LinkedIn profile to start.</div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="card-title">Recommended Jobs</h2>
      <p className="card-subtitle">
        Top {jobs.length} semantic matches from the job store. Choosing one logs the selection and
        generates a role-specific CV strategy.
      </p>
      <div className="stack">
        {jobs.map((job, i) => (
          <div key={job.id || i} className="job-card">
            <div className="job-top">
              <div>
                <h3 className="job-title">{job.title}</h3>
                <p className="job-meta">
                  {job.company} · {job.location}
                </p>
                {job.salary_min && (
                  <p className="job-salary">
                    ${job.salary_min} - ${job.salary_max}
                  </p>
                )}
              </div>
              <span className="match-pill">{(job.score * 100).toFixed(0)}% match</span>
            </div>
            <div className="job-actions">
              <button onClick={() => onSelectJob(job)} className="button button-primary">
                Generate CV guide
              </button>
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="button button-secondary"
              >
                View posting
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
