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

from app.db import get_db
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
    Inserts into Users first, then Client (two-table inheritance from the schema).
    """
    with get_db() as db:
        if db.execute("SELECT 1 FROM Users WHERE email = ?", (req.email,)).fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        client = Client(
            full_name=req.full_name,
            email=req.email,
            password_hash=_hash_password(req.password),
            phone_number=req.phone_number,
            date_of_birth=req.date_of_birth,
            address=req.address,
        )
        db.execute(
            "INSERT INTO Users (userID, fullName, email, passwordHash, phoneNumber, accountStatus, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (client.user_id, client.full_name, client.email, client.password_hash, client.phone_number, client.account_status, client.created_at),
        )
        db.execute(
            "INSERT INTO Client (userID, dateOfBirth, address, medicalNotes) VALUES (?, ?, ?, ?)",
            (client.user_id, client.date_of_birth, client.address, client.medical_notes),
        )
    return {"user_id": client.user_id, "email": client.email}


@router.get("/clients/{user_id}")
def get_client(user_id: str):
    """Return a client's profile by their UUID. Does not return password_hash."""
    with get_db() as db:
        row = db.execute(
            "SELECT u.userID, u.fullName, u.email, u.phoneNumber, u.accountStatus "
            "FROM Users u JOIN Client c ON u.userID = c.userID WHERE u.userID = ?",
            (user_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return {
        "user_id":        row["userID"],
        "full_name":      row["fullName"],
        "email":          row["email"],
        "phone_number":   row["phoneNumber"],
        "account_status": row["accountStatus"],
    }


@router.post("/caregivers")
def register_caregiver(req: RegisterCaregiverRequest):
    """
    Register a new caregiver account.
    After registering, link them to a client via the CaregiverClient junction table.
    Inserts into Users first, then Caregiver (two-table inheritance from the schema).
    """
    with get_db() as db:
        if db.execute("SELECT 1 FROM Users WHERE email = ?", (req.email,)).fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        caregiver = Caregiver(
            full_name=req.full_name,
            email=req.email,
            password_hash=_hash_password(req.password),
            phone_number=req.phone_number,
            relationship_to_client=req.relationship_to_client,
        )
        db.execute(
            "INSERT INTO Users (userID, fullName, email, passwordHash, phoneNumber, accountStatus, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (caregiver.user_id, caregiver.full_name, caregiver.email, caregiver.password_hash, caregiver.phone_number, caregiver.account_status, caregiver.created_at),
        )
        db.execute(
            "INSERT INTO Caregiver (userID, relationshipToClient) VALUES (?, ?)",
            (caregiver.user_id, caregiver.relationship_to_client),
        )
    return {"user_id": caregiver.user_id, "email": caregiver.email}
