-- Migration 009: Task backlog tracking and coach interventions

-- Add 'missed' status to daily_tasks if not exists (check your enum first)
-- Note: If TaskStatus enum already has 'missed', skip this
-- ALTER TYPE taskstatus ADD VALUE 'missed';

-- Create coach_interventions table for backlog and other interventions
CREATE TABLE IF NOT EXISTS coach_interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    intervention_type VARCHAR(50) NOT NULL, -- 'backlog_crisis', 'momentum_decline', etc.
    message TEXT NOT NULL,
    urgency VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high'
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_urgency CHECK (urgency IN ('low', 'medium', 'high'))
);

CREATE INDEX idx_coach_interventions_user_id ON coach_interventions(user_id);
CREATE INDEX idx_coach_interventions_created_at ON coach_interventions(created_at);
CREATE INDEX idx_coach_interventions_type ON coach_interventions(intervention_type);

-- Add index for faster missed task queries
CREATE INDEX idx_daily_tasks_missed ON daily_tasks(user_id, scheduled_date, status) 
WHERE status = 'pending' AND scheduled_date < CURRENT_DATE;