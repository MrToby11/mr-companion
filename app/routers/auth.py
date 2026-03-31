# app/routers/auth.py
# Authentication routes — login only for now.
# Registration is handled in users.py (POST /api/users/clients and /api/users/caregivers).
#
# NOTE: Login is currently a stub. It will look up users in the DB and return a real
# session token once SQLAlchemy is set up. For now it returns a placeholder response
# so the frontend can be wired up and tested end-to-end.
#
# Endpoints:
#   POST  /api/auth/login   — authenticate with email + password

import hashlib

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import store

router = APIRouter()


# --- Request / response schemas ---

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
    Checks clients, caregivers, and admins (in that order).

    TODO: Return a real session token / JWT once auth (AWS Cognito) is integrated.
          For now returns user_id and role so the frontend can navigate to the right page.
    """
    password_hash = _hash_password(req.password)

    # Check clients
    client = next((c for c in store.clients.values() if c.email == req.email), None)
    if client:
        if client.password_hash != password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return {"user_id": client.user_id, "role": "client", "full_name": client.full_name}

    # Check caregivers
    caregiver = next((c for c in store.caregivers.values() if c.email == req.email), None)
    if caregiver:
        if caregiver.password_hash != password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return {"user_id": caregiver.user_id, "role": "caregiver", "full_name": caregiver.full_name}

    # Check admins
    admin = next((a for a in store.admins.values() if a.email == req.email), None)
    if admin:
        if admin.password_hash != password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return {"user_id": admin.user_id, "role": "admin", "full_name": admin.full_name}

    raise HTTPException(status_code=401, detail="Invalid email or password")
