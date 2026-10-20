-- Migration 015: daily time budget, asked as a structured question
-- Date: 2026-10-20
--
-- The AI interview captured time availability for 4 of 50 users with a goal,
-- and those 4 were stored as {"morning": 15} / {"evening": 120} while the task
-- generator read "weekday"/"weekend" keys, so even they were never used: every
-- task was sized to a 30-minute default. daily_minutes and preferred_time are
-- now asked on a required onboarding screen and are the single source of truth.

ALTER TABLE identity_profiles
    ADD COLUMN IF NOT EXISTS daily_minutes integer
        CHECK (daily_minutes IS NULL OR daily_minutes IN (10, 20, 30, 45, 60)),
    ADD COLUMN IF NOT EXISTS preferred_time text
        CHECK (preferred_time IS NULL OR preferred_time IN ('morning', 'midday', 'evening', 'varies'));

COMMENT ON COLUMN identity_profiles.daily_minutes IS
    'Minutes per day the user can give their goal (10/20/30/45/60, 60 = 1 hour+). Asked in onboarding and Settings. Task generator treats it as a hard cap; NULL means 20.';
COMMENT ON COLUMN identity_profiles.preferred_time IS
    'When the user usually has that time: morning, midday, evening, varies. Asked in onboarding and Settings.';
COMMENT ON COLUMN identity_profiles.time_availability IS
    'SUPERSEDED 2026-10-20 by daily_minutes. AI-inferred, rarely filled, no longer read or written by the app.';
COMMENT ON COLUMN identity_profiles.peak_performance_time IS
    'SUPERSEDED 2026-10-20 by preferred_time. AI-inferred, no longer written by the app.';
