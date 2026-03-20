-- Migration 010: Comprehensive Scoring System Fix
-- Date: 2026-03-20
-- Fixes ALL discovered issues in update_user_scores function
-- - momentum_state enum cast error
-- - quality_score column reference (changed to depth_score)
-- - progress_metrics missing columns
-- - task completion source (daily_tasks, not progress_metrics)

-- 1. Ensure momentum_state enum exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'momentum_state') THEN
        CREATE TYPE momentum_state AS ENUM ('rising', 'holding', 'declining', 'critical');
    END IF;
END $$;

-- 2. Ensure all progress_metrics columns exist
ALTER TABLE progress_metrics 
ADD COLUMN IF NOT EXISTS task_id UUID REFERENCES daily_tasks(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS avg_depth_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS transformation_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS momentum_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS alignment_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS consistency_score INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_progress_metrics_task_id ON progress_metrics(task_id);

-- 3. Add depth_score to reflections if quality_score doesn't exist
DO $$
DECLARE
    v_has_depth_score BOOLEAN;
    v_has_quality_score BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'reflections' AND column_name = 'depth_score') INTO v_has_depth_score;
    SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'reflections' AND column_name = 'quality_score') INTO v_has_quality_score;
    
    IF NOT v_has_depth_score AND NOT v_has_quality_score THEN
        ALTER TABLE reflections ADD COLUMN depth_score INTEGER;
    END IF;
END $$;

-- 4. DROP and recreate the function with ALL fixes
DROP FUNCTION IF EXISTS update_user_scores(UUID);

CREATE OR REPLACE FUNCTION update_user_scores(p_user_id UUID)
RETURNS VOID AS $$
DECLARE
    v_consistency INTEGER;
    v_depth INTEGER;
    v_momentum INTEGER;
    v_alignment INTEGER;
    v_transformation INTEGER;
    v_state momentum_state;  -- Use the enum type directly
BEGIN
    -- Calculate consistency from daily_tasks (NOT progress_metrics)
    SELECT COALESCE(
        ROUND(
            (COUNT(*) FILTER (WHERE completed_at IS NOT NULL))::NUMERIC / 
            NULLIF(COUNT(*), 0) * 100
        ), 0)::INTEGER
    INTO v_consistency
    FROM daily_tasks
    WHERE user_id = p_user_id
    AND created_at >= CURRENT_DATE - INTERVAL '14 days';

    -- Calculate depth from reflections (use depth_score, not quality_score)
    SELECT COALESCE(ROUND(AVG(depth_score)), 0)::INTEGER
    INTO v_depth
    FROM reflections
    WHERE user_id = p_user_id
    AND created_at >= CURRENT_DATE - INTERVAL '14 days'
    AND depth_score IS NOT NULL;

    -- Calculate momentum (last 7 vs prior 7 days)
    WITH recent AS (
        SELECT COUNT(*) FILTER (WHERE completed_at IS NOT NULL) as completed
        FROM daily_tasks
        WHERE user_id = p_user_id
        AND created_at >= CURRENT_DATE - INTERVAL '7 days'
    ),
    prior AS (
        SELECT COUNT(*) FILTER (WHERE completed_at IS NOT NULL) as completed
        FROM daily_tasks
        WHERE user_id = p_user_id
        AND created_at >= CURRENT_DATE - INTERVAL '14 days'
        AND created_at < CURRENT_DATE - INTERVAL '7 days'
    )
    SELECT COALESCE(
        CASE 
            WHEN p.completed = 0 THEN 50
            ELSE ROUND((r.completed::NUMERIC / p.completed * 50) + 50)
        END, 50)::INTEGER
    INTO v_momentum
    FROM recent r, prior p;

    -- Calculate alignment from identity_traits
    SELECT COALESCE(ROUND(AVG(current_score) * 10), 0)::INTEGER
    INTO v_alignment
    FROM identity_traits
    WHERE user_id = p_user_id;

    -- Calculate transformation score
    v_transformation := ROUND(
        v_consistency * 0.35 + 
        v_depth * 0.25 + 
        v_momentum * 0.25 + 
        v_alignment * 0.15
    )::INTEGER;

    -- Determine momentum state using ENUM type (not text!)
    v_state := CASE
        WHEN v_momentum >= 65 THEN 'rising'::momentum_state
        WHEN v_momentum >= 40 THEN 'holding'::momentum_state
        WHEN v_momentum >= 20 THEN 'declining'::momentum_state
        ELSE 'critical'::momentum_state
    END;

    -- Update progress_metrics for today
    INSERT INTO progress_metrics (
        user_id, metric_date, task_completed, reflection_submitted,
        avg_depth_score, transformation_score, momentum_score, 
        alignment_score, consistency_score, updated_at
    )
    VALUES (
        p_user_id, CURRENT_DATE, FALSE, FALSE,
        v_depth, v_transformation, v_momentum,
        v_alignment, v_consistency, NOW()
    )
    ON CONFLICT (user_id, metric_date) 
    DO UPDATE SET
        avg_depth_score = EXCLUDED.avg_depth_score,
        transformation_score = EXCLUDED.transformation_score,
        momentum_score = EXCLUDED.momentum_score,
        alignment_score = EXCLUDED.alignment_score,
        consistency_score = EXCLUDED.consistency_score,
        updated_at = NOW();

    -- Update identity_profiles with latest scores
    UPDATE identity_profiles
    SET 
        consistency_score = v_consistency,
        depth_score = v_depth,
        momentum_score = v_momentum,
        alignment_score = v_alignment,
        transformation_score = v_transformation,
        momentum_state = v_state,  -- Now properly typed as enum
        updated_at = NOW()
    WHERE user_id = p_user_id;
    
END;
$$ LANGUAGE plpgsql;