-- Migration 010: Enhanced Coach Memory System

-- 1. Session tracking for intentional openings/closings
CREATE TABLE coach_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    opening_context TEXT, -- What was top of mind when session started
    closing_insight TEXT, -- Key takeaway when session ended
    session_goal TEXT, -- What they wanted to work on this session
    emotional_arc TEXT, -- How their state shifted (JSON array of states)
    coach_mode_used TEXT, -- Which mode dominated
    next_session_hook TEXT, -- What to follow up on
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_coach_sessions_user_id ON coach_sessions(user_id);
CREATE INDEX idx_coach_sessions_start ON coach_sessions(session_start);

-- 2. Key moments database (breakthroughs, resistance, commitments)
CREATE TABLE coach_moments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES coach_sessions(id),
    moment_type TEXT NOT NULL CHECK (moment_type IN ('breakthrough', 'resistance', 'commitment', 'vulnerability', 'pattern_repeat', 'insight')),
    moment_content TEXT NOT NULL, -- What they actually said
    coach_observation TEXT, -- What the coach noticed
    user_language TEXT, -- Exact words/phrases they used
    emotional_tone TEXT,
    trait_referenced TEXT, -- Which identity trait this connects to
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_coach_moments_user_id ON coach_moments(user_id);
CREATE INDEX idx_coach_moments_type ON coach_moments(moment_type);
CREATE INDEX idx_coach_moments_trait ON coach_moments(trait_referenced);

-- 3. Conversation continuity (for between-session touchpoints)
CREATE TABLE coach_touchpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL, -- What they shared
    coach_acknowledgment TEXT, -- Brief response
    session_id UUID REFERENCES coach_sessions(id), -- Linked to next full session
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_coach_touchpoints_user_id ON coach_touchpoints(user_id);
CREATE INDEX idx_coach_touchpoints_unprocessed ON coach_touchpoints(user_id, is_processed) WHERE is_processed = FALSE;

-- 4. Pattern recognition tracking
CREATE TABLE coach_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pattern_name TEXT NOT NULL,
    pattern_type TEXT NOT NULL CHECK (pattern_type IN ('resistance', 'strength', 'growth_edge', 'avoidance', 'breakthrough_indicator')),
    description TEXT NOT NULL,
    evidence_count INTEGER DEFAULT 1,
    first_observed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_observed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_coach_patterns_user_id ON coach_patterns(user_id);
CREATE INDEX idx_coach_patterns_active ON coach_patterns(user_id, is_active) WHERE is_active = TRUE;

-- 5. Crisis/safety tracking
CREATE TABLE coach_safety_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES coach_sessions(id),
    flag_type TEXT NOT NULL CHECK (flag_type IN ('distress', 'self_harm_ideation', 'crisis_language', 'withdrawal_concern')),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'immediate')),
    trigger_phrase TEXT, -- What they said that triggered the flag
    coach_response TEXT, -- How the coach responded
    admin_notified BOOLEAN DEFAULT FALSE,
    admin_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_coach_safety_user_id ON coach_safety_flags(user_id);
CREATE INDEX idx_coach_safety_unresolved ON coach_safety_flags(admin_notified, admin_resolved) WHERE admin_notified = TRUE AND admin_resolved = FALSE;