# app/routers/admin.py
# API routes for the admin portal.
#
# Endpoints:
#   GET  /api/admin/stats  — system-wide counts for the admin dashboard

from fastapi import APIRouter

from app.db import get_db

router = APIRouter()


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
