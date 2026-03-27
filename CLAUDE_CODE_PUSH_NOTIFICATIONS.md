# Task: Implement Web Push Notifications
# For: Claude Code
# Project: OneGoal Pro
# Date: March 27, 2026
# Priority: HIGH

---

## Context

OneGoal Pro sends daily task emails (working). We now need web push notifications —
OS-level alerts that appear on the user's phone/desktop even when the app is closed.

The Supabase database already has the required tables:
- `push_subscriptions` — stores user push tokens (endpoint, p256dh, auth, user_agent)
- `notification_queue` — stores scheduled notifications (channel, scheduled_at, sent_at)

Tech stack:
- Frontend: Next.js 15, Vercel
- Backend: FastAPI/Python, Railway
- Push library: `web-push` (npm, frontend-only for VAPID generation) + `pywebpush` (Python, backend sending)

---

## Step 1 — Generate VAPID Keys

Run this once locally in Git Bash:

```bash
cd frontend
npx web-push generate-vapid-keys
```

This outputs a public key and private key. Add both to Railway environment variables:
- `VAPID_PUBLIC_KEY` = the public key
- `VAPID_PRIVATE_KEY` = the private key
- `VAPID_EMAIL` = `mailto:hello@onegoalpro.app`

Also add `NEXT_PUBLIC_VAPID_PUBLIC_KEY` to Vercel environment variables (same value as VAPID_PUBLIC_KEY — must be prefixed NEXT_PUBLIC_ to be available in the browser).

---

## Step 2 — Install Dependencies

Backend:
```bash
pip install pywebpush
```
Add `pywebpush` to `backend/requirements.txt`.

Frontend — no new package needed. The browser Push API is built-in.

---

## Step 3 — Create the Service Worker

Create `frontend/public/sw.js`:

```javascript
// OneGoal Pro — Service Worker
// Handles incoming push notifications and displays them

self.addEventListener('push', function(event) {
  if (!event.data) return;

  let data;
  try {
    data = event.data.json();
  } catch {
    data = { title: 'OneGoal Pro', body: event.data.text() };
  }

  const title = data.title || 'OneGoal Pro';
  const options = {
    body: data.body || 'Your identity task for today is ready.',
    icon: '/icon-192.png',
    badge: '/icon-72.png',
    tag: 'onegoal-daily-task',
    renotify: true,
    data: {
      url: data.url || '/dashboard',
    },
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = event.notification.data?.url || '/dashboard';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
      for (const client of clientList) {
        if (client.url.includes('onegoalpro.app') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('https://onegoalpro.app' + url);
      }
    })
  );
});
```

---

## Step 4 — Backend: Store Push Subscription Endpoint

Create `backend/api/routers/push.py`:

```python
"""
api/routers/push.py
Stores and manages web push subscriptions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_active_user
from core.database import get_db
from db.models.user import User

router = APIRouter(prefix="/api/push", tags=["push"])


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str = ""


@router.post("/subscribe")
async def subscribe(
    sub: PushSubscriptionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Store or update a push subscription for the current user."""
    await db.execute(
        text("""
            INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, user_agent)
            VALUES (CAST(:user_id AS uuid), :endpoint, :p256dh, :auth, :user_agent)
            ON CONFLICT (user_id) DO UPDATE
            SET endpoint = EXCLUDED.endpoint,
                p256dh = EXCLUDED.p256dh,
                auth = EXCLUDED.auth,
                user_agent = EXCLUDED.user_agent,
                updated_at = NOW()
        """),
        {
            "user_id": str(current_user.id),
            "endpoint": sub.endpoint,
            "p256dh": sub.p256dh,
            "auth": sub.auth,
            "user_agent": sub.user_agent,
        },
    )
    await db.commit()
    return {"status": "subscribed"}


@router.delete("/unsubscribe")
async def unsubscribe(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove push subscription for the current user."""
    await db.execute(
        text("DELETE FROM push_subscriptions WHERE user_id = CAST(:user_id AS uuid)"),
        {"user_id": str(current_user.id)},
    )
    await db.commit()
    return {"status": "unsubscribed"}
```

Register this router in `backend/main.py` — find where other routers are included and add:
```python
from api.routers.push import router as push_router
app.include_router(push_router)
```

---

## Step 5 — Backend: Push Sending Service

Create `backend/services/push.py`:

```python
"""
services/push.py
Sends web push notifications via pywebpush.
"""

import json
import structlog
from pywebpush import webpush, WebPushException
from core.config import settings

logger = structlog.get_logger()


def send_push_notification(
    endpoint: str,
    p256dh: str,
    auth: str,
    title: str,
    body: str,
    url: str = "/dashboard",
) -> bool:
    """
    Send a single web push notification.
    Returns True on success, False on failure.
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
        # 410 Gone means the subscription is no longer valid — should be deleted
        if e.response and e.response.status_code == 410:
            logger.warning("push_subscription_expired", endpoint=endpoint[:50])
            return False
        logger.error("push_send_failed", error=str(e), endpoint=endpoint[:50])
        return False
    except Exception as e:
        logger.error("push_send_error", error=str(e))
        return False
```

---

## Step 6 — Add VAPID Settings to config.py

