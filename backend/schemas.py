"""Pydantic request/response schemas."""

from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str  # "admin" or "user"


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: str
    created_by: Optional[int]


# ── Jobs ──────────────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    name: str
    url: str
    config: Optional[dict] = None
    recipients: Optional[str] = None
    cron: Optional[str] = None


class JobOut(BaseModel):
    id: str
    name: str
    url: str
    status: str
    created_at: str
    started_at: Optional[str]
    finished_at: Optional[str]
    article_count: int
    error: Optional[str]
    output_dir: Optional[str]
    config: Optional[dict]


# ── Schedules ─────────────────────────────────────────────────────────────────

class ScheduleCreate(BaseModel):
    job_name: str
    url: str
    cron: str
    recipients: Optional[str] = None
    config: Optional[dict] = None


class ScheduleToggle(BaseModel):
    enabled: bool


class ScheduleOut(BaseModel):
    id: int
    job_name: str
    url: str
    cron: str
    recipients: Optional[str]
    enabled: bool
    last_run: Optional[str]
    next_run: Optional[str]


# ── Settings (super_admin only) ───────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    groq_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    default_max_scrolls: Optional[int] = None
    default_max_inner_pages: Optional[int] = None
    default_content_limit: Optional[int] = None


class TestEmailRequest(BaseModel):
    to_email: str
