# app/models/subscription.py
# Subscription and payment data classes.
# Each client can have at most one active subscription (enforced in the router).
# Payments are simulated — no real payment processor is integrated.

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class PlanType(str, Enum):
    """Available subscription tiers."""
    STANDARD = "standard"  # Basic features: emergency alerts, caregiver notifications
    PREMIUM  = "premium"   # Adds camera/microphone access and unlimited logs


class PaymentStatus(str, Enum):
    """Result of a payment attempt."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED  = "failed"


@dataclass
class Subscription:
    """
    A client's active plan. Only one subscription is allowed per client.
    Even if a subscription is inactive/expired, basic emergency alerts to EMS are always allowed.
    """
    client_id:       str                = field()                               # FK → Client.user_id
    plan_type:       PlanType           = PlanType.STANDARD
    expiry_date:     Optional[datetime] = None                                  # Set to 30 days from creation
    subscription_id: str                = field(default_factory=lambda: str(uuid4()))


@dataclass
class Payment:
    """
    A single payment transaction linked to a subscription.
    simulate_success in the router controls whether this comes back SUCCESS or FAILED.
    """
    subscription_id: str
    amount:          float
    payment_method:  str           # e.g. "credit_card", "paypal" — free-form for now
    payment_status:  PaymentStatus = PaymentStatus.PENDING
    payment_date:    datetime      = field(default_factory=datetime.utcnow)
    payment_id:      str           = field(default_factory=lambda: str(uuid4()))