In `backend/core/config.py`, add these fields to the Settings class (near the Email section):

```python
# ─── Web Push (VAPID) ───────────────────────────────────────────────
vapid_public_key: str = Field(default="", description="VAPID public key for web push")
vapid_private_key: str = Field(default="", description="VAPID private key for web push")
vapid_email: str = Field(default="mailto:hello@onegoalpro.app", description="VAPID contact email")
```

---

## Step 7 — Wire Push into Scheduler

In `backend/services/scheduler.py`, add a new job `run_daily_push_notifications`.

This job should:
1. Run daily at 8am UTC (alongside the email job)
2. Query `push_subscriptions` joined with `daily_tasks` and `users`
3. For each user with a subscription and a pending task today, call `send_push_notification`
4. Log `push_sent` or `push_failed` per user
5. If a subscription returns 410 Gone, delete it from `push_subscriptions`

SQL to fetch targets:
```sql
SELECT
    ps.user_id,
    ps.endpoint,
    ps.p256dh,
    ps.auth,
    dt.title AS task_title
FROM push_subscriptions ps
JOIN daily_tasks dt ON dt.user_id = ps.user_id
    AND dt.scheduled_date = CURRENT_DATE
    AND dt.status = 'pending'
JOIN users u ON u.id = ps.user_id
WHERE u.is_active = TRUE
```

Register the job in the scheduler startup with:
```python
scheduler.add_job(
    run_daily_push_notifications,
    CronTrigger(hour=8, minute=0),
    name="Send daily push notifications",
    replace_existing=True,
)
```

---

## Step 8 — Frontend: Register Service Worker + Request Permission

In `frontend/src/app/(app)/layout.tsx`, add a `useEffect` that:

1. Registers the service worker (`/sw.js`)
2. Requests notification permission from the user (only once, only if not already granted)
3. If permission granted, creates a push subscription using the VAPID public key
4. POSTs the subscription to `/api/push/subscribe`

```typescript
useEffect(() => {
  if (!user || typeof window === 'undefined') return;
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;

  async function setupPush() {
    try {
      // Register service worker
      const registration = await navigator.serviceWorker.register('/sw.js');

      // Check existing permission
      if (Notification.permission === 'denied') return;

      // Request permission if not yet granted
      if (Notification.permission !== 'granted') {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') return;
      }

      // Check for existing subscription
      const existing = await registration.pushManager.getSubscription();
      if (existing) return; // Already subscribed

      // Subscribe
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY,
      });

      const sub = subscription.toJSON();

      // Store on backend
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/push/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          endpoint: sub.endpoint,
          p256dh: sub.keys?.p256dh,
          auth: sub.keys?.auth,
          user_agent: navigator.userAgent,
        }),
      });
    } catch (e) {
      // Silently fail — push is non-critical
      console.warn('Push setup failed:', e);
    }
  }

  setupPush();
}, [user?.id]);
```

Place this useEffect AFTER the existing auth useEffects, still inside the AppLayout component.

---

## Step 9 — Verify push_subscriptions table schema

Before testing, run this in Supabase SQL editor to confirm the table has the right columns:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'push_subscriptions'
ORDER BY ordinal_position;
```

Expected columns: id, user_id, endpoint, p256dh, auth, user_agent, created_at, updated_at.

If `user_agent` or `updated_at` are missing, add them:
```sql
ALTER TABLE push_subscriptions
ADD COLUMN IF NOT EXISTS user_agent TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
```

Also add a unique constraint on user_id if not present:
```sql
ALTER TABLE push_subscriptions
ADD CONSTRAINT push_subscriptions_user_id_unique UNIQUE (user_id);
```

---

## Step 10 — Test

1. Deploy frontend and backend
2. Open onegoalpro.app on mobile — browser should prompt for notification permission
3. Accept the permission
4. Check Railway logs for the push subscription being stored
5. Check Supabase: `SELECT * FROM push_subscriptions` — your entry should appear
6. Manually trigger a test push from Railway shell:
```python
from services.push import send_push_notification
# Use values from push_subscriptions table
send_push_notification(endpoint, p256dh, auth, "Test", "Your task is ready", "/dashboard")
```
7. Notification should appear on your phone

---

## Definition of Done

- [ ] VAPID keys generated and added to Railway + Vercel
- [ ] `backend/api/routers/push.py` created and registered in main.py
- [ ] `backend/services/push.py` created
- [ ] VAPID fields added to `backend/core/config.py`
- [ ] Scheduler job added and registered
- [ ] `frontend/public/sw.js` created
- [ ] Push setup useEffect added to `frontend/src/app/(app)/layout.tsx`
- [ ] push_subscriptions table schema verified
- [ ] Test notification received on mobile
- [ ] Railway logs show `push_sent` for at least one user
- [ ] job_count in scheduler startup shows +1 (now 10 jobs)

---

## Notes

- Push permission prompt appears automatically on first app load after login — no UI button needed
- Safari on iOS requires the user to "Add to Home Screen" before push works (PWA requirement)
- If a subscription returns HTTP 410, delete it from push_subscriptions — it means the user revoked permission
- The service worker file MUST be at `/public/sw.js` (root of public folder) to have the correct scope
- Do not use any push notification library on the frontend — the browser Push API is sufficient
