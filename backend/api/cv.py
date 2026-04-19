from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.job_page import fetch_job_page_text
from services.llm import generate_cv_guide
from services.storage import (
    get_cached_job_page,
    get_profile_for_session,
    upsert_job_page_cache,
)

router = APIRouter()


class CVGuideRequest(BaseModel):
    session_id: int
    job: dict


@router.post("/guide")
def cv_guide(req: CVGuideRequest):
    if not req.job:
        raise HTTPException(status_code=400, detail="Job data is required")

    try:
        experience, structured_profile = get_profile_for_session(req.session_id)
        full_job_text = ""
        job_text_source = "adzuna-snippet-only"
        job_url = str(req.job.get("url") or "").strip()

        if job_url:
            cached_page = get_cached_job_page(job_url)
            if cached_page and cached_page.get("page_text"):
                full_job_text = cached_page["page_text"]
                job_text_source = f"cached:{cached_page.get('source', 'unknown')}"
            else:
                fetched_page = fetch_job_page_text(job_url)
                full_job_text = fetched_page.get("page_text", "")
                if full_job_text:
                    upsert_job_page_cache(
                        requested_url=job_url,
                        fetched_url=fetched_page.get("fetched_url", job_url),
                        page_title=fetched_page.get("page_title", ""),
                        page_text=full_job_text,
                        source=fetched_page.get("source", "html"),
                    )
                    job_text_source = f"live:{fetched_page.get('source', 'html')}"

        guide = generate_cv_guide(
            experience=experience,
            structured_profile=structured_profile,
            job=req.job,
            full_job_text=full_job_text,
            job_text_source=job_text_source,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    return {"guide": guide}
