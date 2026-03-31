# app/models/emergency.py
# Data classes for the emergency alert system and event logging.
# Also contains CaregiverClient, the junction table linking caregivers to clients.
#
# Emergency flow (from GP-2 use cases):
#   Robot detects event → 30s confirmation window → notify caregivers in priority order
#   → if no acknowledgement → escalate to emergency services (simulated, not a real call)

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class SeverityLevel(str, Enum):
    """How urgent an event type is."""
    CRITICAL = "critical"  # Requires immediate response (e.g. fall detected)
    INFO     = "info"      # Informational only (e.g. battery low)


class NotificationStatus(str, Enum):
    """Tracks where a contact is in the notification workflow."""
    SENT      = "sent"       # Alert dispatched
    DELIVERED = "delivered"  # Confirmed received
    FAILED    = "failed"     # Could not reach contact
    RESPONDED = "responded"  # Contact acknowledged the alert


@dataclass
class EmergencyContact:
    """
    A person to notify when the client's robot detects an emergency.
    priority_order determines the order contacts are called (1 = first).
    Contacts for a client are always fetched sorted by priority_order.
    """
    client_id:      str
    name:           str
    phone_number:   str
    relationship:   str  # e.g. "Spouse", "Child"
    priority_order: int  # 1–5; lower number = contacted first
    contact_id:     str  = field(default_factory=lambda: str(uuid4()))


@dataclass
class EventType:
    """
    A category of event the robot can report (e.g. "Fall Detected").
    Seeded in store.py — would come from the EventType DB table in production.
    """
    name:           str
    severity_level: SeverityLevel
    event_type_id:  int = 0


@dataclass
class Event:
    """
    A single incident reported by a device.
    Logged permanently for medical/legal accountability.
    All events must be stored on Canadian servers (data sovereignty requirement).
    """
    device_id:       str
    event_type_id:   int
    event_timestamp: datetime      = field(default_factory=datetime.utcnow)
    notes:           Optional[str] = None
    event_id:        str           = field(default_factory=lambda: str(uuid4()))


@dataclass
class EventContact:
    """
    Junction table: records which emergency contacts were notified for a given event,
    and whether they acknowledged it.
    """
    event_id:       str
    contact_id:     str
    status:         NotificationStatus = NotificationStatus.SENT
    notified_at:    Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None


@dataclass
class CaregiverClient:
    """
    Junction table: links a Caregiver to a Client (many-to-many).
    One caregiver can look after multiple clients, and one client can have multiple caregivers.
    """
    caregiver_id: str  # FK → Caregiver.user_id
    client_id:    str  # FK → Client.user_id
