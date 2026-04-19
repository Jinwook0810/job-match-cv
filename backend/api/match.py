from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.profile_extractor import extract_profile
from services.storage import create_profile, create_recommendation_session, log_job_selection
from services.vector_store import query_jobs

router = APIRouter()


class MatchRequest(BaseModel):
    experience: str
    n_results: int = 5


class SelectJobRequest(BaseModel):
    session_id: int
    job: dict


@router.post("/")
def match_jobs(req: MatchRequest):
    if not req.experience.strip():
        raise HTTPException(status_code=400, detail="Experience text is required")

    try:
        structured_profile = extract_profile(req.experience)
        search_text = structured_profile["search_text"]
        matches = query_jobs(search_text, n_results=req.n_results)
        profile_id = create_profile(req.experience, structured_profile, search_text)
        session_id = create_recommendation_session(profile_id, req.n_results, matches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching error: {e}")

    return {
        "profile_id": profile_id,
        "session_id": session_id,
        "search_text": search_text,
        "structured_profile": structured_profile,
        "matches": matches,
    }


@router.post("/select")
def select_job(req: SelectJobRequest):
    if not req.job:
        raise HTTPException(status_code=400, detail="Job data is required")

    try:
        selection_id = log_job_selection(req.session_id, req.job)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Selection logging error: {e}")

    return {"selection_id": selection_id, "session_id": req.session_id}
