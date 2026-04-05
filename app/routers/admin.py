# app/routers/admin.py
# API routes for the admin portal.
#
# Endpoints:
#   GET   /api/admin/stats                    — system-wide counts for the admin dashboard
#   GET   /api/admin/devices                  — all paired devices
#   GET   /api/admin/pricing                  — current plan prices
#   PATCH /api/admin/pricing                  — update a plan price
#   GET   /api/admin/reports/subscriptions    — subscription & payment summary
#   GET   /api/admin/reports/emergency        — recent emergency events log
#   GET   /api/admin/reports/usage            — device usage analysis

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_db

router = APIRouter()

# In-memory pricing store — resets on server restart, sufficient for demo/MVP.
# Keys match the planType values stored in the Subscriptions table.
_prices: dict[str, float] = {
    "standard": 19.99,
    "premium":  39.99,
}


# --- Request schemas ---

class UpdatePriceRequest(BaseModel):
    """Body for PATCH /api/admin/pricing"""
    plan_type: str   # "standard" or "premium"
    price:     float


# --- Routes ---

@router.get("/devices")
def get_all_devices():
    """Return all paired devices across all clients, for the admin device health table."""
    with get_db() as db:
        rows = db.execute(
            "SELECT deviceID, serialNumber, status, batteryLevel, wifiStatus, clientID FROM Device"
        ).fetchall()
    return [
        {
            "device_id":     r["deviceID"],
            "serial_number": r["serialNumber"],
            "status":        r["status"],
            "battery_level": r["batteryLevel"],
            "wifi_status":   r["wifiStatus"],
            "client_id":     r["clientID"],
        }
        for r in rows
    ]


@router.get("/stats")
def get_stats():
    """
    Return system-wide counts for the admin dashboard:
      - Total registered clients
      - Total paired devices
      - Total active subscriptions
      - Events logged in the last 30 days
    """
    with get_db() as db:
        clients       = db.execute("SELECT COUNT(*) FROM Client").fetchone()[0]
        devices       = db.execute("SELECT COUNT(*) FROM Device").fetchone()[0]
        subscriptions = db.execute("SELECT COUNT(*) FROM Subscriptions").fetchone()[0]
        events_30d    = db.execute(
            "SELECT COUNT(*) FROM Event WHERE eventTimestamp >= datetime('now', '-30 days')"
        ).fetchone()[0]

    return {
        "clients":       clients,
        "devices":       devices,
        "subscriptions": subscriptions,
        "events_30d":    events_30d,
    }


@router.get("/pricing")
def get_pricing():
    """Return the current monthly prices for each plan."""
    return {"standard": _prices["standard"], "premium": _prices["premium"]}


@router.patch("/pricing")
def update_pricing(req: UpdatePriceRequest):
    """Update the monthly price for a plan. Prices are held in memory for this session."""
    if req.plan_type not in _prices:
        raise HTTPException(status_code=400, detail=f"Unknown plan type: {req.plan_type}")
    if req.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")
    _prices[req.plan_type] = round(req.price, 2)
    return {"plan_type": req.plan_type, "price": _prices[req.plan_type]}


@router.get("/reports/subscriptions")
def report_subscriptions():
    """
    Return a summary of all subscriptions with payment totals.
    Joins Subscriptions → Users (for client name) → Payment (for payment history).
    """
    with get_db() as db:
        rows = db.execute(
            """
            SELECT
                u.fullName,
                u.email,
                s.planType,
                s.expiryDate,
                COUNT(p.paymentID)  AS paymentCount,
                COALESCE(SUM(p.amount), 0) AS totalPaid
            FROM Subscriptions s
            JOIN Users u ON u.userID = s.clientID
            LEFT JOIN Payment p ON p.subscriptionID = s.subscriptionID
            GROUP BY s.subscriptionID
            ORDER BY s.expiryDate DESC
            """
        ).fetchall()
    return [
        {
            "client_name":    r["fullName"],
            "email":          r["email"],
            "plan_type":      r["planType"],
            "expiry_date":    r["expiryDate"],
            "payment_count":  r["paymentCount"],
            "total_paid":     r["totalPaid"],
        }
        for r in rows
    ]


@router.get("/reports/emergency")
def report_emergency():
    """
    Return the 50 most recent emergency events with event type, device serial,
    and number of contacts notified.
    """
    with get_db() as db:
        rows = db.execute(
            """
            SELECT
                e.eventID,
                et.name            AS eventType,
                et.severityLevel,
                e.eventTimestamp,
                e.notes,
                d.serialNumber,
                COUNT(ec.contactID) AS contactsNotified
            FROM Event e
            JOIN EventType et ON et.eventTypeID = e.eventTypeID
            JOIN Device d    ON d.deviceID = e.deviceID
            LEFT JOIN EventContact ec ON ec.eventID = e.eventID
            GROUP BY e.eventID
            ORDER BY e.eventTimestamp DESC
            LIMIT 50
            """
        ).fetchall()
    return [
        {
            "event_id":          r["eventID"],
            "event_type":        r["eventType"],
            "severity":          r["severityLevel"],
            "timestamp":         r["eventTimestamp"],
            "notes":             r["notes"],
            "serial_number":     r["serialNumber"],
            "contacts_notified": r["contactsNotified"],
        }
        for r in rows
    ]


@router.get("/reports/usage")
def report_usage():
    """
    Return per-device usage: total events logged and timestamp of the most recent event.
    """
    with get_db() as db:
        rows = db.execute(
            """
            SELECT
                d.serialNumber,
                d.status,
                d.batteryLevel,
                u.fullName         AS clientName,
                COUNT(e.eventID)   AS totalEvents,
                MAX(e.eventTimestamp) AS lastEvent
            FROM Device d
            JOIN Users u ON u.userID = d.clientID
            LEFT JOIN Event e ON e.deviceID = d.deviceID
            GROUP BY d.deviceID
            ORDER BY totalEvents DESC
            """
        ).fetchall()
    return [
        {
            "serial_number": r["serialNumber"],
            "status":        r["status"],
            "battery_level": r["batteryLevel"],
            "client_name":   r["clientName"],
            "total_events":  r["totalEvents"],
            "last_event":    r["lastEvent"],
        }
        for r in rows
    ]
