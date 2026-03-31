# app/routers/users.py
# API routes for user registration and lookup.
# Handles Clients (elderly users) and Caregivers.
# Admins are not registered via the API — they would be created directly in the DB.
#
# Endpoints:
#   POST   /api/users/clients         — register a new client
#   GET    /api/users/clients/{id}    — get a client's profile
#   POST   /api/users/caregivers      — register a new caregiver

import hashlib
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import store
from app.models.user import Caregiver, Client

router = APIRouter()


# --- Request schemas (Pydantic validates incoming JSON against these) ---

class RegisterClientRequest(BaseModel):
    """Body for POST /api/users/clients"""
    full_name:     str
    email:         str
    password:      str           # Plain text — hashed before storing
    phone_number:  str
    date_of_birth: Optional[str] = None
    address:       Optional[str] = None


class RegisterCaregiverRequest(BaseModel):
    """Body for POST /api/users/caregivers"""
    full_name:              str
    email:                  str
    password:               str
    phone_number:           str
    relationship_to_client: Optional[str] = None


# --- Helpers ---

def _hash_password(password: str) -> str:
    """SHA-256 hash a plain-text password before storing it."""
    return hashlib.sha256(password.encode()).hexdigest()


# --- Routes ---

@router.post("/clients")
def register_client(req: RegisterClientRequest):
    """
    Register a new elderly client account.
    Rejects duplicate emails since email is used as a unique identifier for login.
    """
    # Check for duplicate email across all existing clients
    if any(c.email == req.email for c in store.clients.values()):
        raise HTTPException(status_code=400, detail="Email already registered")

    client = Client(
        full_name=req.full_name,
        email=req.email,
        password_hash=_hash_password(req.password),
        phone_number=req.phone_number,
        date_of_birth=req.date_of_birth,
        address=req.address,
    )
    store.clients[client.user_id] = client
    return {"user_id": client.user_id, "email": client.email}


@router.get("/clients/{user_id}")
def get_client(user_id: str):
    """Return a client's profile by their UUID. Does not return password_hash."""
    client = store.clients.get(user_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return {
        "user_id":        client.user_id,
        "full_name":      client.full_name,
        "email":          client.email,
        "phone_number":   client.phone_number,
        "account_status": client.account_status,
    }


@router.post("/caregivers")
def register_caregiver(req: RegisterCaregiverRequest):
    """
    Register a new caregiver account.
    After registering, link them to a client via the CaregiverClient junction table.
    """
    if any(c.email == req.email for c in store.caregivers.values()):
        raise HTTPException(status_code=400, detail="Email already registered")

    caregiver = Caregiver(
        full_name=req.full_name,
        email=req.email,
        password_hash=_hash_password(req.password),
        phone_number=req.phone_number,
        relationship_to_client=req.relationship_to_client,
    )
    store.caregivers[caregiver.user_id] = caregiver
    return {"user_id": caregiver.user_id, "email": caregiver.email}
