# app/routers/miro.py
# MiRo robot integration endpoints.
#
# miro_bridge.py runs in a Docker container with ROS Noetic and exposes a
# small HTTP API on localhost:5001. These endpoints proxy that API and tie
# the results into the application database.
#
# Endpoints:
#   GET  /api/miro/battery/{device_id}  — read battery % from simulator, persist to DB
#   POST /api/miro/alert/{device_id}    — flash LEDs red + play tone on the robot

import json
import urllib.error
import urllib.request

from fastapi import APIRouter, HTTPException

from app.db import get_db

router = APIRouter()

BRIDGE_URL = "http://localhost:5001"


def _call_bridge(path: str, method: str = "GET") -> dict:
    """Call the MiRo bridge. Returns parsed JSON or raises HTTPException."""
    req = urllib.request.Request(BRIDGE_URL + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError:
        raise HTTPException(
            status_code=503,
            detail=(
                "MiRo bridge is offline. "
                "Start it with: docker run --rm --network host miro-bridge"
            ),
        )


@router.get("/battery/{device_id}")
def sync_battery(device_id: str):
    """
    Read the current battery level from the MiRo simulator and update the
    device record in the database. Returns voltage and percentage.
    Requires miro_bridge.py to be running (see Dockerfile.miro).
    """
    with get_db() as db:
        if not db.execute("SELECT 1 FROM Device WHERE deviceID = ?", (device_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Device not found")

    data = _call_bridge("/battery")

    if "error" in data:
        raise HTTPException(status_code=503, detail=data["error"])

    with get_db() as db:
        db.execute(
            "UPDATE Device SET batteryLevel = ? WHERE deviceID = ?",
            (data["percent"], device_id),
        )

    return {
        "device_id":     device_id,
        "voltage":       data["voltage"],
        "battery_level": data["percent"],
    }


@router.post("/alert/{device_id}")
def trigger_robot_alert(device_id: str):
    """
    Signal the MiRo robot to flash its LEDs red and play a warning tone.
    Called automatically when an emergency event is triggered, and can be
    invoked directly for testing. Requires miro_bridge.py to be running.
    """
    with get_db() as db:
        if not db.execute("SELECT 1 FROM Device WHERE deviceID = ?", (device_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Device not found")

    _call_bridge("/alert", method="POST")
    return {"device_id": device_id, "alerted": True}
