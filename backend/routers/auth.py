"""Authentication router – login and me endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from auth import verify_password, create_access_token, get_current_user
from schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1", (body.username,)
        ).fetchone()
    finally:
        db.close()

    if not row or not verify_password(body.password, row["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {
        "sub": row["username"],
        "user_id": row["id"],
        "role": row["role"],
    }
    token = create_access_token(token_data)

    return TokenResponse(
        access_token=token,
        user={
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "role": row["role"],
        },
    )


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    db = get_db()
    try:
        row = db.execute(
            "SELECT id, username, email, role, is_active FROM users WHERE id = ?",
            (current_user["user_id"],),
        ).fetchone()
    finally:
        db.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return dict(row)
