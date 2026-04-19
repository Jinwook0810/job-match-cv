import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


def fetch_jobs(keyword: str, location: str, country: str = "us", page: int = 1, results_per_page: int = 20) -> list[dict]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        raise RuntimeError("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY in .env")

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": keyword,
        "results_per_page": results_per_page,
    }
    if location:
        params["where"] = location

    url = f"{BASE_URL}/{country}/search/{page}"
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data.get("results", [])


def parse_job(raw: dict) -> dict:
    """Extract only the fields we need from a raw Adzuna job result."""
    return {
        "id": raw.get("id", ""),
        "title": raw.get("title", ""),
        "company": (raw.get("company") or {}).get("display_name", ""),
        "location": (raw.get("location") or {}).get("display_name", ""),
        "description": raw.get("description", ""),
        "salary_min": raw.get("salary_min"),
        "salary_max": raw.get("salary_max"),
        "url": raw.get("redirect_url", ""),
        "category": (raw.get("category") or {}).get("label", ""),
        "created": raw.get("created", ""),
    }
