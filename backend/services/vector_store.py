import os

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-base-en-v1.5"
COLLECTION_NAME = "jobs"

_client = None
_model = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path="./chroma_db")
    return _client


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_collection():
    return get_client().get_or_create_collection(COLLECTION_NAME)


def embed(text: str) -> list[float]:
    return get_model().encode(text, normalize_embeddings=True).tolist()


def upsert_jobs(jobs: list[dict]) -> int:
    collection = get_collection()
    ids, embeddings, documents, metadatas = [], [], [], []

    for job in jobs:
        text = f"{job['title']} {job['company']} {job['description']}"
        ids.append(job["id"])
        embeddings.append(embed(text))
        documents.append(text)
        metadatas.append(
            {
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "salary_min": str(job["salary_min"] or ""),
                "salary_max": str(job["salary_max"] or ""),
                "url": job["url"],
                "category": job["category"],
                "description": job["description"],
            }
        )

    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    return len(ids)


def query_jobs(experience_text: str, n_results: int = 5) -> list[dict]:
    collection = get_collection()
    query_embedding = embed(experience_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["metadatas", "distances", "documents"],
    )

    jobs = []
    for i, metadata in enumerate(results["metadatas"][0] or []):
        description = metadata.get("description") or results["documents"][0][i]
        jobs.append(
            {
                **metadata,
                "id": metadata.get("id", ""),
                "description": description,
                "score": round(1 - results["distances"][0][i], 4),
            }
        )
    return jobs
