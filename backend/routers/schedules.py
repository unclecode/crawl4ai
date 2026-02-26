"""Schedules CRUD router."""

from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from auth import get_current_user, require_any_role
from schemas import ScheduleCreate, ScheduleToggle

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("")
def list_schedules(current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM schedules ORDER BY created_at DESC"
        ).fetchall()
    finally:
        db.close()

    return [dict(r) for r in rows]


@router.get("/{schedule_id}")
def get_schedule(schedule_id: int, current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    finally:
        db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return dict(row)


@router.post("", status_code=201)
def create_schedule(body: ScheduleCreate, current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        cursor = db.execute(
            """INSERT INTO schedules (job_name, url, cron, recipients, enabled, created_by)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (body.job_name, body.url, body.cron, body.recipients, current_user["user_id"]),
        )
        db.commit()
        row = db.execute("SELECT * FROM schedules WHERE id = ?", (cursor.lastrowid,)).fetchone()
    finally:
        db.close()

    return dict(row)


@router.put("/{schedule_id}/toggle")
def toggle_schedule(
    schedule_id: int,
    body: ScheduleToggle,
    current_user: dict = Depends(require_any_role),
):
    db = get_db()
    try:
        row = db.execute("SELECT id FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        db.execute(
            "UPDATE schedules SET enabled = ? WHERE id = ?",
            (1 if body.enabled else 0, schedule_id),
        )
        db.commit()
        row = db.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    finally:
        db.close()

    return dict(row)


@router.post("/{schedule_id}/run-now")
def run_schedule_now(schedule_id: int, current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        # Stub: trigger the job immediately (integrate with crawl4ai task queue here)
    finally:
        db.close()

    return {"message": "Schedule triggered", "schedule_id": schedule_id}


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, current_user: dict = Depends(require_any_role)):
    db = get_db()
    try:
        row = db.execute("SELECT id FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        db.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
        db.commit()
    finally:
        db.close()

    return {"message": "Schedule deleted"}
