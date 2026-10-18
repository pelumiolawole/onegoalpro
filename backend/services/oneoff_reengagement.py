"""
services/oneoff_reengagement.py

TEMPORARY. One-off re-engagement email to dormant task completers, October 2026.
Remove this file and its scheduler entry after Segment B has been sent.

Runs every 15 minutes from the scheduler. Each run:
  1. Does nothing if ONEOFF_REENGAGEMENT_PAUSED is "true" (read at run time).
  2. Sends each segment's version once to the test address, tagged [TEST].
  3. Sends a segment once its London send time has passed AND its test version
     was accepted by Resend at least MIN_GAP_AFTER_TEST earlier.
Every accepted email is recorded in oneoff_email_sends; anyone already recorded for
a campaign is skipped, so restarts and repeat runs never send a duplicate.
Recipients are selected by query at run time; no recipient address is in this file.
"""

import asyncio
import html
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import resend
import sentry_sdk
import structlog
from sqlalchemy import text

from core.config import settings

logger = structlog.get_logger()

KILL_SWITCH_ENV = "ONEOFF_REENGAGEMENT_PAUSED"
TEST_CAMPAIGN = "reengagement_2026_10_test"
CAMPAIGNS = {"A": "reengagement_2026_10_A", "B": "reengagement_2026_10_B"}

LONDON = ZoneInfo("Europe/London")
SEND_AT = {
    "A": datetime(2026, 10, 18, 18, 0, tzinfo=LONDON),
    "B": datetime(2026, 10, 19, 18, 0, tzinfo=LONDON),
}
MIN_GAP_AFTER_TEST = timedelta(minutes=30)

FROM_HEADER = "Pelumi <pelumi@onegoalpro.app>"
REPLY_TO = "pelumi@onegoalpro.app"
TEST_RECIPIENT = "pelumi@onegoalpro.app"
TEST_GREETING = "Pelumi"
TEST_N = 6

THROTTLE_SECONDS = 0.6
MAX_ATTEMPTS_PER_PROCESS = 3

# Pelumi's own accounts and two personal contacts he will message himself.
EXCLUDED_EMAILS = frozenset({
    "olawolepelumisunday@gmail.com",
    "pelumisolawole@gmail.com",
    "iicnetworksng@gmail.com",
    "pelumi.olawole@icloud.com",
    "tomolawblog@gmail.com",
    "olawoleromeo@gmail.com",
    "busayo@simpletest.ai",
})

SUBJECTS = {
    "A": "A question from Pelumi at OneGoal Pro",
    "B": "What made you stop?",
}

BODIES = {
    "A": """Hi {first_name},

It's Pelumi, the founder of OneGoal Pro. You completed {n} tasks back in the spring, more than almost anyone else who tried it, and then you stopped.

I'm not writing to talk you into coming back. I want to understand what happened. Was it the tasks themselves, the timing, life getting busy, or something about the app? A one-line reply is plenty, and a blunt answer helps me more than a polite one.

Separately, I've just built an Android version and I'm looking for a small group to try it before it goes public. If you'd like in, reply with the Google account email you use on your phone and I'll add you.

Thanks,
Pelumi

If you'd rather not hear from me again, reply "stop" and I won't email you.""",
    "B": """Hi {first_name},

It's Pelumi from OneGoal Pro. You signed up in the spring and tried a task or two, and then it didn't stick.

I'd like to know why. Hit reply and tell me in a sentence, even if the answer is "it wasn't for me". That kind of honesty is what helps me fix it.

I'm also opening an early Android version to a small group. If you'd like to try it, reply with the Google account email on your Android phone and I'll add you.

Pelumi
Founder, OneGoal Pro

Reply "stop" and I won't email you again.""",
}

_attempts: dict[tuple[str, str], int] = {}


def is_paused() -> bool:
    return os.getenv(KILL_SWITCH_ENV, "").strip().lower() == "true"


def segment_for(completed: int) -> str | None:
    if completed >= 5:
        return "A"
    if completed >= 1:
        return "B"
    return None


def default_greeting(display_name: str | None) -> str:
    words = (display_name or "").split()
    return words[0].title() if words else "there"


def render(segment: str, first_name: str, n: int) -> tuple[str, str]:
    """Return (plain text, minimal HTML) for a segment. The HTML is the same paragraphs, nothing else."""
    body = BODIES[segment].replace("{first_name}", first_name).replace("{n}", str(n))
    paragraphs = body.split("\n\n")
    html_body = "".join(
        f"<p>{'<br>'.join(html.escape(line) for line in p.split(chr(10)))}</p>" for p in paragraphs
    )
    return body, html_body


def select_recipients(rows, overrides: dict[str, str]) -> dict[str, list[dict]]:
    """rows: (user_id, email, display_name, completed_count). Returns {"A": [...], "B": [...]}."""
    out: dict[str, list[dict]] = {"A": [], "B": []}
    for user_id, email, display_name, completed in rows:
        if not email or email.strip().lower() in EXCLUDED_EMAILS:
            continue
        segment = segment_for(int(completed))
        if segment is None:
            continue
        key = email.strip().lower()
        out[segment].append({
            "user_id": str(user_id),
            "email": email.strip(),
            "greeting": overrides.get(key) or default_greeting(display_name),
            "n": int(completed),
        })
    return out


