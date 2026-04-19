import json
from typing import Any

from services.llm import get_client

PROFILE_MODEL = "gpt-4o-mini"


def _coerce_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_json_loads(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(content[start : end + 1])


def _fallback_profile(raw_text: str) -> dict[str, Any]:
    return {
        "target_roles": [],
        "years_experience": None,
        "seniority": "",
        "skills": [],
        "industries": [],
        "preferred_locations": [],
        "education": [],
        "highlights": [],
        "search_text": " ".join(raw_text.split())[:3000],
    }


def normalize_profile(profile: dict[str, Any], raw_text: str) -> dict[str, Any]:
    normalized = {
        "target_roles": _coerce_list(profile.get("target_roles")),
        "years_experience": profile.get("years_experience"),
        "seniority": _coerce_text(profile.get("seniority")),
        "skills": _coerce_list(profile.get("skills")),
        "industries": _coerce_list(profile.get("industries")),
        "preferred_locations": _coerce_list(profile.get("preferred_locations")),
        "education": _coerce_list(profile.get("education")),
        "highlights": _coerce_list(profile.get("highlights")),
        "search_text": _coerce_text(profile.get("search_text")),
    }

    if not normalized["search_text"]:
        parts = [
            ", ".join(normalized["target_roles"]),
            f"{normalized['years_experience']} years experience"
            if normalized["years_experience"] is not None
            else "",
            normalized["seniority"],
            ", ".join(normalized["skills"]),
            ", ".join(normalized["industries"]),
            ", ".join(normalized["preferred_locations"]),
            ", ".join(normalized["highlights"]),
        ]
        normalized["search_text"] = ". ".join(part for part in parts if part).strip()

    if not normalized["search_text"]:
        normalized["search_text"] = _fallback_profile(raw_text)["search_text"]

    return normalized


def extract_profile(raw_text: str) -> dict[str, Any]:
    prompt = f"""You extract job-matching data from pasted LinkedIn profile text.

Return strict JSON only. Do not wrap the JSON in markdown.

Schema:
{{
  "target_roles": ["role"],
  "years_experience": 0,
  "seniority": "intern|junior|mid|senior|lead|executive|",
  "skills": ["skill"],
  "industries": ["industry"],
  "preferred_locations": ["location"],
  "education": ["education item"],
  "highlights": ["short evidence-backed resume highlight"],
  "search_text": "A concise search-oriented summary for semantic job matching."
}}

Rules:
- Extract only job-relevant information.
- Infer likely target roles when the text implies them.
- Keep highlights short and evidence-based.
- search_text should be a compact paragraph optimized for semantic retrieval against job descriptions.
- If data is missing, use empty lists or empty strings. Use null for unknown years_experience.

LinkedIn text:
{raw_text}
"""

    client = get_client()
    response = client.chat.completions.create(
        model=PROFILE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=900,
    )
    content = response.choices[0].message.content or ""

    try:
        parsed = _safe_json_loads(content)
    except json.JSONDecodeError:
        return _fallback_profile(raw_text)

    return normalize_profile(parsed, raw_text)
