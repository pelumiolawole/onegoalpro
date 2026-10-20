"""
core/names.py

One place for display-name rules, so sign-up, OAuth, settings, AI prompts,
emails and push copy all agree.

Rules (20 Oct 2026): trimmed, 1-50 characters, letters plus spaces, hyphens
and apostrophes. Letters from any script count (Adé, Zoë, Ọlá).

Copy rule: when there is no usable name, write the sentence so it reads
naturally without one. Never fall back to the email address, and never put
"there" mid-sentence ("Good morning there, ...").
"""

import re
import unicodedata
from typing import Optional

MAX_NAME_LENGTH = 50
_SEPARATORS = {" ", "-", "'", "’"}  # space, hyphen, apostrophe, curly apostrophe


def clean_display_name(value: Optional[str]) -> str:
    """
    Validate and normalise a display name. Raises ValueError with a
    user-facing message if it isn't acceptable.
    """
    name = re.sub(r"\s+", " ", unicodedata.normalize("NFC", value or "").strip())
    if not name:
        raise ValueError("Please tell us what to call you.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Please keep your name to {MAX_NAME_LENGTH} characters or fewer.")
    if not all(ch.isalpha() or unicodedata.category(ch).startswith("M") or ch in _SEPARATORS for ch in name):
        raise ValueError("Please use letters only. Spaces, hyphens and apostrophes are fine.")
    if not any(ch.isalpha() for ch in name):
        raise ValueError("Please tell us what to call you.")
    return name


def valid_display_name_or_none(value: Optional[str]) -> Optional[str]:
    """Return the cleaned name, or None if it doesn't pass the rules."""
    try:
        return clean_display_name(value)
    except ValueError:
        return None


def first_name(display_name: Optional[str]) -> Optional[str]:
    """
    The name to address someone by: the first word of their display name.
    Returns None when there is no usable name. Callers must then write copy
    that needs no name, rather than substituting "there" or the email.
    """
    if not display_name:
        return None
    parts = display_name.strip().split()
    if not parts:
        return None
    first = parts[0]
    return first if any(ch.isalpha() for ch in first) else None


def name_from_oauth_metadata(metadata: dict) -> Optional[str]:
    """
    Google (via Supabase) usually sends given_name; older payloads only carry
    full_name / name. Take the given name if present, else the first word of
    the full name. Returns None if nothing usable, so the user is asked.
    """
    metadata = metadata or {}
    given = valid_display_name_or_none(metadata.get("given_name"))
    if given:
        return given
    for key in ("full_name", "name"):
        first = first_name(metadata.get(key))
        cleaned = valid_display_name_or_none(first)
        if cleaned:
            return cleaned
    return None
