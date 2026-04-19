# Job Match CV

Paste a LinkedIn profile into the web app, get 5 job recommendations, select one, and generate a tailored resume/CV writing guide.

## What It Does

This project is a small full-stack prototype for job matching and resume guidance.

Flow:

1. The user copies the full text of a LinkedIn profile and pastes it into the web app.
2. The backend uses an LLM to extract job-relevant structured profile data.
3. The backend converts that into a semantic search summary and queries ChromaDB.
4. The app returns the top 5 matching jobs.
5. When the user selects one job, that selection is stored in SQLite.
6. For the selected job, the backend tries to fetch a fuller job page text.
7. The backend uses the candidate profile plus the selected job text to generate a tailored CV guide.

## Current Stack

- Frontend: Next.js 15, React 19, TypeScript
- Backend: FastAPI
- Vector store: ChromaDB
- Embedding model: `BAAI/bge-base-en-v1.5`
- LLM: OpenAI API
- Job source: Adzuna API
- Relational/event storage: SQLite

## Project Structure

```text
job-match-cv/
├─ backend/
│  ├─ api/
│  │  ├─ cv.py
│  │  ├─ jobs.py
│  │  └─ match.py
│  ├─ services/
│  │  ├─ adzuna.py
│  │  ├─ job_page.py
│  │  ├─ llm.py
│  │  ├─ profile_extractor.py
│  │  ├─ storage.py
│  │  └─ vector_store.py
│  ├─ chroma_db/
│  ├─ app.db
│  ├─ main.py
│  ├─ requirements.txt
│  └─ seed_jobs.py
├─ frontend/
│  ├─ src/
│  │  ├─ app/
│  │  └─ components/
│  ├─ package.json
│  └─ tsconfig.json
└─ README.md
```

## Core Backend Flow

### 1. Profile Extraction

`backend/services/profile_extractor.py`

The pasted LinkedIn text is converted into:

- `structured_profile`
- `search_text`

`search_text` is used for semantic retrieval.
`structured_profile` is stored for later analysis and CV generation.

### 2. Job Retrieval

`backend/services/vector_store.py`

Jobs are embedded into ChromaDB using:

- `title`
- `company`
- `description`

Stored metadata includes:

- `id`
- `title`
- `company`
- `location`
- `salary_min`
- `salary_max`
- `url`
- `category`
- `description`

### 3. Recommendation Logging

`backend/services/storage.py`

The backend stores:

- raw LinkedIn text
- extracted structured profile
- search summary
- recommendation session
- selected job

This is intended to support future recommender analysis and model improvement.

### 4. CV Guide Generation

`backend/api/cv.py`

When the user selects a job:

- the selection is logged
- the backend attempts to fetch a fuller job page text
- cached page text is reused when available
- the LLM generates a tailored CV guide

## Database

SQLite database path:

- [backend/app.db](C:\Users\USER\Desktop\대학교 자료\4-1학기(NYU)\Seminar in Applied ML&AI Tools for Technology Management\job-match-cv\backend\app.db)

Current tables:

- `profiles`
- `recommendation_sessions`
- `job_selections`
- `job_page_cache`

What this enables:

- analyze which recommended jobs users actually click/select
- compare profiles against chosen roles
- study company/category selection patterns
- later build a reranker or recommender using logged selections

## ChromaDB Contents

Current seeding strategy:

- 8 role keywords
- 2 pages per keyword
- 20 results per page

Current total after latest seed:

- 320 jobs

Keywords currently used:

- `data scientist`
- `data analyst`
- `machine learning engineer`
- `software engineer`
- `product manager`
- `business analyst`
- `data engineer`
- `AI engineer`

## Environment Variables

Backend example:

```env
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CV_MODEL=gpt-4o-mini
```

Frontend example:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Install

### Backend

```powershell
cd "C:\Users\USER\Desktop\대학교 자료\4-1학기(NYU)\Seminar in Applied ML&AI Tools for Technology Management\job-match-cv\backend"
py -3 -m pip install -r requirements.txt
```

### Frontend

```powershell
cd "C:\Users\USER\Desktop\대학교 자료\4-1학기(NYU)\Seminar in Applied ML&AI Tools for Technology Management\job-match-cv\frontend"
npm install
```

## Run

### 1. Start Backend

```powershell
cd "C:\Users\USER\Desktop\대학교 자료\4-1학기(NYU)\Seminar in Applied ML&AI Tools for Technology Management\job-match-cv\backend"
py -3 -m uvicorn main:app --reload --port 8000
```

### 2. Start Frontend

```powershell
cd "C:\Users\USER\Desktop\대학교 자료\4-1학기(NYU)\Seminar in Applied ML&AI Tools for Technology Management\job-match-cv\frontend"
npm run dev
```

### 3. Open the App

- [http://localhost:3000](http://localhost:3000)

Notes:

- `http://localhost:3000` is the actual user-facing website.
- `http://127.0.0.1:8000` is the backend API server.
- `http://127.0.0.1:8000/health` can be used as a health check.

## Seed Jobs from Adzuna

To rebuild the ChromaDB job store:

```powershell
cd "C:\Users\USER\Desktop\대학교 자료\4-1학기(NYU)\Seminar in Applied ML&AI Tools for Technology Management\job-match-cv\backend"
py -3 seed_jobs.py
```

What this currently does:

- deletes the existing Chroma collection
- fetches fresh jobs from Adzuna
- embeds the jobs
- stores them back into ChromaDB

## API Endpoints

### `POST /match/`

Input:

```json
{
  "experience": "full pasted LinkedIn text",
  "n_results": 5
}
```

Returns:

- `profile_id`
- `session_id`
- `search_text`
- `structured_profile`
- `matches`

### `POST /match/select`

Logs which recommended job the user selected.

### `POST /cv/guide`

Uses:

- stored candidate profile
- selected job metadata
- fuller job page text when available

Returns:

- generated CV guide text

## Current Limitations

- Recommendation quality depends on Adzuna coverage and the current keyword seed list.
- The embedding model is solid but not the strongest open model available.
- Job matching uses Adzuna snippet text, while fuller job text is fetched only after selection.
- Some Adzuna redirect URLs are blocked directly, so the backend falls back to Adzuna detail pages where possible.
- The current selection logging is useful, but still minimal for serious recommender analytics.

## Good Next Improvements

- store recommendation rank position for each selected job
- log non-click impressions as separate events
- add user/session identifiers beyond a single recommendation session
- improve query-side embedding prompts or upgrade the embedding model
- support scheduled job refresh
- add admin or analytics views for stored recommendation/select data

## Summary

This repository currently supports:

- LinkedIn paste to structured profile extraction
- semantic job recommendation from ChromaDB
- logging of selected jobs into SQLite
- fuller selected-job text extraction
- tailored CV guide generation

It is a practical prototype for testing job matching, resume guidance, and future recommendation-system analysis.
