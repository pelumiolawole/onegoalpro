-- Migration 014: user reports of AI-generated content
-- Date: 2026-10-20
--
-- Google Play's AI-generated content policy requires users to be able to report or flag
-- offensive AI output from inside the app. Separate from coach_safety_flags and
-- ai_safety_flags, which record content the system itself detected.
-- ON DELETE CASCADE so account deletion (hard delete of users) also removes a user's reports.

CREATE TABLE IF NOT EXISTS ai_content_reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source text NOT NULL CHECK (source IN ('coach', 'interview', 'task')),
    reference_id text,
    content_excerpt text NOT NULL CHECK (char_length(content_excerpt) <= 1000),
    reason text NOT NULL CHECK (reason IN ('offensive', 'inaccurate', 'inappropriate_advice', 'other')),
    details text CHECK (details IS NULL OR char_length(details) <= 1000),
    reviewed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_content_reports_user_created ON ai_content_reports (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_ai_content_reports_unreviewed ON ai_content_reports (created_at) WHERE NOT reviewed;

ALTER TABLE ai_content_reports ENABLE ROW LEVEL SECURITY;
