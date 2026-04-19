from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import cv, jobs, match
from services.storage import init_db

app = FastAPI(title="Job Match CV API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(match.router, prefix="/match", tags=["match"])
app.include_router(cv.router, prefix="/cv", tags=["cv"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
