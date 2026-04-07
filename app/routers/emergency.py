# app/routers/emergency.py
# API routes for emergency contacts and event triggering.
# The emergency alert flow is: robot reports an event → contacts are notified in
# priority order → if no acknowledgement, escalate to emergency services.
# Real SMS/phone calls are out of scope — this router logs and simulates them.
#
# Endpoints:
#   POST  /api/emergency/contacts                  — add an emergency contact for a client
#   GET   /api/emergency/contacts/client/{id}      — list a client's contacts (sorted by priority)
#   POST  /api/emergency/events                    — trigger an event and notify contacts

import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_db
from app.models.emergency import EmergencyContact, Event, NotificationStatus

router = APIRouter()


# --- Request schemas ---

class AddContactRequest(BaseModel):
    """Body for POST /api/emergency/contacts"""
    client_id:      str
    name:           str
    phone_number:   str
    relationship:   str
    priority_order: int  # 1 = called first, higher numbers = called later


class TriggerEventRequest(BaseModel):
    """Body for POST /api/emergency/events"""
    device_id:     str
    event_type_id: int           # Must match a row in the EventType table (1=Fall, 2=Battery, 3=Offline)
    notes:         Optional[str] = None


# --- Routes ---

@router.post("/contacts")
def add_emergency_contact(req: AddContactRequest):
    """
    Register an emergency contact for a client.
    Up to 5 contacts are recommended (priority_order 1–5), but not enforced here.
    """
    with get_db() as db:
        if not db.execute("SELECT 1 FROM Client WHERE userID = ?", (req.client_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Client not found")

        contact = EmergencyContact(
            client_id=req.client_id,
            name=req.name,
            phone_number=req.phone_number,
            relationship=req.relationship,
            priority_order=req.priority_order,
        )
        db.execute(
            "INSERT INTO EmergencyContact (contactID, clientID, name, phoneNumber, relationship, priorityOrder) VALUES (?, ?, ?, ?, ?, ?)",
            (contact.contact_id, contact.client_id, contact.name, contact.phone_number, contact.relationship, contact.priority_order),
        )
    return {"contact_id": contact.contact_id, "name": contact.name, "priority_order": contact.priority_order}


@router.get("/contacts/client/{client_id}")
def get_emergency_contacts(client_id: str):
    """
    Return all emergency contacts for a client, sorted by priority_order ascending.
    ORDER BY in the query mirrors the index on (clientID, priorityOrder) in the schema.
    """
    with get_db() as db:
        rows = db.execute(
            "SELECT contactID, name, phoneNumber, relationship, priorityOrder "
            "FROM EmergencyContact WHERE clientID = ? ORDER BY priorityOrder",
            (client_id,),
        ).fetchall()
    return [
        {
            "contact_id":     r["contactID"],
            "name":           r["name"],
            "phone_number":   r["phoneNumber"],
            "relationship":   r["relationship"],
            "priority_order": r["priorityOrder"],
        }
        for r in rows
    ]


@router.post("/events")
def trigger_event(req: TriggerEventRequest):
    """
    Log an event from a device and simulate notifying the client's emergency contacts.
    Contacts are notified in priority_order (lowest first).
    In production, this would send real SMS/calls — here it just creates EventContact records.
    Escalation to emergency services would be handled by a background task after a timeout.
    """
    with get_db() as db:
        device_row = db.execute(
            "SELECT clientID FROM Device WHERE deviceID = ?", (req.device_id,)
        ).fetchone()
        if not device_row:
            raise HTTPException(status_code=404, detail="Device not found")

        event_type_row = db.execute(
            "SELECT name FROM EventType WHERE eventTypeID = ?", (req.event_type_id,)
        ).fetchone()
        if not event_type_row:
            raise HTTPException(status_code=400, detail="Unknown event type")

        event = Event(device_id=req.device_id, event_type_id=req.event_type_id, notes=req.notes)
        db.execute(
            "INSERT INTO Event (eventID, deviceID, eventTypeID, eventTimestamp, notes) VALUES (?, ?, ?, ?, ?)",
            (event.event_id, event.device_id, event.event_type_id, event.event_timestamp, event.notes),
        )

        contacts = db.execute(
            "SELECT contactID FROM EmergencyContact WHERE clientID = ? ORDER BY priorityOrder",
            (device_row["clientID"],),
        ).fetchall()

        now = datetime.utcnow()
        for contact in contacts:
            db.execute(
                "INSERT INTO EventContact (eventID, contactID, notifiedAt, status) VALUES (?, ?, ?, ?)",
                (event.event_id, contact["contactID"], now, NotificationStatus.SENT),
            )

    # Best-effort: signal the robot to alert (LEDs + tone). Does not fail the
    # request if the MiRo bridge is offline — emergency logging still succeeds.
    try:
        urllib.request.urlopen(
            urllib.request.Request(
                f"http://localhost:5001/alert", method="POST"
            ),
            timeout=3,
        )
    except Exception:
        pass

    return {
        "event_id":          event.event_id,
        "event_type":        event_type_row["name"],
        "contacts_notified": len(contacts),
    }
