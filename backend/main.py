"""
IntelliFetch API – FastAPI entry point.

Roles:
  super_admin  Static credentials (env: SUPER_ADMIN_USERNAME / SUPER_ADMIN_PASSWORD).
               Full access including /settings. Can create admins and users.
  admin        Created by super_admin. Can add/invite users. No access to /settings.
  user         Created by admin. Can use jobs, schedules, dashboard.

Run:
  uvicorn main:app --reload --port 8000
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import auth, users, jobs, schedules, settings, stats

app = FastAPI(
    title="IntelliFetch API",
    description="Role-based API for the IntelliFetch web crawling platform",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,https://crawl4ai-web-production.up.railway.app",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()


# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(jobs.router, prefix=API_PREFIX)
app.include_router(schedules.router, prefix=API_PREFIX)
app.include_router(settings.router, prefix=API_PREFIX)
app.include_router(stats.router, prefix=API_PREFIX)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "intellifetch-api"}


@app.get("/")
def root():
    return {
        "service": "IntelliFetch API",
        "docs": "/docs",
        "health": "/health",
    }
