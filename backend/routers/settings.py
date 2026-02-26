"""Settings router – super_admin only."""

import smtplib
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from auth import require_super_admin
from schemas import SettingsUpdate, TestEmailRequest

router = APIRouter(prefix="/settings", tags=["settings"])


def _load_settings(db) -> dict:
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    raw = {r["key"]: r["value"] for r in rows}
    return {
        "groq_api_key": raw.get("groq_api_key", ""),
        "llm_provider": raw.get("llm_provider", ""),
        "smtp_host": raw.get("smtp_host", ""),
        "smtp_port": raw.get("smtp_port", "587"),
        "smtp_user": raw.get("smtp_user", ""),
        "smtp_password": raw.get("smtp_password", ""),
        "default_max_scrolls": int(raw.get("default_max_scrolls", "3")),
        "default_max_inner_pages": int(raw.get("default_max_inner_pages", "5")),
        "default_content_limit": int(raw.get("default_content_limit", "10000")),
    }


@router.get("")
def get_settings(_: dict = Depends(require_super_admin)):
    db = get_db()
    try:
        return _load_settings(db)
    finally:
        db.close()


@router.put("")
def update_settings(body: SettingsUpdate, _: dict = Depends(require_super_admin)):
    updates = body.model_dump(exclude_none=True)
    db = get_db()
    try:
        for key, value in updates.items():
            db.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )
        db.commit()
        return _load_settings(db)
    finally:
        db.close()


@router.post("/test-email")
def test_email(body: TestEmailRequest, _: dict = Depends(require_super_admin)):
    db = get_db()
    try:
        settings = _load_settings(db)
    finally:
        db.close()

    smtp_host = settings.get("smtp_host", "")
    smtp_port = int(settings.get("smtp_port") or 587)
    smtp_user = settings.get("smtp_user", "")
    smtp_password = settings.get("smtp_password", "")

    if not smtp_host or not smtp_user:
        raise HTTPException(status_code=400, detail="SMTP not configured")

    try:
        msg = MIMEText("This is a test email from IntelliFetch.")
        msg["Subject"] = "IntelliFetch – Test Email"
        msg["From"] = smtp_user
        msg["To"] = body.to_email

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {exc}")

    return {"message": "Test email sent"}
