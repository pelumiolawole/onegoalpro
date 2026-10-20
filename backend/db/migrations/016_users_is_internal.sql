-- Migration 016: mark internal accounts in the database
-- Date: 2026-10-20
--
-- Pelumi's own accounts and the Google Play reviewer account. Excluded from
-- re-engagement and nudge emails (services/scheduler.py) and should be
-- excluded from every metric (WHERE NOT is_internal).
-- Which accounts are internal is set with an UPDATE run in the Supabase SQL
-- editor, not here: email addresses are not committed to the repo. The list
-- is in CLAUDE.md (user/revenue block).

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_internal boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN users.is_internal IS
    'Internal account (founder or Play reviewer). Excluded from re-engagement emails and from metrics. Set by hand; see CLAUDE.md.';
