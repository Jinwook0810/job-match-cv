from collections import Counter
import os
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from services.vector_store import get_model

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

STOPWORDS = {
    "a",
    "an",
    "and",
    "analyst",
    "associate",
    "business",
    "data",
    "engineer",
    "entry",
    "for",
    "in",
    "jobs",
    "junior",
    "lead",
    "level",
    "manager",
    "new",
    "ny",
    "nyc",
    "of",
    "on",
    "project",
    "program",
    "role",
    "senior",
    "the",
    "to",
    "york",
}


def _cluster_text(job: dict[str, Any]) -> str:
    return " ".join(
        [
            str(job.get("title") or ""),
            str(job.get("category") or ""),
            str(job.get("description") or ""),
        ]
    ).strip()


def _cluster_label(cluster_jobs: list[dict[str, Any]]) -> tuple[str, str]:
    categories = Counter(str(job.get("category") or "").strip() for job in cluster_jobs if job.get("category"))
    titles = Counter()
    for job in cluster_jobs:
        title = str(job.get("title") or "").lower()
        for token in title.replace("/", " ").replace("-", " ").split():
            token = token.strip(".,()")
            if len(token) < 3 or token in STOPWORDS:
                continue
            titles[token] += 1

    top_tokens = [token.title() for token, _ in titles.most_common(2)]
    if top_tokens:
        label = " / ".join(top_tokens) + " Roles"
    elif categories:
        label = categories.most_common(1)[0][0]
    else:
        label = "Related Roles"

    summary_parts = []
    if categories:
        top_categories = [name for name, _ in categories.most_common(2)]
        summary_parts.append("Mostly " + ", ".join(top_categories))
    if cluster_jobs:
        summary_parts.append(f"{len(cluster_jobs)} jobs")

    return label, " • ".join(summary_parts)


def cluster_jobs(jobs: list[dict[str, Any]], requested_clusters: int = 5) -> dict[str, Any]:
    if len(jobs) < 3:
        raise ValueError("At least 3 jobs are needed for clustering")

    texts = [_cluster_text(job) for job in jobs]
    embeddings = get_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)

    actual_clusters = max(2, min(requested_clusters, len(jobs)))
    features = np.asarray(embeddings)
    pca_components = None

    max_components = min(features.shape[0] - 1, features.shape[1], 100)
    if max_components >= actual_clusters and max_components >= 8:
        pca = PCA(n_components=max_components, random_state=42)
        features = pca.fit_transform(features)
        pca_components = max_components

    model = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
    assignments = model.fit_predict(features)

    grouped: dict[int, list[dict[str, Any]]] = {index: [] for index in range(actual_clusters)}
    for job, cluster_id in zip(jobs, assignments, strict=True):
        grouped[int(cluster_id)].append(job)

    clusters = []
    for cluster_id, cluster_members in grouped.items():
        cluster_members.sort(key=lambda job: str(job.get("title") or ""))
        label, summary = _cluster_label(cluster_members)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "label": label,
                "summary": summary,
                "job_count": len(cluster_members),
                "jobs": cluster_members,
            }
        )

    clusters.sort(key=lambda cluster: (-int(cluster["job_count"]), str(cluster["label"])))
    return {
        "cluster_count": actual_clusters,
        "pca_components": pca_components,
        "clusters": clusters,
    }
