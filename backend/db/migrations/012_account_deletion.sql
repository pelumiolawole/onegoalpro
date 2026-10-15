-- Migration 012: account deletion ledger
-- Date: 2026-10-15
--
-- Account deletion now hard-deletes the users row, and ON DELETE CASCADE removes
-- the user's data from every table that references users(id).
-- deletion_requests is the record that a deletion was requested and completed, so
-- it must outlive the users row. It keeps the bare user UUID, without a foreign key.
-- Pending state stays on users.deletion_scheduled_at (existing column).

ALTER TABLE deletion_requests DROP CONSTRAINT IF EXISTS deletion_requests_user_id_fkey;

CREATE INDEX IF NOT EXISTS idx_deletion_requests_user_id ON deletion_requests (user_id);

-- At most one open request per user, so a double-submit cannot create two.
CREATE UNIQUE INDEX IF NOT EXISTS uq_deletion_requests_pending_user
    ON deletion_requests (user_id) WHERE status = 'pending';
