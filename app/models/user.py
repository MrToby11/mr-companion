# app/models/user.py
# User-related data classes based on the GP-3 class diagram.
# User is the base class. Client, Caregiver, and Admin extend it with role-specific fields.
# This mirrors the database's table-per-subclass inheritance (Users + Client/Caregiver/Admin tables).

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class AccountStatus(str, Enum):
    """Whether the user account is usable. Suspended blocks login."""
    ACTIVE    = "active"
    INACTIVE  = "inactive"
    SUSPENDED = "suspended"


@dataclass
class User:
    """
    Base class for all user types.
    Stores credentials and contact info shared by Client, Caregiver, and Admin.
    Passwords are never stored in plain text — always pass a hashed value to password_hash.
    """
    full_name:      str
    email:          str
    password_hash:  str           # SHA-256 hash — see _hash_password() in routers/users.py
    phone_number:   str
    account_status: AccountStatus = AccountStatus.ACTIVE
    user_id:        str           = field(default_factory=lambda: str(uuid4()))  # UUID primary key
    created_at:     datetime      = field(default_factory=datetime.utcnow)


@dataclass
class Client(User):
    """
    An elderly user who owns a robot.
    Can register emergency contacts, manage subscriptions, and trigger/cancel alerts.
    """
    date_of_birth: Optional[str] = None
    address:       Optional[str] = None
    medical_notes: Optional[str] = None  # Visible to caregivers during emergencies


@dataclass
class Caregiver(User):
    """
    A family member or trusted person linked to one or more Clients.
    Receives emergency alerts and can acknowledge them.
    Linked to clients via the CaregiverClient junction table.
    """
    relationship_to_client: Optional[str] = None  # e.g. "Spouse", "Child"


@dataclass
class Admin(User):
    """
    An ABC Tech Ltd staff member.
    Can view reports, manage pricing plans, and monitor device health.
    """
    employee_id: Optional[str] = None
