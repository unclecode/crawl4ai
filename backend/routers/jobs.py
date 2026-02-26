"""Jobs CRUD router."""

import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from auth import get_current_user, require_any_role
from schemas import JobCreate

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _row_to_job(row) -> dict:
    d = dict(row)
    if d.get("config") and isinstance(d["config"], str):
        try:
            d["config"] = json.loads(d["config"])
        except Exception:
            d["config"] = None
    return d


@router.get("")
def list_jobs(status: str = None, current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        query = "SELECT * FROM jobs"
        params: list = []
        conditions: list = []

        if status:
            conditions.append("status = ?")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"
        rows = db.execute(query, params).fetchall()
    finally:
        db.close()

    return [_row_to_job(r) for r in rows]


@router.get("/{job_id}")
def get_job(job_id: str, current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    finally:
        db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return _row_to_job(row)


@router.post("", status_code=201)
def create_job(body: JobCreate, current_user: dict = Depends(require_any_role)):
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    config_str = json.dumps(body.config) if body.config else None

    db = get_db()
    try:
        db.execute(
            """INSERT INTO jobs (id, name, url, status, created_at, config, created_by)
               VALUES (?, ?, ?, 'pending', ?, ?, ?)""",
            (job_id, body.name, body.url, now, config_str, current_user["user_id"]),
        )
        # If cron is provided, also create a schedule
        if body.cron:
            db.execute(
                """INSERT INTO schedules (job_name, url, cron, recipients, enabled, created_by)
                   VALUES (?, ?, ?, ?, 1, ?)""",
                (body.name, body.url, body.cron, body.recipients, current_user["user_id"]),
            )
        db.commit()
        row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    finally:
        db.close()

    return _row_to_job(row)


@router.post("/{job_id}/rerun")
def rerun_job(job_id: str, current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")

        new_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            """INSERT INTO jobs (id, name, url, status, created_at, config, created_by)
               VALUES (?, ?, ?, 'pending', ?, ?, ?)""",
            (new_id, row["name"], row["url"], now, row["config"], current_user["user_id"]),
        )
        db.commit()
        new_row = db.execute("SELECT * FROM jobs WHERE id = ?", (new_id,)).fetchone()
    finally:
        db.close()

    return _row_to_job(new_row)


@router.delete("/{job_id}")
def delete_job(job_id: str, current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        row = db.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        db.commit()
    finally:
        db.close()

    return {"message": "Job deleted"}


@router.get("/{job_id}/results")
def get_job_results(job_id: str, current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    finally:
        db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    # Stub: return empty results; integrate crawl4ai extraction here
    return {"job_id": job_id, "articles": [], "total": 0}
