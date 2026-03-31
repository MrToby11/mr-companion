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

from app import store
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
    if req.client_id not in store.clients:
        raise HTTPException(status_code=404, detail="Client not found")
    if any(d.serial_number == req.serial_number for d in store.devices.values()):
        raise HTTPException(status_code=400, detail="Device already paired")

    device = Device(serial_number=req.serial_number, client_id=req.client_id, status=DeviceStatus.PAIRING)
    store.devices[device.device_id] = device
    return {"device_id": device.device_id, "serial_number": device.serial_number, "status": device.status}


@router.get("/client/{client_id}")
def get_client_devices(client_id: str):
    """Return all devices registered to a given client."""
    devices = [d for d in store.devices.values() if d.client_id == client_id]
    return [
        {
            "device_id":     d.device_id,
            "serial_number": d.serial_number,
            "status":        d.status,
            "battery_level": d.battery_level,
            "wifi_status":   d.wifi_status,
        }
        for d in devices
    ]


@router.patch("/{device_id}")
def update_device(device_id: str, req: UpdateDeviceRequest):
    """
    Update one or more fields on a device.
    Called by the robot to report live status, or by the app to change settings.
    Only fields included in the request body are changed.
    """
    device = store.devices.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Apply only the fields that were provided
    if req.status        is not None: device.status        = req.status
    if req.battery_level is not None: device.battery_level = req.battery_level
    if req.wifi_status   is not None: device.wifi_status   = req.wifi_status

    return {"device_id": device.device_id, "status": device.status}
