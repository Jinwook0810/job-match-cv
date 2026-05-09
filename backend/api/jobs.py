from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.adzuna import fetch_jobs, parse_job
from services.job_clustering import cluster_jobs
from services.storage import create_job_browse_event, log_job_browse_selection, search_job_records, upsert_job_records
from services.vector_store import upsert_jobs

router = APIRouter()


class FetchJobsRequest(BaseModel):
    keyword: str
    location: str = "New York"
    country: str = "us"
    page: int = 1
    results_per_page: int = 20


class BrowseSelectionRequest(BaseModel):
    browse_event_id: int
    profile_id: int
    job: dict

ROLE_FOCUS_RULES = {
    "analytics": ("analyst", "analytics", "business intelligence", "insights", "market research", "reporting"),
    "business": ("business analyst", "operations analyst", "strategy", "operations", "process improvement"),
    "product_project": ("product manager", "product analyst", "project manager", "program manager", "roadmap"),
    "consulting": ("consultant", "consulting", "advisory", "transformation"),
    "data_ai": ("data scientist", "machine learning", "ai engineer", "data engineer", "ml engineer"),
}


def _job_text(job: dict) -> str:
    return " ".join(
        [
            str(job.get("title") or ""),
            str(job.get("company") or ""),
            str(job.get("location") or ""),
            str(job.get("category") or ""),
            str(job.get("description") or ""),
        ]
    ).lower()


def _matches_role_focus(job: dict, role_focus: str) -> bool:
    if role_focus == "all":
        return True
    tokens = ROLE_FOCUS_RULES.get(role_focus, ())
    text = _job_text(job)
    return any(token in text for token in tokens)


def _salary_value(job: dict) -> float | None:
    raw_min = str(job.get("salary_min") or "").strip()
    raw_max = str(job.get("salary_max") or "").strip()
    for value in (raw_min, raw_max):
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _search_rank(job: dict, query: str) -> int:
    if not query:
        return 0
    text = _job_text(job)
    title = str(job.get("title") or "").lower()
    company = str(job.get("company") or "").lower()
    query = query.lower()
    score = 0
    if query in title:
        score += 4
    if query in company:
        score += 2
    if query in text:
        score += 1
    return score


@router.get("/browse")
def browse_jobs(
    profile_id: int | None = None,
    q: str = "",
    role_focus: str = "all",
    salary_floor: int = 0,
    page: int = 1,
    page_size: int = 12,
):
    try:
        jobs = search_job_records(q, ROLE_FOCUS_RULES.get(role_focus, ()), salary_floor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load jobs: {e}")

    filtered = []
    lowered_query = q.strip().lower()
    for job in jobs:
        filtered.append(
            {
                **job,
                "browse_rank": _search_rank(job, lowered_query),
                "score": 0,
            }
        )

    filtered.sort(
        key=lambda job: (
            -int(job.get("browse_rank", 0)),
            -(float(_salary_value(job) or 0)),
            str(job.get("title") or ""),
        )
    )

    safe_page = max(1, page)
    safe_page_size = max(1, min(page_size, 50))
    total_count = len(filtered)
    total_pages = max(1, (total_count + safe_page_size - 1) // safe_page_size)
    if safe_page > total_pages:
        safe_page = total_pages

    start = (safe_page - 1) * safe_page_size
    end = start + safe_page_size
    results = filtered[start:end]
    filters = {
        "role_focus": role_focus,
        "salary_floor": salary_floor,
        "page": safe_page,
        "page_size": safe_page_size,
    }

    browse_event_id = None
    if profile_id is not None:
        try:
            browse_event_id = create_job_browse_event(profile_id, q, filters, results)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not log browse event: {e}")

    return {
        "browse_event_id": browse_event_id,
        "total_count": total_count,
        "page": safe_page,
        "page_size": safe_page_size,
        "total_pages": total_pages,
        "jobs": results,
    }


@router.get("/cluster")
def cluster_browse_jobs(
    q: str = "",
    role_focus: str = "all",
    salary_floor: int = 0,
    cluster_count: int = 5,
    limit: int = 60,
):
    try:
        jobs = search_job_records(q, ROLE_FOCUS_RULES.get(role_focus, ()), salary_floor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load jobs: {e}")

    if not jobs:
        return {"total_count": 0, "cluster_count": 0, "clusters": []}

    lowered_query = q.strip().lower()
    ranked = [
        {
            **job,
            "browse_rank": _search_rank(job, lowered_query),
            "score": 0,
        }
        for job in jobs
    ]
    ranked.sort(
        key=lambda job: (
            -int(job.get("browse_rank", 0)),
            -(float(_salary_value(job) or 0)),
            str(job.get("title") or ""),
        )
    )
    candidate_jobs = ranked[:limit]

    try:
        cluster_payload = cluster_jobs(candidate_jobs, requested_clusters=cluster_count)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not cluster jobs: {e}")

    return {
        "total_count": len(candidate_jobs),
        **cluster_payload,
    }


@router.post("/fetch")
def fetch_and_store(req: FetchJobsRequest):
    """Fetch jobs from Adzuna and store them in ChromaDB."""
    try:
        raw_jobs = fetch_jobs(
            keyword=req.keyword,
            location=req.location,
            country=req.country,
            page=req.page,
            results_per_page=req.results_per_page,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Adzuna API error: {e}")

    if not raw_jobs:
        return {"stored": 0, "message": "No jobs returned from Adzuna"}

    jobs = [parse_job(j) for j in raw_jobs]

    try:
        upsert_job_records(jobs)
        stored = upsert_jobs(jobs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job storage error: {e}")

    return {"stored": stored, "jobs": jobs}


@router.post("/browse/select")
def log_browse_selection(req: BrowseSelectionRequest):
    if not req.job:
        raise HTTPException(status_code=400, detail="Job data is required")

    try:
        selection_id = log_job_browse_selection(req.browse_event_id, req.profile_id, req.job)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Browse selection logging error: {e}")

    return {"selection_id": selection_id, "browse_event_id": req.browse_event_id}