def _send_sync(to: str, subject: str, text_body: str, html_body: str) -> str | None:
    response = resend.Emails.send({
        "from": FROM_HEADER,
        "to": [to],
        "reply_to": REPLY_TO,
        "subject": subject,
        "text": text_body,
        "html": html_body,
    })
    if isinstance(response, dict):
        return response.get("id")
    return getattr(response, "id", None)


async def _send_and_record(db, campaign: str, segment: str, to: str, subject: str,
                           first_name: str, n: int, user_id: str | None) -> bool:
    key = (campaign, to.lower())
    if _attempts.get(key, 0) >= MAX_ATTEMPTS_PER_PROCESS:
        return False
    _attempts[key] = _attempts.get(key, 0) + 1

    text_body, html_body = render(segment, first_name, n)
    try:
        resend_id = await asyncio.to_thread(_send_sync, to, subject, text_body, html_body)
    except Exception as e:
        logger.error("oneoff_email_failed", campaign=campaign, segment=segment, user_id=user_id, error=str(e))
        sentry_sdk.capture_exception(e, tags={"oneoff_campaign": campaign, "user_id": user_id or "test"})
        return False

    await db.execute(
        text("""
            INSERT INTO oneoff_email_sends (campaign, recipient_email, segment, resend_email_id)
            VALUES (:campaign, :email, :segment, :resend_id)
            ON CONFLICT (campaign, recipient_email, segment) DO NOTHING
        """),
        {"campaign": campaign, "email": to.lower(), "segment": segment, "resend_id": resend_id},
    )
    await db.commit()
    logger.info("oneoff_email_sent", campaign=campaign, segment=segment, user_id=user_id, resend_id=resend_id)
    return True


async def _sent_set(db, campaign: str, segment: str) -> set[str]:
    rows = await db.execute(
        text("SELECT lower(recipient_email) FROM oneoff_email_sends WHERE campaign = :c AND segment = :s"),
        {"c": campaign, "s": segment},
    )
    return {r[0] for r in rows.fetchall()}


async def _test_sent_at(db, segment: str) -> datetime | None:
    row = (await db.execute(
        text("""
            SELECT sent_at FROM oneoff_email_sends
            WHERE campaign = :c AND segment = :s AND lower(recipient_email) = :e
        """),
        {"c": TEST_CAMPAIGN, "s": segment, "e": TEST_RECIPIENT},
    )).first()
    return row[0] if row else None


async def run_once(db, now: datetime) -> dict:
    """One pass. Returns counts per action, for logging and tests."""
    result = {"paused": False, "test_sent": 0, "A": 0, "B": 0}
    if is_paused():
        result["paused"] = True
        logger.info("oneoff_reengagement_paused")
        return result

    for segment in ("A", "B"):
        if await _test_sent_at(db, segment) is None:
            if await _send_and_record(db, TEST_CAMPAIGN, segment, TEST_RECIPIENT,
                                      f"[TEST] {SUBJECTS[segment]}", TEST_GREETING, TEST_N, None):
                result["test_sent"] += 1
            await asyncio.sleep(THROTTLE_SECONDS)

    due = []
    for segment in ("A", "B"):
        test_at = await _test_sent_at(db, segment)
        if now >= SEND_AT[segment] and test_at is not None and now - test_at >= MIN_GAP_AFTER_TEST:
            due.append(segment)
    if not due:
        return result

    overrides = {
        r[0].strip().lower(): r[1]
        for r in (await db.execute(text("SELECT email, greeting FROM oneoff_email_greetings"))).fetchall()
    }
    rows = (await db.execute(text("""
        SELECT u.id, u.email, u.display_name, COUNT(t.id) AS completed
        FROM users u
        JOIN daily_tasks t ON t.user_id = u.id AND t.status = 'completed'
        WHERE u.is_active = TRUE
          AND u.deletion_scheduled_at IS NULL
          AND u.email_verified_at IS NOT NULL
        GROUP BY u.id, u.email, u.display_name
    """))).fetchall()
    segments = select_recipients(rows, overrides)

    for segment in due:
        campaign = CAMPAIGNS[segment]
        already = await _sent_set(db, campaign, segment)
        for r in segments[segment]:
            if r["email"].lower() in already:
                continue
            if is_paused():
                logger.info("oneoff_reengagement_paused_mid_batch", campaign=campaign)
                return result
            if await _send_and_record(db, campaign, segment, r["email"], SUBJECTS[segment],
                                      r["greeting"], r["n"], r["user_id"]):
                result[segment] += 1
            await asyncio.sleep(THROTTLE_SECONDS)
    return result


async def run_oneoff_reengagement() -> None:
    """Scheduler entry point (every 15 minutes)."""
    from core.cache import acquire_lock, release_lock
    from core.database import get_db_context

    if not settings.resend_api_key:
        logger.error("oneoff_reengagement_no_resend_key")
        return
    resend.api_key = settings.resend_api_key

    if not await acquire_lock("oneoff_reengagement", ttl_seconds=900):
        return
    try:
        async with get_db_context() as db:
            result = await run_once(db, datetime.now(timezone.utc))
        logger.info("oneoff_reengagement_run", **result)
    except Exception as e:
        logger.error("oneoff_reengagement_error", error=str(e), exc_info=True)
        sentry_sdk.capture_exception(e)
    finally:
        await release_lock("oneoff_reengagement")
