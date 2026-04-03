# app/routers/auth.py
# Authentication routes — login only for now.
# Registration is handled in users.py (POST /api/users/clients and /api/users/caregivers).
#
# NOTE: This is a simple credential check. A real session token / JWT would be added
# once AWS Cognito auth is integrated. For now, returns user_id and role so the frontend
# can navigate to the right page after login.
#
# Endpoints:
#   POST  /api/auth/login   — authenticate with email + password

import hashlib

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_db

router = APIRouter()


# --- Request schema ---

class LoginRequest(BaseModel):
    """Body for POST /api/auth/login"""
    email:    str
    password: str


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# --- Routes ---

@router.post("/login")
def login(req: LoginRequest):
    """
    Authenticate a user by email and password.
    Looks up the Users table first, then checks which role sub-table the user belongs to.

    TODO: Return a real session token / JWT once auth (AWS Cognito) is integrated.
          For now returns user_id and role so the frontend can navigate to the right page.
    """
    password_hash = _hash_password(req.password)

    with get_db() as db:
        row = db.execute(
            "SELECT userID, fullName, passwordHash FROM Users WHERE email = ?",
            (req.email,),
        ).fetchone()

        if not row or row["passwordHash"] != password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_id   = row["userID"]
        full_name = row["fullName"]

        if db.execute("SELECT 1 FROM Client WHERE userID = ?",    (user_id,)).fetchone():
            return {"user_id": user_id, "role": "client",    "full_name": full_name}
        if db.execute("SELECT 1 FROM Caregiver WHERE userID = ?", (user_id,)).fetchone():
            return {"user_id": user_id, "role": "caregiver", "full_name": full_name}
        if db.execute("SELECT 1 FROM Admin WHERE userID = ?",     (user_id,)).fetchone():
            return {"user_id": user_id, "role": "admin",     "full_name": full_name}

    raise HTTPException(status_code=401, detail="Invalid email or password")
