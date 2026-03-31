# app/models/device.py
# Represents a physical Mr. Companion robot unit.
# Each device belongs to one Client and reports its status to the cloud.

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import uuid4


class DeviceStatus(str, Enum):
    """Current connectivity state of the robot."""
    ONLINE  = "online"   # Connected and operating normally
    OFFLINE = "offline"  # Not reachable
    PAIRING = "pairing"  # Newly registered, not yet fully configured


@dataclass
class Device:
    """
    A robot unit linked to a client account.
    The physical robot updates battery_level and wifi_status by calling PATCH /api/devices/{id}.
    """
    serial_number: str          # Printed on the robot, used during pairing
    client_id:     str          # FK → Client.user_id
    status:        DeviceStatus = DeviceStatus.OFFLINE
    battery_level: Optional[int] = None  # Percentage 0–100
    wifi_status:   Optional[str] = None  # e.g. "connected", "disconnected"
    device_id:     str           = field(default_factory=lambda: str(uuid4()))  # UUID primary key
