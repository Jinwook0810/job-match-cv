import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                salary_min REAL,
                salary_max REAL,
                url TEXT NOT NULL,
                category TEXT NOT NULL,
                created TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'adzuna',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs (title);
            CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs (company);
            CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs (category);
            CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs (location);

            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_linkedin_text TEXT NOT NULL,
                structured_profile_json TEXT NOT NULL,
                search_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS recommendation_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                requested_top_k INTEGER NOT NULL,
                matches_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles (id)
            );

            CREATE TABLE IF NOT EXISTS job_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                profile_id INTEGER NOT NULL,
                job_id TEXT NOT NULL,
                selected_job_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES recommendation_sessions (id),
                FOREIGN KEY (profile_id) REFERENCES profiles (id)
            );

            CREATE TABLE IF NOT EXISTS job_browse_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                query_text TEXT NOT NULL,
                filters_json TEXT NOT NULL,
                results_json TEXT NOT NULL,
                result_count INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles (id)
            );

            CREATE TABLE IF NOT EXISTS job_browse_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                browse_event_id INTEGER NOT NULL,
                profile_id INTEGER NOT NULL,
                job_id TEXT NOT NULL,
                selected_job_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (browse_event_id) REFERENCES job_browse_events (id),
                FOREIGN KEY (profile_id) REFERENCES profiles (id)
            );

            CREATE TABLE IF NOT EXISTS job_page_cache (
                requested_url TEXT PRIMARY KEY,
                fetched_url TEXT NOT NULL,
                page_title TEXT NOT NULL,
                page_text TEXT NOT NULL,
                source TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def reset_jobs_table() -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM jobs")


def count_jobs() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM jobs").fetchone()
    return int(row["count"] if row is not None else 0)


def upsert_job_records(jobs: list[dict], source: str = "adzuna") -> int:
    rows = []
    for job in jobs:
        rows.append(
            (
                str(job.get("id") or ""),
                str(job.get("title") or ""),
                str(job.get("company") or ""),
                str(job.get("location") or ""),
                str(job.get("description") or ""),
                job.get("salary_min"),
                job.get("salary_max"),
                str(job.get("url") or ""),
                str(job.get("category") or ""),
                str(job.get("created") or ""),
                source,
            )
        )

    if not rows:
        return 0

    with _connect() as conn:
        conn.executemany(
            """
            INSERT INTO jobs (
                id, title, company, location, description,
                salary_min, salary_max, url, category, created, source, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                description = excluded.description,
                salary_min = excluded.salary_min,
                salary_max = excluded.salary_max,
                url = excluded.url,
                category = excluded.category,
                created = excluded.created,
                source = excluded.source,
                updated_at = CURRENT_TIMESTAMP
            """,
            rows,
        )
    return len(rows)


def search_job_records(query_text: str = "", role_terms: tuple[str, ...] = (), salary_floor: int = 0) -> list[dict]:
    clauses: list[str] = []
    params: list[object] = []

    lowered_query = query_text.strip().lower()
    if lowered_query:
        like_value = f"%{lowered_query}%"
        clauses.append(
            """
            (
                LOWER(title) LIKE ?
                OR LOWER(company) LIKE ?
                OR LOWER(location) LIKE ?
                OR LOWER(category) LIKE ?
                OR LOWER(description) LIKE ?
            )
            """.strip()
        )
        params.extend([like_value] * 5)

    if role_terms:
        role_clauses = []
        for term in role_terms:
            like_value = f"%{term.lower()}%"
            role_clauses.append(
                """
                (
                    LOWER(title) LIKE ?
                    OR LOWER(company) LIKE ?
                    OR LOWER(location) LIKE ?
                    OR LOWER(category) LIKE ?
                    OR LOWER(description) LIKE ?
                )
                """.strip()
            )
            params.extend([like_value] * 5)
        clauses.append(f"({' OR '.join(role_clauses)})")

    if salary_floor:
        clauses.append("COALESCE(salary_min, salary_max) >= ?")
        params.append(salary_floor)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT id, title, company, location, description, salary_min, salary_max, url, category, created, source
        FROM jobs
        {where_sql}
    """

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def create_profile(raw_linkedin_text: str, structured_profile: dict, search_text: str) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO profiles (raw_linkedin_text, structured_profile_json, search_text)
            VALUES (?, ?, ?)
            """,
            (raw_linkedin_text, json.dumps(structured_profile), search_text),
        )
        return int(cursor.lastrowid)


