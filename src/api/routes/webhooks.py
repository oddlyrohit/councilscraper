"""Webhook endpoints."""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, Field


router = APIRouter()


class WebhookCreate(BaseModel):
    """Request to create a webhook subscription."""
    url: HttpUrl = Field(..., description="Webhook URL to receive notifications")
    councils: Optional[list[str]] = Field(None, description="Filter by council codes")
    categories: Optional[list[str]] = Field(None, description="Filter by categories")
    statuses: Optional[list[str]] = Field(None, description="Filter by statuses")
    secret: Optional[str] = Field(None, description="Secret for signature verification")


class WebhookResponse(BaseModel):
    """Webhook subscription response."""
    id: str
    url: str
    councils: Optional[list[str]] = None
    categories: Optional[list[str]] = None
    statuses: Optional[list[str]] = None
    active: bool = True
    created_at: str


# In-memory storage (replace with database in production)
_webhooks: dict[str, dict] = {}


@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(webhook: WebhookCreate):
    """
    Register a webhook for new DA notifications.

    Webhooks will receive POST requests with the following payload:
    ```json
    {
        "event": "application.created" | "application.updated",
        "application": { ... application data ... },
        "timestamp": "2025-01-01T00:00:00Z"
    }
    ```

    Optionally filter by councils, categories, or statuses.
    """
    from datetime import datetime

    webhook_id = str(uuid4())

    webhook_data = {
        "id": webhook_id,
        "url": str(webhook.url),
        "councils": webhook.councils,
        "categories": webhook.categories,
        "statuses": webhook.statuses,
        "secret": webhook.secret,
        "active": True,
        "created_at": datetime.utcnow().isoformat(),
    }

    _webhooks[webhook_id] = webhook_data

    return WebhookResponse(**webhook_data)


@router.get("/webhooks")
async def list_webhooks():
    """
    List all registered webhooks.
    """
    return {
        "data": [
            WebhookResponse(**{k: v for k, v in w.items() if k != "secret"})
            for w in _webhooks.values()
        ],
        "meta": {"total": len(_webhooks)},
    }


@router.get("/webhooks/{webhook_id}")
async def get_webhook(webhook_id: str):
    """
    Get webhook details.
    """
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    webhook = _webhooks[webhook_id]
    return WebhookResponse(**{k: v for k, v in webhook.items() if k != "secret"})


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """
    Delete a webhook subscription.
    """
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    del _webhooks[webhook_id]
    return {"message": "Webhook deleted", "id": webhook_id}


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str):
    """
    Send a test notification to a webhook.
    """
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    webhook = _webhooks[webhook_id]

    # In production, this would actually send an HTTP request
    return {
        "message": "Test webhook sent",
        "webhook_id": webhook_id,
        "url": webhook["url"],
    }
