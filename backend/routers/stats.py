"""Stats router."""

from fastapi import APIRouter, Depends
from database import get_db
from auth import require_any_role

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def get_stats(_: dict = Depends(require_any_role)):
    db = get_db()
    try:
        total_jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        running_jobs = db.execute("SELECT COUNT(*) FROM jobs WHERE status = 'running'").fetchone()[0]
        completed_jobs = db.execute("SELECT COUNT(*) FROM jobs WHERE status = 'completed'").fetchone()[0]
        failed_jobs = db.execute("SELECT COUNT(*) FROM jobs WHERE status = 'failed'").fetchone()[0]
        total_articles = db.execute("SELECT COALESCE(SUM(article_count), 0) FROM jobs").fetchone()[0]
        active_schedules = db.execute("SELECT COUNT(*) FROM schedules WHERE enabled = 1").fetchone()[0]
    finally:
        db.close()

    return {
        "total_jobs": total_jobs,
        "running_jobs": running_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "total_articles": total_articles,
        "active_schedules": active_schedules,
    }
