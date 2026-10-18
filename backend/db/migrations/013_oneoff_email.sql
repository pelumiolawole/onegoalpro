-- Migration 013: one-off email campaign tables
-- Date: 2026-10-18
--
-- oneoff_email_sends is the permanent record of every one-off campaign email that Resend
-- accepted, and the duplicate guard: a row exists only after Resend accepts the email, and the
-- job skips anyone who already has a row for that campaign and segment.
-- segment is part of the unique key so the test campaign can hold one row per segment version
-- for the same test address. Real campaigns have one segment each, so for them this is the same
-- as unique (campaign, recipient_email).
--
-- oneoff_email_greetings holds per-recipient greeting overrides for one campaign. Rows are
-- inserted by SQL, never committed to the repo, and the table is dropped after the campaign.

CREATE TABLE IF NOT EXISTS oneoff_email_sends (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign text NOT NULL,
    recipient_email text NOT NULL,
    segment text NOT NULL,
    resend_email_id text,
    sent_at timestamptz DEFAULT now(),
    UNIQUE (campaign, recipient_email, segment)
);

CREATE TABLE IF NOT EXISTS oneoff_email_greetings (
    email text PRIMARY KEY,
    greeting text NOT NULL
);

ALTER TABLE oneoff_email_sends ENABLE ROW LEVEL SECURITY;
ALTER TABLE oneoff_email_greetings ENABLE ROW LEVEL SECURITY;