def create_recommendation_session(profile_id: int, requested_top_k: int, matches: list[dict]) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO recommendation_sessions (profile_id, requested_top_k, matches_json)
            VALUES (?, ?, ?)
            """,
            (profile_id, requested_top_k, json.dumps(matches)),
        )
        return int(cursor.lastrowid)


def get_profile(profile_id: int) -> tuple[str, dict, str]:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT raw_linkedin_text, structured_profile_json, search_text
            FROM profiles
            WHERE id = ?
            """,
            (profile_id,),
        ).fetchone()

    if row is None:
        raise ValueError("Profile not found")

    return row["raw_linkedin_text"], json.loads(row["structured_profile_json"]), row["search_text"]


def get_profile_for_session(session_id: int) -> tuple[str, dict]:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT p.raw_linkedin_text, p.structured_profile_json
            FROM recommendation_sessions s
            JOIN profiles p ON p.id = s.profile_id
            WHERE s.id = ?
            """,
            (session_id,),
        ).fetchone()

    if row is None:
        raise ValueError("Recommendation session not found")

    return row["raw_linkedin_text"], json.loads(row["structured_profile_json"])


def create_job_browse_event(profile_id: int, query_text: str, filters: dict, results: list[dict]) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO job_browse_events (profile_id, query_text, filters_json, results_json, result_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (profile_id, query_text, json.dumps(filters), json.dumps(results), len(results)),
        )
        return int(cursor.lastrowid)


def log_job_selection(session_id: int, job: dict) -> int:
    with _connect() as conn:
        session = conn.execute(
            "SELECT profile_id FROM recommendation_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()

        if session is None:
            raise ValueError("Recommendation session not found")

        job_id = str(job.get("id") or "")
        if not job_id:
            job_id = f"{job.get('title', 'unknown')}::{job.get('company', 'unknown')}"

        cursor = conn.execute(
            """
            INSERT INTO job_selections (session_id, profile_id, job_id, selected_job_json)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, int(session["profile_id"]), job_id, json.dumps(job)),
        )
        return int(cursor.lastrowid)


def log_job_browse_selection(browse_event_id: int, profile_id: int, job: dict) -> int:
    with _connect() as conn:
        browse_event = conn.execute(
            "SELECT id FROM job_browse_events WHERE id = ? AND profile_id = ?",
            (browse_event_id, profile_id),
        ).fetchone()

        if browse_event is None:
            raise ValueError("Browse event not found")

        job_id = str(job.get("id") or "")
        if not job_id:
            job_id = f"{job.get('title', 'unknown')}::{job.get('company', 'unknown')}"

        cursor = conn.execute(
            """
            INSERT INTO job_browse_selections (browse_event_id, profile_id, job_id, selected_job_json)
            VALUES (?, ?, ?, ?)
            """,
            (browse_event_id, profile_id, job_id, json.dumps(job)),
        )
        return int(cursor.lastrowid)


def get_cached_job_page(requested_url: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT requested_url, fetched_url, page_title, page_text, source, updated_at
            FROM job_page_cache
            WHERE requested_url = ?
            """,
            (requested_url,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def upsert_job_page_cache(
    requested_url: str,
    fetched_url: str,
    page_title: str,
    page_text: str,
    source: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO job_page_cache (requested_url, fetched_url, page_title, page_text, source, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(requested_url) DO UPDATE SET
                fetched_url = excluded.fetched_url,
                page_title = excluded.page_title,
                page_text = excluded.page_text,
                source = excluded.source,
                updated_at = CURRENT_TIMESTAMP
            """,
            (requested_url, fetched_url, page_title, page_text, source),
        )
