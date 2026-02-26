"""User management – create, list, update, delete users."""

from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from auth import hash_password, get_current_user, require_super_admin, require_admin_or_above
from schemas import UserCreate, UserUpdate, UserOut
from typing import List

router = APIRouter(prefix="/users", tags=["users"])


def _allowed_to_create(current_role: str, new_role: str) -> bool:
    """
    super_admin can create admins and users.
    admin can only create users.
    """
    if current_role == "super_admin":
        return new_role in ("admin", "user")
    if current_role == "admin":
        return new_role == "user"
    return False


@router.get("", response_model=List[UserOut])
def list_users(current_user: dict = Depends(get_current_user)):
    db = get_db()
    try:
        if current_user["role"] == "super_admin":
            # super_admin sees everyone
            rows = db.execute(
                "SELECT id, username, email, role, is_active, created_at, created_by FROM users ORDER BY created_at DESC"
            ).fetchall()
        elif current_user["role"] == "admin":
            # admin sees only users they created
            rows = db.execute(
                """SELECT id, username, email, role, is_active, created_at, created_by
                   FROM users WHERE created_by = ? ORDER BY created_at DESC""",
                (current_user["user_id"],),
            ).fetchall()
        else:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    finally:
        db.close()

    return [dict(r) for r in rows]


@router.post("", response_model=UserOut)
def create_user(body: UserCreate, current_user: dict = Depends(get_current_user)):
    if not _allowed_to_create(current_user["role"], body.role):
        raise HTTPException(
            status_code=403,
            detail=f"Your role ({current_user['role']}) cannot create a {body.role}",
        )

    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (body.username,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")

        hashed = hash_password(body.password)
        cursor = db.execute(
            """INSERT INTO users (username, email, hashed_password, role, created_by)
               VALUES (?, ?, ?, ?, ?)""",
            (body.username, body.email, hashed, body.role, current_user["user_id"]),
        )
        db.commit()
        row = db.execute(
            "SELECT id, username, email, role, is_active, created_at, created_by FROM users WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    finally:
        db.close()

    return dict(row)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    db = get_db()
    try:
        row = db.execute(
            "SELECT id, username, email, role, is_active, created_at, created_by FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        db.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    # Admins can only view users they created; super_admin can view anyone
    if current_user["role"] == "admin" and row["created_by"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user["role"] == "user" and row["id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return dict(row)


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    try:
        row = db.execute(
            "SELECT id, username, email, role, is_active, created_at, created_by FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        # Permission check
        if current_user["role"] == "admin" and row["created_by"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        if current_user["role"] == "user" and row["id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        updates = {}
        if body.email is not None:
            updates["email"] = body.email
        if body.password is not None:
            updates["hashed_password"] = hash_password(body.password)
        if body.is_active is not None and current_user["role"] in ("super_admin", "admin"):
            updates["is_active"] = 1 if body.is_active else 0

        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            db.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?",
                list(updates.values()) + [user_id],
            )
            db.commit()

        row = db.execute(
            "SELECT id, username, email, role, is_active, created_at, created_by FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        db.close()

    return dict(row)


@router.delete("/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    db = get_db()
    try:
        row = db.execute("SELECT id, role, created_by FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        # Cannot delete yourself
        if row["id"] == current_user["user_id"]:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")

        # Cannot delete super_admin
        if row["role"] == "super_admin":
            raise HTTPException(status_code=403, detail="Cannot delete super admin")

        # Admins can only delete their own users
        if current_user["role"] == "admin" and row["created_by"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        if current_user["role"] == "user":
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
    finally:
        db.close()

    return {"message": "User deleted"}
