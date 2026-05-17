"""
Optional outbound webhooks for enquiries / bookings / reviews.

If you'd like to keep using Notion, Airtable, Slack, or Google Sheets
alongside Django (e.g. so the existing team workflow doesn't change),
configure any of these env vars and the data will be mirrored
fire-and-forget on every new submission.

Env vars (any combination):
    NOTION_API_TOKEN, NOTION_ENQUIRY_DB_ID, NOTION_BOOKING_DB_ID
    AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_ENQUIRY_TABLE, AIRTABLE_BOOKING_TABLE
    SLACK_WEBHOOK_URL              # posts a quick text summary
    SHEETS_WEBHOOK_URL             # your old Google Apps Script URL, if you keep it

All requests have a 4-second timeout; failures are logged but never
break the user-facing submission flow.
"""
from __future__ import annotations

import logging
import os
from threading import Thread

import requests

logger = logging.getLogger(__name__)

TIMEOUT = 4  # seconds


# ─── Helpers ─────────────────────────────────────────────────────────
def _async(target):
    """Fire-and-forget — don't make the user wait for webhooks."""
    Thread(target=target, daemon=True).start()


def _safe(name, fn):
    """Run a webhook, swallow + log any error."""
    try:
        fn()
    except Exception as exc:
        logger.warning("Webhook %s failed: %s", name, exc)


# ─── Slack ───────────────────────────────────────────────────────────
def post_slack(text: str) -> None:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return
    _async(lambda: _safe("slack", lambda: requests.post(
        url, json={"text": text}, timeout=TIMEOUT
    )))


# ─── Notion ──────────────────────────────────────────────────────────
def post_notion(database_id_env: str, properties: dict) -> None:
    """Add a row to a Notion database. `properties` is the Notion API shape."""
    token = os.environ.get("NOTION_API_TOKEN")
    db_id = os.environ.get(database_id_env)
    if not (token and db_id):
        return

    def go():
        _safe("notion", lambda: requests.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json={"parent": {"database_id": db_id}, "properties": properties},
            timeout=TIMEOUT,
        ))
    _async(go)


# ─── Airtable ────────────────────────────────────────────────────────
def post_airtable(table_env: str, fields: dict) -> None:
    key = os.environ.get("AIRTABLE_API_KEY")
    base = os.environ.get("AIRTABLE_BASE_ID")
    table = os.environ.get(table_env)
    if not (key and base and table):
        return

    def go():
        _safe("airtable", lambda: requests.post(
            f"https://api.airtable.com/v0/{base}/{table}",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={"fields": fields},
            timeout=TIMEOUT,
        ))
    _async(go)


# ─── Legacy Google Sheets webhook ────────────────────────────────────
def post_sheets(action: str, data: dict) -> None:
    """If the old google-apps-script.gs Web App is still live, mirror to it."""
    url = os.environ.get("SHEETS_WEBHOOK_URL")
    secret = os.environ.get("SHEETS_SECRET", "")
    if not url:
        return

    def go():
        _safe("sheets", lambda: requests.post(
            url,
            headers={"Content-Type": "text/plain;charset=utf-8"},
            data='{"action":"%s","secret":"%s","data":%s}' % (
                action, secret, _to_json(data)
            ),
            timeout=TIMEOUT,
        ))
    _async(go)


def _to_json(d: dict) -> str:
    import json
    return json.dumps(d, ensure_ascii=False)


# ─── High-level mirrors per submission type ──────────────────────────
def mirror_enquiry(obj) -> None:
    summary = (
        f"📩 *New enquiry* from *{obj.name}*\n"
        f"📞 {obj.phone}  ·  ✉️ {obj.email}\n"
        f"Destination: {obj.destination or '—'}  ·  Group: {obj.group_size or '—'}  ·  "
        f"Month: {obj.month or '—'}  ·  Budget: {obj.budget or '—'}\n"
        f"> {obj.message or '(no message)'}"
    )
    post_slack(summary)
    post_notion("NOTION_ENQUIRY_DB_ID", {
        "Name":        {"title": [{"text": {"content": obj.name}}]},
        "Phone":       {"phone_number": obj.phone},
        "Email":       {"email": obj.email},
        "Destination": {"rich_text": [{"text": {"content": obj.destination or ""}}]},
        "Status":      {"select": {"name": "new"}},
    })
    post_airtable("AIRTABLE_ENQUIRY_TABLE", {
        "Name": obj.name, "Phone": obj.phone, "Email": obj.email,
        "Destination": obj.destination, "Group": obj.group_size,
        "Month": obj.month, "Budget": obj.budget, "Message": obj.message,
    })
    post_sheets("addEnquiry", {
        "id": f"ENQ-{obj.id}", "name": obj.name, "phone": obj.phone,
        "email": obj.email, "destination": obj.destination,
        "groupSize": obj.group_size, "month": obj.month,
        "budget": obj.budget, "message": obj.message,
    })


def mirror_booking(obj) -> None:
    summary = (
        f"📋 *New booking*: *{obj.name}* → *{obj.package}*\n"
        f"📞 {obj.phone}  ·  ✉️ {obj.email}  ·  ₹{obj.price or '?'}  ·  "
        f"{obj.persons or '?'} persons  ·  Date: {obj.preferred_date or '—'}"
    )
    post_slack(summary)
    post_notion("NOTION_BOOKING_DB_ID", {
        "Name":    {"title": [{"text": {"content": obj.name}}]},
        "Package": {"rich_text": [{"text": {"content": obj.package}}]},
        "Phone":   {"phone_number": obj.phone},
        "Email":   {"email": obj.email},
        "Status":  {"select": {"name": "new"}},
    })
    post_airtable("AIRTABLE_BOOKING_TABLE", {
        "Name": obj.name, "Phone": obj.phone, "Email": obj.email,
        "Package": obj.package, "Price": obj.price,
        "Persons": obj.persons, "Date": obj.preferred_date,
    })
    post_sheets("addBooking", {
        "id": f"BK-{obj.id}", "name": obj.name, "phone": obj.phone,
        "email": obj.email, "package": obj.package, "price": obj.price,
        "persons": obj.persons, "date": obj.preferred_date,
    })


def mirror_review(obj) -> None:
    summary = (
        f"⭐ *New review* ({obj.rating}★) from *{obj.name}*\n"
        f"> {obj.body}"
    )
    post_slack(summary)
    post_sheets("addReview", {
        "id": f"RV-{obj.id}", "name": obj.name, "city": obj.city,
        "rating": obj.rating, "package": obj.package, "body": obj.body,
    })
