# Job Match CV

Search New York jobs directly, or prepare a LinkedIn/resume profile for AI-based matching and CV tailoring.

## Overview

This project is a full-stack prototype for two related workflows:

1. `Search Jobs`
   Search and filter a stored New York job corpus directly, page through the results, and optionally group the filtered set with semantic clustering.
2. `Profile + AI Match`
   Paste LinkedIn text or upload a resume, extract a reusable profile representation with an LLM, retrieve top semantic matches, and generate a tailored CV guide for a selected role.

The system is intentionally split into:

- structured search and pagination from SQL
- semantic retrieval from a vector store
- LLM-based profile extraction and CV guidance

## Current Product Flow

### Search Jobs

1. The app loads a stored New York job corpus.
2. The user searches and filters by:
   - query text
   - role focus
   - salary floor
3. The user can:
   - browse paginated job results
   - or cluster the filtered result set with `PCA + K-means`
4. If a profile has already been prepared, selecting a searched job can generate a CV guide.

### Profile + AI Match

1. The user either:
   - pastes LinkedIn profile text
   - or uploads a resume (`.pdf`, `.docx`, `.txt`)
2. The backend uses an LLM to produce:
   - `structured_profile`
   - `search_text`
3. `search_text` is embedded and used to retrieve the top semantic matches from ChromaDB.
4. When the user selects a recommended role, the app logs the selection and generates a CV guide.

## Current Stack

- Frontend: Next.js 15, React 19, TypeScript
- Backend: FastAPI
- Relational storage: SQLite
- Vector storage: ChromaDB
- Embedding model: `BAAI/bge-base-en-v1.5`
- LLM: OpenAI API
- Job source: Adzuna API

## Data Architecture

The project now uses **both** SQLite and ChromaDB for the job corpus.

### SQLite

Path:

- [backend/app.db](C:\Users\USER\Desktop\대학교 자료\4-1학기(NYU)\Seminar in Applied ML&AI Tools for Technology Management\job-match-cv\backend\app.db)

Used for:

- `jobs` table for structured search, filtering, and pagination
- `profiles`
- `recommendation_sessions`
- `job_selections`
- `job_browse_events`
- `job_browse_selections`
- `job_page_cache`

### ChromaDB

Path:

- [backend/chroma_db](C:\Users\USER\Desktop\대학교 자료\4-1학기(NYU)\Seminar in Applied ML&AI Tools for Technology Management\job-match-cv\backend\chroma_db)

Used for:

- semantic job retrieval from embeddings

### Why Both?

- SQLite handles structured access well:
  - search
  - filtering
  - pagination
  - logging
  - future analytics
- ChromaDB handles semantic similarity retrieval well.

This is closer to a practical production-style split:

- SQL for structured data access
- vector DB for semantic matching

## Stored Job Corpus

Current Adzuna seed strategy:

- location: `New York`
- 17 role-oriented search keywords
- up to 3 pages per keyword
- 20 results per page

Current unique job count after the latest refresh:

- `924` jobs in SQLite
- `924` jobs in ChromaDB

Current seeded keywords:

- `data scientist`
- `data analyst`
- `business intelligence analyst`
- `machine learning engineer`
- `business analyst`
- `product analyst`
- `strategy analyst`
- `insights analyst`
- `operations analyst`
- `healthcare analyst`
- `market research analyst`
- `project manager`
- `program manager`
- `product manager`
- `management consultant`
- `data engineer`
- `AI engineer`

Each stored job record includes:

- `id`
- `title`
- `company`
- `location`
- `description`
- `salary_min`
- `salary_max`
- `url`
- `category`
- `created`

## AI and Data Science Components

### 1. Profile Representation

`backend/services/profile_extractor.py`

The backend converts raw LinkedIn/resume text into:

- `structured_profile`
- `search_text`

This makes the user profile usable for both:

- semantic retrieval
- later analytics / future recommendation modeling

### 2. Semantic Retrieval

`backend/services/vector_store.py`

Jobs are stored as embeddings derived from job text and queried with the profile search text.

This is the main recommendation engine for `AI Match`.

### 3. Job Clustering

`backend/services/job_clustering.py`

For the `Search Jobs` tab, the filtered result set can be grouped using:

- text embeddings from job title/category/description
- optional PCA dimensionality reduction
- K-means clustering

This is used as an exploratory job-discovery feature rather than the main recommendation engine.

### 4. CV Guide Generation

`backend/api/cv.py`

When a user selects a job:

- the app optionally logs the event
- tries to fetch fuller job text
- uses the selected job plus the prepared profile
- generates a tailored CV guide

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
│  │  ├─ document_parser.py
│  │  ├─ job_clustering.py
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
├─ README.md
├─ REPORT.md
├─ REPORT.docx
└─ REPORT.pdf
```

## API Summary

### Match / Profile Preparation

- `POST /match/profile`
  - prepare a profile from pasted LinkedIn text
- `POST /match/profile/upload`
  - prepare a profile from uploaded resume text
- `POST /match/recommend`
  - generate top semantic matches for a prepared profile
- `POST /match/select`
  - log a selected AI-recommended job

### Search / Browse

- `GET /jobs/browse`
  - structured search and pagination over the SQL job corpus
- `GET /jobs/cluster`
  - cluster the currently filtered result set with PCA + K-means
- `POST /jobs/browse/select`
  - log a selected searched/browsed job
- `POST /jobs/fetch`
  - fetch and store more jobs from Adzuna

### CV

- `POST /cv/guide`
  - generate a guide from an AI recommendation session
- `POST /cv/guide/profile`
  - generate a guide from a prepared profile and a searched job

### Health

- `GET /health`

## Environment Variables

### Backend

```env
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CV_MODEL=gpt-4o-mini
```

### Frontend

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

## Run Locally

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

- `http://localhost:3000` is the user-facing web app.
- `http://127.0.0.1:8000` is the backend API server.
- `http://127.0.0.1:8000/health` is the backend health check.

## Refresh the Job Corpus

To rebuild both the SQL job table and the ChromaDB collection from Adzuna:

```powershell
cd "C:\Users\USER\Desktop\대학교 자료\4-1학기(NYU)\Seminar in Applied ML&AI Tools for Technology Management\job-match-cv\backend"
py -3 seed_jobs.py
```

This currently:

- clears the SQL `jobs` table
- recreates the Chroma `jobs` collection
- fetches fresh Adzuna jobs
- writes them into both SQLite and ChromaDB

## Current Limitations

- Adzuna search descriptions are snippet-level, not full job postings.
- The `category` field is useful but too broad for fine-grained role filtering.
- Early-career filtering was removed because Adzuna does not expose a reliable seniority label in the public search API.
- The current clustering view is exploratory and heuristic; it is not a user-feedback-trained role taxonomy.
- The system logs interactions in SQLite, so the current architecture is better for local/demo use than for serverless production deployment.

## Why the Logging Layer Matters

The project already stores:

- prepared profiles
- recommendation sessions
- AI match selections
- browse/search events
- browse selections

This means the system can later support:

- click / selection analysis
- reranking experiments
- supervised recommendation models once enough interactions accumulate

## Summary

This repository currently supports:

- direct job search from a stored New York corpus
- pagination and structured SQL filtering
- semantic clustering over filtered result sets
- LinkedIn paste or resume upload for profile preparation
- semantic AI job matching with ChromaDB
- CV guide generation from either searched or recommended jobs
- user interaction logging for future recommendation-system analysis

It is a practical prototype for combining structured search, semantic retrieval, LLM-based profile understanding, and future recommender-system experimentation.
