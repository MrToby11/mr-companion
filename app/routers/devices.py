# app/routers/devices.py
# API routes for robot device pairing and status management.
# The physical robot calls PATCH /{device_id} to report its battery and Wi-Fi status.
#
# Endpoints:
#   POST   /api/devices/pair              — pair a new robot to a client account
#   GET    /api/devices/client/{id}       — list all devices belonging to a client
#   PATCH  /api/devices/{device_id}       — update a device's status/battery/wifi

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_db
from app.models.device import Device, DeviceStatus

router = APIRouter()


# --- Request schemas ---

class PairDeviceRequest(BaseModel):
    """Body for POST /api/devices/pair"""
    serial_number: str  # Printed on the robot hardware
    client_id:     str  # The client this device will belong to


class UpdateDeviceRequest(BaseModel):
    """
    Body for PATCH /api/devices/{device_id}.
    All fields are optional — only provided fields are updated.
    """
    status:        Optional[DeviceStatus] = None
    battery_level: Optional[int]          = None  # 0–100
    wifi_status:   Optional[str]          = None


# --- Routes ---

@router.post("/pair")
def pair_device(req: PairDeviceRequest):
    """
    Link a robot to a client account by serial number.
    Device starts in PAIRING status until Wi-Fi setup is confirmed.
    A serial number can only be paired once.
    """
    with get_db() as db:
        if not db.execute("SELECT 1 FROM Client WHERE userID = ?", (req.client_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Client not found")
        if db.execute("SELECT 1 FROM Device WHERE serialNumber = ?", (req.serial_number,)).fetchone():
            raise HTTPException(status_code=400, detail="Device already paired")

        device = Device(serial_number=req.serial_number, client_id=req.client_id, status=DeviceStatus.PAIRING)
        db.execute(
            "INSERT INTO Device (deviceID, serialNumber, clientID, status) VALUES (?, ?, ?, ?)",
            (device.device_id, device.serial_number, device.client_id, device.status),
        )
    return {"device_id": device.device_id, "serial_number": device.serial_number, "status": device.status}


@router.get("/client/{client_id}")
def get_client_devices(client_id: str):
    """Return all devices registered to a given client."""
    with get_db() as db:
        rows = db.execute(
            "SELECT deviceID, serialNumber, status, batteryLevel, wifiStatus FROM Device WHERE clientID = ?",
            (client_id,),
        ).fetchall()
    return [
        {
            "device_id":     r["deviceID"],
            "serial_number": r["serialNumber"],
            "status":        r["status"],
            "battery_level": r["batteryLevel"],
            "wifi_status":   r["wifiStatus"],
        }
        for r in rows
    ]


@router.patch("/{device_id}")
def update_device(device_id: str, req: UpdateDeviceRequest):
    """
    Update one or more fields on a device.
    Called by the robot to report live status, or by the app to change settings.
    Only fields included in the request body are changed.
    """
    with get_db() as db:
        if not db.execute("SELECT 1 FROM Device WHERE deviceID = ?", (device_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Device not found")

        if req.status        is not None: db.execute("UPDATE Device SET status = ? WHERE deviceID = ?",       (req.status,        device_id))
        if req.battery_level is not None: db.execute("UPDATE Device SET batteryLevel = ? WHERE deviceID = ?", (req.battery_level, device_id))
        if req.wifi_status   is not None: db.execute("UPDATE Device SET wifiStatus = ? WHERE deviceID = ?",   (req.wifi_status,   device_id))

        row = db.execute("SELECT status FROM Device WHERE deviceID = ?", (device_id,)).fetchone()
    return {"device_id": device_id, "status": row["status"]}
