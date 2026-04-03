# app/routers/subscriptions.py
# API routes for managing client subscriptions and processing payments.
# Payment processing is simulated — no real payment gateway is connected.
#
# Endpoints:
#   POST  /api/subscriptions                    — create a subscription for a client
#   GET   /api/subscriptions/client/{client_id} — get a client's current subscription
#   POST  /api/subscriptions/payments           — process (simulated) payment

from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_db
from app.models.subscription import Payment, PaymentStatus, PlanType, Subscription

router = APIRouter()


# --- Request schemas ---

class CreateSubscriptionRequest(BaseModel):
    """Body for POST /api/subscriptions"""
    client_id: str
    plan_type: PlanType = PlanType.STANDARD


class ProcessPaymentRequest(BaseModel):
    """
    Body for POST /api/subscriptions/payments.
    simulate_success lets us test both success and failure paths without a real gateway.
    """
    subscription_id:  str
    amount:           float
    payment_method:   str
    simulate_success: bool = True  # Set to False to simulate a declined payment


# --- Routes ---

@router.post("/")
def create_subscription(req: CreateSubscriptionRequest):
    """
    Create a new subscription for a client.
    Enforces the one-subscription-per-client business rule from GP-3.
    Expiry is set to 30 days from creation.
    """
    with get_db() as db:
        if not db.execute("SELECT 1 FROM Client WHERE userID = ?", (req.client_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Client not found")
        if db.execute("SELECT 1 FROM Subscriptions WHERE clientID = ?", (req.client_id,)).fetchone():
            raise HTTPException(status_code=400, detail="Client already has a subscription")

        sub = Subscription(
            client_id=req.client_id,
            plan_type=req.plan_type,
            expiry_date=datetime.utcnow() + timedelta(days=30),
        )
        db.execute(
            "INSERT INTO Subscriptions (subscriptionID, clientID, planType, expiryDate) VALUES (?, ?, ?, ?)",
            (sub.subscription_id, sub.client_id, sub.plan_type, sub.expiry_date),
        )
    return {"subscription_id": sub.subscription_id, "plan_type": sub.plan_type, "expiry_date": sub.expiry_date}


@router.get("/client/{client_id}")
def get_client_subscription(client_id: str):
    """Return the client's current subscription, or 404 if they have none."""
    with get_db() as db:
        row = db.execute(
            "SELECT subscriptionID, planType, expiryDate FROM Subscriptions WHERE clientID = ?",
            (client_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No subscription found")
    return {"subscription_id": row["subscriptionID"], "plan_type": row["planType"], "expiry_date": row["expiryDate"]}


@router.post("/payments")
def process_payment(req: ProcessPaymentRequest):
    """
    Record a payment for an existing subscription.
    simulate_success=True → PaymentStatus.SUCCESS
    simulate_success=False → PaymentStatus.FAILED (to test declined card handling)
    """
    with get_db() as db:
        if not db.execute("SELECT 1 FROM Subscriptions WHERE subscriptionID = ?", (req.subscription_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Subscription not found")

        payment = Payment(
            subscription_id=req.subscription_id,
            amount=req.amount,
            payment_method=req.payment_method,
            payment_status=PaymentStatus.SUCCESS if req.simulate_success else PaymentStatus.FAILED,
        )
        db.execute(
            "INSERT INTO Payment (paymentID, subscriptionID, amount, paymentDate, paymentMethod, paymentStatus) VALUES (?, ?, ?, ?, ?, ?)",
            (payment.payment_id, payment.subscription_id, payment.amount, payment.payment_date, payment.payment_method, payment.payment_status),
        )
    return {"payment_id": payment.payment_id, "status": payment.payment_status, "amount": payment.amount}
