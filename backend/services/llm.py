import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = None
CV_MODEL = os.getenv("OPENAI_CV_MODEL", "gpt-4o-mini")


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def generate_cv_guide(
    experience: str,
    structured_profile: dict,
    job: dict,
    full_job_text: str = "",
    job_text_source: str = "",
) -> str:
    prompt = f"""You are a professional career coach specializing in US job applications.

A candidate has provided their LinkedIn experience and wants to apply for the following job.
Analyze both and provide a structured CV or resume writing guide.

---
JOB TITLE: {job.get("title")}
COMPANY: {job.get("company")}
LOCATION: {job.get("location")}
CATEGORY: {job.get("category")}
ADZUNA JOB DESCRIPTION SNIPPET:
{job.get("description", "Not available")}

FULL JOB PAGE TEXT SOURCE: {job_text_source or "not available"}
FULL JOB PAGE TEXT:
{full_job_text or "Not available"}

---
CANDIDATE EXPERIENCE (from LinkedIn):
{experience}

---
STRUCTURED PROFILE FOR MATCHING:
{structured_profile}

---
Please provide:
1. Key skills to highlight: specific skills from their experience that match this JD
2. Experience bullets to emphasize: which past roles or projects to lead with and why
3. Gaps to address: anything in the JD the candidate is missing, and how to frame it honestly
4. Summary statement: a 2-3 sentence professional summary tailored to this role
5. ATS keywords: important keywords from the JD to include in the resume
6. Resume tailoring plan: a short ordered action plan for rewriting the resume for this role

Instructions:
- Prefer the full job page text when it is available because it may contain more detailed requirements than the Adzuna snippet.
- Ignore application form fields, privacy notices, and boilerplate if they appear in the full page text.
- Be specific and actionable. Reference the candidate's actual experience."""

    client = get_client()
    response = client.chat.completions.create(
        model=CV_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
    )
    return response.choices[0].message.content or ""
