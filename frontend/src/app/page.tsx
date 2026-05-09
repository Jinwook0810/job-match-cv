"use client";

import { useEffect, useState } from "react";
import CVGuide from "@/components/CVGuide";
import ExperienceUpload from "@/components/ExperienceUpload";
import JobMatches from "@/components/JobMatches";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const BROWSE_PAGE_SIZE = 12;

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

interface JobCluster {
  cluster_id: number;
  label: string;
  summary: string;
  job_count: number;
  jobs: Job[];
}

interface MatchInput {
  mode: "linkedin" | "resume";
  text?: string;
  file?: File | null;
}

type AppTab = "search" | "profile";
type ExploreView = "list" | "cluster";
type RoleFocus = "all" | "analytics" | "business" | "product_project" | "consulting" | "data_ai";

export default function Home() {
  const [activeTab, setActiveTab] = useState<AppTab>("search");
  const [exploreView, setExploreView] = useState<ExploreView>("list");
  const [profileId, setProfileId] = useState<number | null>(null);
  const [searchText, setSearchText] = useState("");
  const [matchedJobs, setMatchedJobs] = useState<Job[]>([]);
  const [browseJobs, setBrowseJobs] = useState<Job[]>([]);
  const [browseClusters, setBrowseClusters] = useState<JobCluster[]>([]);
  const [browseEventId, setBrowseEventId] = useState<number | null>(null);
  const [browseQuery, setBrowseQuery] = useState("");
  const [roleFocus, setRoleFocus] = useState<RoleFocus>("all");
  const [salaryFloor, setSalaryFloor] = useState(0);
  const [clusterCount, setClusterCount] = useState(5);
  const [browseTotalCount, setBrowseTotalCount] = useState(0);
  const [browsePage, setBrowsePage] = useState(1);
  const [browseTotalPages, setBrowseTotalPages] = useState(1);
  const [clusteredJobCount, setClusteredJobCount] = useState(0);
  const [pcaComponents, setPcaComponents] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [cvGuide, setCvGuide] = useState("");
  const [profileError, setProfileError] = useState("");
  const [matchError, setMatchError] = useState("");
  const [browseError, setBrowseError] = useState("");
  const [cvError, setCvError] = useState("");
  const [profileLoading, setProfileLoading] = useState(false);
  const [matchLoading, setMatchLoading] = useState(false);
  const [browseLoading, setBrowseLoading] = useState(false);
  const [clusterLoading, setClusterLoading] = useState(false);
  const [cvLoading, setCvLoading] = useState(false);

  const profileReady = profileId !== null;

  async function prepareProfile(input: MatchInput) {
    setProfileError("");
    setMatchError("");
    setCvError("");
    setCvGuide("");
    setMatchedJobs([]);
    setSessionId(null);
    setProfileLoading(true);

    try {
      const response =
        input.mode === "linkedin"
          ? await fetch(`${API}/match/profile`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ experience: input.text }),
            })
          : await (() => {
              const formData = new FormData();
              formData.append("resume", input.file as File);
              return fetch(`${API}/match/profile/upload`, {
                method: "POST",
                body: formData,
              });
            })();

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to prepare profile");
      }

      const data = await response.json();
      setProfileId(data.profile_id ?? null);
      setSearchText(data.search_text ?? "");
      setActiveTab("profile");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to prepare profile";
      setProfileError(message);
    } finally {
      setProfileLoading(false);
    }
  }

  async function fetchBrowseJobs(
    overrides?: Partial<{
      page: number;
      query: string;
      roleFocus: RoleFocus;
      salaryFloor: number;
    }>,
  ) {
    const effectivePage = overrides?.page ?? browsePage;
    const effectiveQuery = overrides?.query ?? browseQuery;
    const effectiveRoleFocus = overrides?.roleFocus ?? roleFocus;
    const effectiveSalaryFloor = overrides?.salaryFloor ?? salaryFloor;

    setBrowseError("");
    setBrowseLoading(true);
    setBrowseClusters([]);
    setExploreView("list");

    try {
      const params = new URLSearchParams({
        q: effectiveQuery,
        role_focus: effectiveRoleFocus,
        salary_floor: String(effectiveSalaryFloor),
        page: String(effectivePage),
        page_size: String(BROWSE_PAGE_SIZE),
      });
      if (profileId !== null) {
        params.set("profile_id", String(profileId));
      }

      const response = await fetch(`${API}/jobs/browse?${params.toString()}`);
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to browse jobs");
      }

      const data = await response.json();
      setBrowseEventId(data.browse_event_id ?? null);
      setBrowseJobs(data.jobs || []);
      setBrowseTotalCount(data.total_count || 0);
      setBrowsePage(data.page || effectivePage);
      setBrowseTotalPages(data.total_pages || 1);
      setClusteredJobCount(0);
      setPcaComponents(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to browse jobs";
      setBrowseError(message);
    } finally {
      setBrowseLoading(false);
    }
  }

  async function fetchBrowseClusters() {
    setBrowseError("");
    setClusterLoading(true);
    setCvError("");

    try {
      const params = new URLSearchParams({
        q: browseQuery,
        role_focus: roleFocus,
        salary_floor: String(salaryFloor),
        cluster_count: String(clusterCount),
        limit: "60",
      });

      const response = await fetch(`${API}/jobs/cluster?${params.toString()}`);
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to cluster jobs");
      }

      const data = await response.json();
      setBrowseClusters(data.clusters || []);
      setClusteredJobCount(data.total_count || 0);
      setPcaComponents(data.pca_components ?? null);
      setExploreView("cluster");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to cluster jobs";
      setBrowseError(message);
    } finally {
      setClusterLoading(false);
    }
  }

  useEffect(() => {
    void fetchBrowseJobs({ page: 1 });
  }, []);

  async function fetchRecommendations() {
    if (!profileId) {
      return;
    }

    setMatchError("");
    setMatchLoading(true);
    setCvGuide("");
    setCvError("");

    try {
      const response = await fetch(`${API}/match/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_id: profileId, n_results: 5 }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to fetch personalized matches");
      }

      const data = await response.json();
      setSessionId(data.session_id ?? null);
      setMatchedJobs(data.matches || []);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to fetch personalized matches";
      setMatchError(message);
    } finally {
      setMatchLoading(false);
    }
  }

  async function handleSelectRecommendedJob(job: Job) {
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

      const response = await fetch(`${API}/cv/guide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, job }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to generate CV guide");
      }

      const data = await response.json();
      setCvGuide(data.guide || "");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to generate CV guide";
      setCvError(message);
    } finally {
      setCvLoading(false);
    }
  }

  async function handleSelectBrowseJob(job: Job) {
    if (!profileId) {
      setCvGuide("");
      setCvError("Prepare a LinkedIn profile or resume first to generate a CV guide for explored jobs.");
      setActiveTab("profile");
      return;
    }

    if (!browseEventId) {
      setCvGuide("");
      setCvError("Refresh the current results once after preparing your profile so the selection can be logged.");
      return;
    }

    setCvGuide("");
    setCvError("");
    setCvLoading(true);

    try {
      const selectionRes = await fetch(`${API}/jobs/browse/select`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ browse_event_id: browseEventId, profile_id: profileId, job }),
      });

      if (!selectionRes.ok) {
        const payload = await selectionRes.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to log browse selection");
      }

      const response = await fetch(`${API}/cv/guide/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_id: profileId, job }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || "Failed to generate CV guide");
      }

      const data = await response.json();
      setCvGuide(data.guide || "");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to generate CV guide";
      setCvError(message);
    } finally {
      setCvLoading(false);
    }
  }

  const currentSearchSummary =
    exploreView === "cluster"
      ? `Semantic grouping over ${clusteredJobCount} filtered jobs${pcaComponents ? ` with PCA(${pcaComponents}) + K-means` : " with K-means"}.`
      : `Showing page ${browsePage} of ${browseTotalPages} across ${browseTotalCount} matching jobs.`;

  return (
    <main className="page-shell">
      <section className="app-header panel">
        <div className="app-header-copy">
          <div className="section-kicker">Job discovery and profile-based tailoring</div>
          <h1 className="app-title">Search jobs directly, or prepare a profile for AI matching.</h1>
          <p className="app-subtitle">
            Use the stored New York job corpus like a searchable board, then switch to personalized
            matching and CV guidance whenever you want profile-aware recommendations.
          </p>
        </div>
        <div className="results-badges">
          <span className="micro-pill micro-pill-strong">{browseTotalCount || clusteredJobCount} jobs in view</span>
          <span className="micro-pill">{profileReady ? "Profile prepared" : "Profile optional"}</span>
          <span className="micro-pill">924 stored New York jobs</span>
        </div>
      </section>

      <section className="top-tabs">
        <button
          type="button"
          className={`top-tab ${activeTab === "search" ? "top-tab-active" : ""}`}
          onClick={() => setActiveTab("search")}
        >
          Search Jobs
        </button>
        <button
          type="button"
          className={`top-tab ${activeTab === "profile" ? "top-tab-active" : ""}`}
          onClick={() => setActiveTab("profile")}
        >
          Profile + AI Match
        </button>
      </section>

      {activeTab === "search" ? (
        <section className="tab-layout tab-layout-search">
          <aside className="panel card sidebar-panel">
            <div className="section-kicker">Search controls</div>
            <h2 className="card-title">Search the stored corpus</h2>
            <p className="card-subtitle">
              Filter the New York job dataset directly. If you later want a tailored CV guide, prepare a
              LinkedIn profile or resume in the other tab.
            </p>

            <div className="filters-card">
              <div className="filters-grid">
                <label className="filter-field">
                  <span>Search jobs</span>
                  <input
                    className="filter-input"
                    value={browseQuery}
                    onChange={(e) => setBrowseQuery(e.target.value)}
                    placeholder="Healthcare analyst, consulting, program manager..."
                    disabled={browseLoading}
                  />
                </label>

                <label className="filter-field">
                  <span>Role focus</span>
                  <select
                    className="filter-select"
                    value={roleFocus}
                    onChange={(e) => setRoleFocus(e.target.value as RoleFocus)}
                    disabled={browseLoading}
                  >
                    <option value="all">All roles</option>
                    <option value="analytics">Analytics</option>
                    <option value="business">Business</option>
                    <option value="product_project">Product / Project</option>
                    <option value="consulting">Consulting</option>
                    <option value="data_ai">Data / AI</option>
                  </select>
                </label>

                <label className="filter-field">
                  <span>Salary floor</span>
                  <select
                    className="filter-select"
                    value={salaryFloor}
                    onChange={(e) => setSalaryFloor(Number(e.target.value))}
                    disabled={browseLoading}
                  >
                    <option value={0}>Any salary</option>
                    <option value={80000}>80k+</option>
                    <option value={100000}>100k+</option>
                    <option value={120000}>120k+</option>
                  </select>
                </label>

                <label className="filter-field">
                  <span>Cluster groups</span>
                  <select
                    className="filter-select"
                    value={clusterCount}
                    onChange={(e) => setClusterCount(Number(e.target.value))}
                    disabled={clusterLoading}
                  >
                    <option value={4}>4 groups</option>
                    <option value={5}>5 groups</option>
                    <option value={6}>6 groups</option>
                    <option value={8}>8 groups</option>
                  </select>
                </label>
              </div>

              <div className="cta-row filters-actions">
                <button
                  type="button"
                  className="button button-primary"
                  onClick={() => void fetchBrowseJobs({ page: 1 })}
                  disabled={browseLoading}
                >
                  {browseLoading ? "Refreshing jobs..." : "Apply filters"}
                </button>
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => void fetchBrowseClusters()}
                  disabled={clusterLoading}
                >
                  {clusterLoading ? "Clustering jobs..." : "Cluster results"}
                </button>
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => {
                    setBrowseQuery("");
                    setRoleFocus("all");
                    setSalaryFloor(0);
                    setClusterCount(5);
                    void fetchBrowseJobs({
                      page: 1,
                      query: "",
                      roleFocus: "all",
                      salaryFloor: 0,
                    });
                  }}
                  disabled={browseLoading || clusterLoading}
                >
                  Reset
                </button>
              </div>
            </div>

            <div className="status-card">
              <span className="status-card-label">Current view</span>
              <strong>{exploreView === "cluster" ? "Semantic clusters" : "Paged search results"}</strong>
              <p>{currentSearchSummary}</p>
            </div>

            <div className="status-card">
              <span className="status-card-label">CV guide requirement</span>
              <strong>{profileReady ? "Ready to tailor from search results" : "Prepare a profile when needed"}</strong>
              <p>
                Search works without a profile. CV guide generation from searched jobs becomes available
                after you prepare LinkedIn or resume input.
              </p>
            </div>
          </aside>

          <div className="tab-content">
            <div className="panel card content-panel">
              <div className="results-shell-header">
                <div>
                  <div className="section-kicker">Search results</div>
                  <h2 className="results-title">Browse and filter jobs directly.</h2>
                </div>
                <div className="results-badges">
                  <button
                    type="button"
                    className={`mini-tab ${exploreView === "list" ? "mini-tab-active" : ""}`}
                    onClick={() => setExploreView("list")}
                  >
                    List view
                  </button>
                  <button
                    type="button"
                    className={`mini-tab ${exploreView === "cluster" ? "mini-tab-active" : ""}`}
                    onClick={() => browseClusters.length && setExploreView("cluster")}
                    disabled={!browseClusters.length}
                  >
                    Clustered view
                  </button>
                </div>
              </div>

              {browseError && <div className="error">{browseError}</div>}
              <div className="status result-status">{currentSearchSummary}</div>

              {exploreView === "cluster" ? (
                <div>
                  <div className="cluster-stack">
                    {browseClusters.map((cluster) => (
                      <section key={cluster.cluster_id} className="cluster-card">
                        <div className="cluster-header">
                          <div>
                            <h3 className="cluster-title">{cluster.label}</h3>
                            <p className="cluster-summary">{cluster.summary}</p>
                          </div>
                          <span className="cluster-pill">{cluster.job_count} jobs</span>
                        </div>
                        <JobMatches
                          jobs={cluster.jobs}
                          onSelectJob={handleSelectBrowseJob}
                          title=""
                          subtitle=""
                          emptyMessage="No jobs in this cluster."
                          showMatchScore={false}
                        />
                      </section>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  <JobMatches
                    jobs={browseJobs}
                    onSelectJob={handleSelectBrowseJob}
                    title="Search Jobs"
                    subtitle="Use role, salary, and keyword filters to move through the stored job corpus page by page."
                    emptyMessage="No jobs match the current search and filters."
                    showMatchScore={false}
                  />

                  {browseTotalPages > 1 && (
                    <div className="pagination-bar">
                      <button
                        type="button"
                        className="button button-secondary"
                        onClick={() => void fetchBrowseJobs({ page: browsePage - 1 })}
                        disabled={browseLoading || browsePage <= 1}
                      >
                        Previous
                      </button>
                      <div className="pagination-copy">
                        Page <strong>{browsePage}</strong> of <strong>{browseTotalPages}</strong>
                      </div>
                      <button
                        type="button"
                        className="button button-secondary"
                        onClick={() => void fetchBrowseJobs({ page: browsePage + 1 })}
                        disabled={browseLoading || browsePage >= browseTotalPages}
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="panel card content-panel">
              {cvError && <div className="error">{cvError}</div>}
              <CVGuide guide={cvGuide} loading={cvLoading} />
            </div>
          </div>
        </section>
      ) : (
        <section className="tab-layout tab-layout-profile">
          <div className="tab-content">
            <div className="panel card content-panel">
              <ExperienceUpload onSubmit={prepareProfile} loading={profileLoading} />
              {searchText && (
                <div className="match-summary info-card">
                  <strong>Stored profile summary:</strong> {searchText}
                </div>
              )}
              <div className="status-grid">
                <div className={`status-card ${profileReady ? "status-card-ready" : ""}`}>
                  <span className="status-card-label">Profile status</span>
                  <strong>{profileReady ? "Ready for AI matching" : "No prepared profile yet"}</strong>
                  <p>
                    {profileReady
                      ? "You can now generate personalized matches and CV guides."
                      : "Paste LinkedIn text or upload a resume to unlock personalized retrieval."}
                  </p>
                </div>
                <div className="status-card">
                  <span className="status-card-label">Backend API</span>
                  <strong>{API}</strong>
                  <p>The stored profile is reused across matching and CV-tailoring requests.</p>
                </div>
              </div>
              {profileError && <div className="error">{profileError}</div>}
              {matchError && <div className="error">{matchError}</div>}
            </div>

            <div className="panel card content-panel">
              <div className="results-shell-header">
                <div>
                  <div className="section-kicker">Personalized matching</div>
                  <h2 className="results-title">Generate AI-guided job recommendations.</h2>
                </div>
                <div className="results-badges">
                  <span className="micro-pill">{profileReady ? "Profile connected" : "Profile required"}</span>
                </div>
              </div>

              <div className="cta-row">
                <button
                  type="button"
                  className="button button-primary"
                  onClick={() => void fetchRecommendations()}
                  disabled={!profileReady || matchLoading}
                >
                  {matchLoading ? "Finding matches..." : "Generate personalized matches"}
                </button>
              </div>

              <JobMatches
                jobs={matchedJobs}
                onSelectJob={handleSelectRecommendedJob}
                title="AI Matched Jobs"
                subtitle="These are the top semantic matches produced from your stored profile representation and the job embeddings in ChromaDB."
                emptyMessage={
                  profileReady
                    ? "No personalized matches yet. Generate them from your prepared profile."
                    : "Prepare a LinkedIn profile or resume first, then generate AI matches."
                }
                showMatchScore
              />
            </div>

            <div className="panel card content-panel">
              {cvError && <div className="error">{cvError}</div>}
              <CVGuide guide={cvGuide} loading={cvLoading} />
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
