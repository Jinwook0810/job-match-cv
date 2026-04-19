"""
Populate ChromaDB with fresh job data from Adzuna.

Usage:
    py -3 seed_jobs.py
"""

import os

import chromadb

os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

from services.adzuna import fetch_jobs, parse_job
from services.vector_store import COLLECTION_NAME, upsert_jobs

SEARCHES = [
    {"keyword": "data scientist", "location": "New York"},
    {"keyword": "data analyst", "location": "New York"},
    {"keyword": "machine learning engineer", "location": "New York"},
    {"keyword": "software engineer", "location": "New York"},
    {"keyword": "product manager", "location": "New York"},
    {"keyword": "business analyst", "location": "New York"},
    {"keyword": "data engineer", "location": "New York"},
    {"keyword": "AI engineer", "location": "New York"},
]
PAGES = 2
RESULTS_PER_PAGE = 20


def reset_collection() -> None:
    client = chromadb.PersistentClient(path="./chroma_db")
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing Chroma collection: {COLLECTION_NAME}")
    except Exception:
        print(f"No existing Chroma collection to delete: {COLLECTION_NAME}")


def main():
    reset_collection()

    total = 0
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
                stored = upsert_jobs(jobs)
                print(f"stored {stored}")
                total += stored
            except Exception as e:
                print(f"error: {e}")

    print(f"\nFinished seeding ChromaDB with {total} jobs.")


if __name__ == "__main__":
    main()
