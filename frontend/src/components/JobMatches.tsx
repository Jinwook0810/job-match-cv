"use client";

function formatSalary(min: string, max: string) {
  const minValue = Number(min);
  const maxValue = Number(max);

  if (!Number.isFinite(minValue) && !Number.isFinite(maxValue)) {
    return "";
  }

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(value);

  if (Number.isFinite(minValue) && Number.isFinite(maxValue)) {
    if (minValue === maxValue) {
      return formatCurrency(minValue);
    }
    return `${formatCurrency(minValue)} - ${formatCurrency(maxValue)}`;
  }

  return formatCurrency(Number.isFinite(minValue) ? minValue : maxValue);
}

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
  score?: number;
}

interface Props {
  jobs: Job[];
  onSelectJob: (job: Job) => void;
  title?: string;
  subtitle?: string;
  emptyMessage?: string;
  showMatchScore?: boolean;
}

export default function JobMatches({
  jobs,
  onSelectJob,
  title = "Recommended Jobs",
  subtitle = "Once a profile is matched, the top roles will appear here with direct links and a CV guide trigger for the selected job.",
  emptyMessage = "No results yet.",
  showMatchScore = true,
}: Props) {
  if (!jobs.length) {
    return (
      <div>
        {title && <h2 className="card-title">{title}</h2>}
        {subtitle && <p className="card-subtitle">{subtitle}</p>}
        <div className="guide-box guide-empty">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div>
      {title && <h2 className="card-title">{title}</h2>}
      {subtitle && <p className="card-subtitle">{subtitle}</p>}
      <div className="stack">
        {jobs.map((job, i) => {
          const salaryLabel = formatSalary(job.salary_min, job.salary_max);

          return (
            <div key={job.id || i} className="job-card">
              <div className="job-top">
                <div>
                  <h3 className="job-title">{job.title}</h3>
                  <p className="job-meta">
                    {job.company} | {job.location}
                  </p>
                  {salaryLabel && <p className="job-salary">{salaryLabel}</p>}
                </div>
                {showMatchScore && typeof job.score === "number" && (
                  <span className="match-pill">{(job.score * 100).toFixed(0)}% match</span>
                )}
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
          );
        })}
      </div>
    </div>
  );
}
