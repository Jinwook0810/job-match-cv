from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.adzuna import fetch_jobs, parse_job
from services.vector_store import upsert_jobs

router = APIRouter()


class FetchJobsRequest(BaseModel):
    keyword: str
    location: str = "New York"
    country: str = "us"
    page: int = 1
    results_per_page: int = 20


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
        stored = upsert_jobs(jobs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChromaDB error: {e}")

    return {"stored": stored, "jobs": jobs}
