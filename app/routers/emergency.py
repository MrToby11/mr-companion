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

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import store
from app.models.emergency import EmergencyContact, Event, EventContact, NotificationStatus

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
    event_type_id: int           # Must match a key in store.event_types (1=Fall, 2=Battery, 3=Offline)
    notes:         Optional[str] = None


# --- Routes ---

@router.post("/contacts")
def add_emergency_contact(req: AddContactRequest):
    """
    Register an emergency contact for a client.
    Up to 5 contacts are recommended (priority_order 1–5), but not enforced here.
    """
    if req.client_id not in store.clients:
        raise HTTPException(status_code=404, detail="Client not found")

    contact = EmergencyContact(
        client_id=req.client_id,
        name=req.name,
        phone_number=req.phone_number,
        relationship=req.relationship,
        priority_order=req.priority_order,
    )
    store.emergency_contacts[contact.contact_id] = contact
    return {"contact_id": contact.contact_id, "name": contact.name, "priority_order": contact.priority_order}


@router.get("/contacts/client/{client_id}")
def get_emergency_contacts(client_id: str):
    """
    Return all emergency contacts for a client, sorted by priority_order ascending.
    The sort here mirrors the index on (clientID, priorityOrder) in the DB schema.
    """
    contacts = sorted(
        [c for c in store.emergency_contacts.values() if c.client_id == client_id],
        key=lambda c: c.priority_order,
    )
    return [
        {
            "contact_id":     c.contact_id,
            "name":           c.name,
            "phone_number":   c.phone_number,
            "relationship":   c.relationship,
            "priority_order": c.priority_order,
        }
        for c in contacts
    ]


@router.post("/events")
def trigger_event(req: TriggerEventRequest):
    """
    Log an event from a device and simulate notifying the client's emergency contacts.
    Contacts are notified in priority_order (lowest first).
    In production, this would send real SMS/calls — here it just creates EventContact records.
    Escalation to emergency services would be handled by a background task after a timeout.
    """
    if req.device_id not in store.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    if req.event_type_id not in store.event_types:
        raise HTTPException(status_code=400, detail="Unknown event type")

    # Log the event
    event = Event(device_id=req.device_id, event_type_id=req.event_type_id, notes=req.notes)
    store.events[event.event_id] = event

    # Look up which client owns this device, then get their contacts in priority order
    device = store.devices[req.device_id]
    contacts = sorted(
        [c for c in store.emergency_contacts.values() if c.client_id == device.client_id],
        key=lambda c: c.priority_order,
    )

    # Create an EventContact record for each contact to track notification status
    for contact in contacts:
        store.event_contacts.append(
            EventContact(
                event_id=event.event_id,
                contact_id=contact.contact_id,
                status=NotificationStatus.SENT,
                notified_at=datetime.utcnow(),
            )
        )

    return {
        "event_id":          event.event_id,
        "event_type":        store.event_types[req.event_type_id].name,
        "contacts_notified": len(contacts),
    }
