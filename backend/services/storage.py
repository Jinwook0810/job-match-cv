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
