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
        if e.response and e.response.status_code == 410:
            logger.warning("push_subscription_expired", endpoint=endpoint[:50])
            return PUSH_EXPIRED
        logger.error("push_send_failed", error=str(e), endpoint=endpoint[:50])
        return False
    except Exception as e:
        logger.error("push_send_error", error=str(e))
        return False
