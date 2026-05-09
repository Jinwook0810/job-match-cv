"""
Populate ChromaDB with fresh job data from Adzuna.

Usage:
    py -3 seed_jobs.py
"""

import os
from pathlib import Path

import chromadb

os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

from services.adzuna import fetch_jobs, parse_job
from services.storage import init_db, reset_jobs_table, upsert_job_records
from services.vector_store import COLLECTION_NAME, upsert_jobs

SEARCHES = [
    {"keyword": "data scientist", "location": "New York"},
    {"keyword": "data analyst", "location": "New York"},
    {"keyword": "business intelligence analyst", "location": "New York"},
    {"keyword": "machine learning engineer", "location": "New York"},
    {"keyword": "business analyst", "location": "New York"},
    {"keyword": "product analyst", "location": "New York"},
    {"keyword": "strategy analyst", "location": "New York"},
    {"keyword": "insights analyst", "location": "New York"},
    {"keyword": "operations analyst", "location": "New York"},
    {"keyword": "healthcare analyst", "location": "New York"},
    {"keyword": "market research analyst", "location": "New York"},
    {"keyword": "project manager", "location": "New York"},
    {"keyword": "program manager", "location": "New York"},
    {"keyword": "product manager", "location": "New York"},
    {"keyword": "management consultant", "location": "New York"},
    {"keyword": "data engineer", "location": "New York"},
    {"keyword": "AI engineer", "location": "New York"},
]
PAGES = 3
RESULTS_PER_PAGE = 20
CHROMA_PATH = Path(__file__).resolve().parent / "chroma_db"


def reset_collection() -> None:
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing Chroma collection: {COLLECTION_NAME}")
    except Exception:
        print(f"No existing Chroma collection to delete: {COLLECTION_NAME}")


def reset_job_store() -> None:
    reset_jobs_table()
    print("Cleared existing SQLite jobs table")


def main():
    init_db()
    reset_collection()
    reset_job_store()

    total_requested = 0
    for search in SEARCHES:
        for page in range(1, PAGES + 1):
            print(f"Fetching: {search['keyword']} in {search['location']} (page {page})...", end=" ")
            try:
                raw_jobs = fetch_jobs(
                    keyword=search["keyword"],
                    location=search["location"],
                    country="us",
                    page=page,
                    results_per_page=RESULTS_PER_PAGE,
                )
                jobs = [parse_job(job) for job in raw_jobs]
                jobs = [job for job in jobs if job["description"].strip()]
                if not jobs:
                    print("no usable jobs")
                    continue
                upsert_job_records(jobs)
                stored = upsert_jobs(jobs)
                print(f"stored {stored}")
                total_requested += stored
            except Exception as e:
                print(f"error: {e}")

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    final_count = client.get_collection(COLLECTION_NAME).count()

    print("\nFinished seeding ChromaDB.")
    print(f"Requested upserts: {total_requested}")
    print(f"Unique jobs currently stored: {final_count}")


if __name__ == "__main__":
    main()
