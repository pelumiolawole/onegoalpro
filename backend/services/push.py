"""
services/push.py
Sends web push notifications via pywebpush.
"""

import json
import structlog
from pywebpush import webpush, WebPushException
from core.config import settings

logger = structlog.get_logger()

PUSH_EXPIRED = "expired"  # Subscription returned 410 — caller should delete it


def send_push_notification(
    endpoint: str,
    p256dh: str,
    auth: str,
    title: str,
    body: str,
    url: str = "/dashboard",
) -> bool | str:
    """
    Send a single web push notification.
    Returns True on success, False on transient failure, PUSH_EXPIRED on 410.
    """
    try:
        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {
                    "p256dh": p256dh,
                    "auth": auth,
                },
            },
            data=json.dumps({
                "title": title,
                "body": body,
                "url": url,
            }),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={
                "sub": settings.vapid_email,
            },
        )
        return True
    except WebPushException as e:
        # BUG FIX (July 2026): `e.response` is a requests.Response object, and
        # requests overrides truthiness on Response so that `bool(response)`
        # is False for ANY error status code (400+), by design (so error pages
        # aren't mistaken for successful content). That means the old check
        # `if e.response and e.response.status_code == 410` short-circuited to
        # False on every error response, 410 included — the status code was
        # never actually inspected. This branch has never fired since it was
        # written; every 410 fell through to the generic error log below,
        # which is why expired subscriptions were never cleaned up and instead
        # generated a fresh Sentry error on every retry, indefinitely.
        # Fix: check `is not None` instead of relying on truthiness.
        status_code = e.response.status_code if e.response is not None else None
        if status_code in (410, 404):
            # Both codes mean "this subscription no longer exists" per the
            # Web Push protocol (RFC 8030) — 410 Gone is the common case,
            # 404 Not Found is a documented alternative some push services use.
            logger.warning(
                "push_subscription_expired",
                endpoint=endpoint[:50],
                status_code=status_code,
            )
            return PUSH_EXPIRED
        logger.error(
            "push_send_failed",
            error=str(e),
            endpoint=endpoint[:50],
            status_code=status_code,
        )
        return False
    except Exception as e:
        logger.error("push_send_error", error=str(e))
        return False