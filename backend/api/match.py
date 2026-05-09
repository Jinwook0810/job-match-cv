from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from services.document_parser import extract_text_from_upload
from services.profile_extractor import extract_profile
from services.storage import (
    create_profile,
    create_recommendation_session,
    get_profile,
    log_job_selection,
)
from services.vector_store import query_jobs

router = APIRouter()


class MatchRequest(BaseModel):
    experience: str
    n_results: int = 5


class ProfileRequest(BaseModel):
    experience: str


class RecommendRequest(BaseModel):
    profile_id: int
    n_results: int = 5


class SelectJobRequest(BaseModel):
    session_id: int
    job: dict


def _store_profile(experience_text: str) -> dict:
    try:
        structured_profile = extract_profile(experience_text)
        search_text = structured_profile["search_text"]
        profile_id = create_profile(experience_text, structured_profile, search_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile extraction error: {e}")

    return {
        "profile_id": profile_id,
        "search_text": search_text,
        "structured_profile": structured_profile,
    }


def _recommend_for_profile(profile_id: int, n_results: int) -> dict:
    try:
        _, _, search_text = get_profile(profile_id)
        matches = query_jobs(search_text, n_results=n_results)
        session_id = create_recommendation_session(profile_id, n_results, matches)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching error: {e}")

    return {
        "profile_id": profile_id,
        "session_id": session_id,
        "search_text": search_text,
        "matches": matches,
    }


@router.post("/profile")
def create_profile_from_text(req: ProfileRequest):
    if not req.experience.strip():
        raise HTTPException(status_code=400, detail="Experience text is required")

    return _store_profile(req.experience)


@router.post("/profile/upload")
async def create_profile_from_upload(resume: UploadFile = File(...)):
    try:
        extracted_text = await extract_text_from_upload(resume)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract readable text from the uploaded resume")

    return _store_profile(extracted_text)


@router.post("/recommend")
def recommend_for_profile(req: RecommendRequest):
    return _recommend_for_profile(req.profile_id, req.n_results)


@router.post("/")
def match_jobs(req: MatchRequest):
    if not req.experience.strip():
        raise HTTPException(status_code=400, detail="Experience text is required")

    profile_payload = _store_profile(req.experience)
    recommendation_payload = _recommend_for_profile(profile_payload["profile_id"], req.n_results)
    return {
        **profile_payload,
        "session_id": recommendation_payload["session_id"],
        "matches": recommendation_payload["matches"],
    }


@router.post("/upload")
async def match_uploaded_resume(
    resume: UploadFile = File(...),
    n_results: int = Form(5),
):
    profile_payload = await create_profile_from_upload(resume)
    recommendation_payload = _recommend_for_profile(profile_payload["profile_id"], n_results)
    return {
        **profile_payload,
        "session_id": recommendation_payload["session_id"],
        "matches": recommendation_payload["matches"],
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
