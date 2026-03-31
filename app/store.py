# app/store.py
# Temporary in-memory storage for all application data.
# Acts as a stand-in for the database until SQLAlchemy (or another ORM) is set up.
# Each dict is keyed by the object's UUID primary key.
# When the DB is ready, replace these dicts with proper DB session queries —
# the router code that calls store.x won't need to change much.

from typing import Dict, List

from app.models.device import Device
from app.models.emergency import CaregiverClient, EmergencyContact, Event, EventContact, EventType, SeverityLevel
from app.models.subscription import Payment, Subscription
from app.models.user import Admin, Caregiver, Client

# User tables — split by role (matching the DB schema's inheritance structure)
clients:    Dict[str, Client]    = {}
caregivers: Dict[str, Caregiver] = {}
admins:     Dict[str, Admin]     = {}

# Robot devices — each device is linked to one client via client_id
devices: Dict[str, Device] = {}

# Subscription and payment records
subscriptions: Dict[str, Subscription] = {}
payments:      Dict[str, Payment]      = {}

# Emergency contacts per client, and the event log
emergency_contacts: Dict[str, EmergencyContact] = {}
events:             Dict[str, Event]             = {}

# Seed data: built-in event types that the robot can report
# These would normally come from the EventType table in the DB
event_types: Dict[int, EventType] = {
    1: EventType(event_type_id=1, name="Fall Detected",  severity_level=SeverityLevel.CRITICAL),
    2: EventType(event_type_id=2, name="Battery Low",    severity_level=SeverityLevel.INFO),
    3: EventType(event_type_id=3, name="Device Offline", severity_level=SeverityLevel.INFO),
}

# Junction tables — stored as lists since they use composite keys
event_contacts:    List[EventContact]    = []  # tracks which contacts were notified for each event
caregiver_clients: List[CaregiverClient] = []  # many-to-many: caregivers linked to clients