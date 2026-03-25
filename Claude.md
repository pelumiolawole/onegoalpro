# OneGoal Pro — Master Claude Skill File
# Version: 1.0 | Last updated: March 2026
# READ THIS ENTIRE FILE BEFORE DOING ANYTHING ELSE IN THIS SESSION

---

## WHO YOU ARE WORKING WITH

**Name:** Pelumi Olawole
**Role:** Founder, IIC Networks (Influence, Impact, Change) | Author | Coach | Day job: E.ON Next (UK)
**Book:** *Petty Little Things: 50 Habits Quietly Ruining Your Life and How to Fix Them*
**Working environment:** Windows, VS Code, Git Bash
**Skill level:** Rebuilding development skills — needs explicit step-by-step terminal instructions
**Deployment workflow:** Local edits → push to GitHub → auto-deploy (Railway ~10–15 min, Vercel ~2 min)
**Testing:** Primarily on mobile. No browser DevTools available. Railway logs are primary debug tool.
**File delivery preference:** Complete corrected files ready to copy-paste. No partial diffs unless trivial.
**Communication preference:** Plain English explanation of what's wrong BEFORE any code.

---

## WHAT WE ARE BUILDING

**Product:** OneGoal Pro
**Tagline:** One goal. Full commitment. No excuses.
**Core idea:** Identity-based goal transformation. Not what to do — who to become.
**Live URL:** https://onegoalpro.app
**API URL:** https://api.onegoalpro.app
**GitHub:** https://github.com/pelumiolawole/onegoalclaude
**Stage:** MVP — deployed, 7 registered users (4 real: wife, engineer, website guy, friend)

---

## TECH STACK — PRODUCTION

| Layer | Technology | Provider | URL |
|---|---|---|---|
| Frontend | Next.js 15 (React 19) | Vercel | onegoalpro.app |
| Backend | FastAPI (Python) | Railway | api.onegoalpro.app |
| Database | Supabase (PostgreSQL + pgvector) | Supabase | project: one-goal-v2 |
| Cache | Redis | Railway | internal |
| AI | OpenAI GPT-4o-mini | OpenAI | — |
| Storage | Supabase Storage (avatars bucket) | Supabase | — |
| Auth | JWT + Google OAuth | Supabase Auth | — |
| Email | Custom (core/email.py + services/email.py) | — | — |
| Payments | Stripe (code complete, DB migration PENDING) | Stripe | — |
| Scheduler | APScheduler | Railway (in-process) | — |
| Domain | Cloudflare Registrar | Cloudflare | — |

---

## REPOSITORY STRUCTURE

```
onegoalclaude/
├── backend/
│   ├── ai/
│   │   ├── base.py                    # AI base class
│   │   ├── engines/
│   │   │   ├── coach.py               # AI Coach V2 — PMOS + psychological frameworks
│   │   │   ├── goal_decomposer.py     # Breaks goal into actionable structure
│   │   │   ├── interview.py           # Discovery interview engine V2
│   │   │   ├── profile_updater.py     # Updates identity profile from interactions
│   │   │   ├── reflection_analyzer.py # Analyses task reflections
│   │   │   └── task_generator.py      # Daily identity task generation
│   │   ├── memory/
│   │   │   ├── context_builder.py     # Builds coaching context from history
│   │   │   └── retrieval.py           # pgvector semantic retrieval
│   │   ├── prompts/
│   │   │   └── system_prompts.py      # All AI prompts — centralised and versioned
│   │   └── utils/
│   │       ├── cost_tracker.py        # OpenAI usage tracking
│   │       └── safety_filter.py       # Content safety checks
│   ├── api/
│   │   ├── dependencies/auth.py       # JWT auth dependency
│   │   ├── routers/
│   │   │   ├── admin.py               # Admin endpoints + safety flag review
│   │   │   ├── auth.py                # Login, signup, verify, reset password
│   │   │   ├── billing.py             # Stripe checkout, webhooks, subscriptions
│   │   │   ├── coach.py               # AI coach streaming endpoint
│   │   │   ├── goals.py               # Goal CRUD
│   │   │   ├── onboarding.py          # Onboarding flow steps
│   │   │   ├── profile.py             # Profile, avatar, bio generation
│   │   │   ├── progress.py            # Scores, traits, weekly review
│   │   │   ├── reflections.py         # Task reflections
│   │   │   ├── settings.py            # User settings
│   │   │   └── tasks.py               # Task CRUD + completion + history
│   │   └── schemas/
│   │       ├── auth.py                # Auth request/response models
│   │       └── core.py                # Core pydantic models
│   ├── core/
│   │   ├── cache.py                   # Redis client
│   │   ├── config.py                  # Environment config (Settings class)
│   │   ├── database.py                # Async SQLAlchemy + Supabase session
│   │   ├── email.py                   # Email sending (core transport)
│   │   ├── middleware.py              # CORS, rate limiting
│   │   └── security.py                # JWT, password hashing
│   ├── db/models/
│   │   ├── __init__.py
│   │   ├── goal.py                    # Goal SQLAlchemy model
│   │   ├── identity_profile.py        # Identity profile model
│   │   ├── task.py                    # Task model
│   │   └── user.py                    # User model
│   ├── services/
│   │   ├── analytics.py               # Usage analytics
│   │   ├── billing.py                 # Stripe service layer
│   │   ├── data_export.py             # GDPR data export
│   │   ├── email.py                   # Email service (templates + sending)
│   │   ├── scheduler.py               # APScheduler jobs
│   │   └── scoring.py                 # Transformation score calculation
│   └── main.py                        # FastAPI app entry point
├── frontend/
│   ├── src/app/
│   │   ├── (app)/                     # Authenticated app routes
│   │   │   ├── billing/cancel/        # Billing cancel page
│   │   │   ├── billing/success/       # Post-payment success
│   │   │   ├── coach/                 # AI Coach tab
│   │   │   ├── dashboard/             # Main dashboard
│   │   │   ├── goal/                  # Goal view
│   │   │   ├── progress/              # Progress + traits + weekly review
│   │   │   └── settings/              # Settings, Upgrade, Subscription pages
│   │   ├── (auth)/                    # Unauthenticated auth routes
│   │   │   ├── forgot-password/
│   │   │   ├── login/
│   │   │   ├── resend-verification/
│   │   │   ├── reset-password/
│   │   │   ├── signup/
│   │   │   └── verify-email/
│   │   ├── (onboarding)/              # Onboarding flow
│   │   │   ├── activate/
│   │   │   ├── goal-setup/
│   │   │   ├── interview/
│   │   │   └── preview/
│   │   ├── auth/callback/             # Google OAuth callback
│   │   ├── layout.tsx                 # Root layout
│   │   └── page.tsx                   # Landing page
│   ├── src/components/
│   │   ├── OneGoalLogo.tsx
│   │   ├── QuotaBanner.tsx            # Tier quota warning banner
│   │   ├── dashboard/ScoreRing.tsx
│   │   ├── dashboard/WeekGrid.tsx
│   │   ├── landing/                   # Landing page components
│   │   ├── reflection/ReflectionModal.tsx
│   │   └── task/TaskCard.tsx
│   ├── src/hooks/                     # useReducedMotion, useScrollProgress, useWebGLSupport
│   ├── src/lib/
│   │   ├── api.ts                     # Full API client — ALL backend calls go through here
│   │   └── utils.ts
│   └── src/stores/auth.ts             # Zustand auth store
├── dead code/                         # Retired files — do not touch or import from here
├── docs/                              # Project documentation (this file lives here too)
├── CLAUDE.md                          # THIS FILE — read at start of every session
└── TODO.md                            # Current sprint tasks — check this every session
```

---

## WHAT IS FULLY BUILT AND WORKING

### Core user journey (end-to-end)
- Landing page → Sign up / Login (email + Google OAuth) → AI Discovery Interview (V2, 3-phase) → Goal synthesis → Strategy preview → Activation → Dashboard → Daily tasks → AI Coach → Progress tracking → Settings

### Backend systems
- JWT auth with token refresh
- Google OAuth via Supabase
- Email verification + password reset
- AI Interview Engine V2 (psychological funnel)
- Goal synthesis from interview
- Daily task generation (APScheduler, 4am sweep + guardrail)
- AI Coach V2 with PMOS + psychological frameworks + session memory (pgvector)
- Transformation scoring system (repaired March 20)
- Traits timeline
- Weekly review generation
- Reflection submission + analysis
- Avatar upload (Supabase Storage)
- AI bio generation (once on first Settings visit)
- Invite/share flow
- Tier-based quota enforcement on AI coach
- GDPR data export + account deletion
- Admin endpoints + safety flag review
- Email service (welcome emails, verification reminders)
- Cost tracking (OpenAI usage)
- Safety filter

### Frontend screens
- Landing page (pricing tiers visible)
- Full auth flow (login, signup, verify, forgot/reset password, resend verification)
- Full onboarding flow (interview, goal-setup, preview, activate)
- Dashboard (today's task, streak, score, traits, task history panel)
- AI Coach tab (streaming, quota-aware)
- Progress tab (transformation score, traits timeline, weekly review)
- Settings page (avatar, bio, share)
- Billing pages (success, cancel, upgrade, subscription management)

### Billing (PARTIALLY BUILT — SEE CRITICAL ISSUES)
- Stripe service layer: `services/billing.py`
- Billing router: `api/routers/billing.py`
- Frontend billing pages: success, cancel, upgrade, subscription
- Quota enforcement by tier in coach router
- ⚠️ MISSING: `subscriptions` table does not exist in Supabase database
- ⚠️ MISSING: Stripe webhook not yet receiving events (no DB to write to)

---

## CRITICAL KNOWN ISSUES — CHECK BEFORE EVERY SESSION

### 1. BILLING DATABASE MIGRATION PENDING (HIGH PRIORITY)
The `subscriptions` table does not exist in Supabase. All billing code will fail at runtime.
Migration needed: `subscriptions`, `invoices` tables matching `services/billing.py` schema.
**Do not touch billing frontend until this is fixed.**

### 2. WORKTREE CONTAMINATION
`.claude/worktrees/adoring-leavitt/` contains a full duplicate of the codebase.
This was created by a Claude Code session. It should be removed from the repo.
```bash
rm -rf .claude/worktrees/
git add -A && git commit -m "chore: remove claude code worktree artifacts"
```

### 3. PUSH NOTIFICATIONS — NOT BUILT
No web push or email notification system for daily re-engagement.
APScheduler generates tasks but does not notify users.
All 7 users tried the coach exactly once and never returned — this is the retention blocker.

### 4. POSTHOG / SENTRY IN DEAD CODE
PostHog and Sentry are referenced in `dead code/` but `frontend/src/lib/posthog.ts` still exists in the live frontend. Verify it is not being imported anywhere.

---

## ENGINEERING RULES — NEVER VIOLATE THESE

1. **Supabase Storage** — always use `supabase-py` client, never raw `httpx` calls
2. **asyncpg vector syntax** — never use `:param::vector`. Always inline embeddings in f-strings or use `CAST(:param AS vector)`
3. **asyncpg type casts** — avoid `::jsonb`, `::text[]` etc. with named params. Use `CAST()` syntax
4. **FastAPI route ordering** — named routes (`/history`, `/today`) MUST be defined BEFORE catch-all routes (`/{date}`)
5. **Streak updates** — always update immediately on user action, never defer to scheduler
6. **Task queries** — never filter on specific `task_type` values unless deliberately excluding
7. **JSON serialisation** — always `json.dumps()`, never `str()` on structured data
8. **Environment variables** — never hardcode. All config lives in `backend/core/config.py` (Settings class)
9. **File delivery** — always deliver complete files. Pelumi deploys by replacing whole files
10. **No partial diffs** unless the change is a single clearly-identified line

---

## DEPLOYMENT PROCEDURE

### Backend (Railway)
```bash
git add -A
git commit -m "your message"
git push origin main
# Railway auto-deploys in ~10–15 minutes
# Monitor: Railway dashboard → Deployments → View logs
```

### Frontend (Vercel)
```bash
# Same git push — Vercel auto-deploys in ~2 minutes
# Monitor: Vercel dashboard → Deployments
```

### Environment variables
- Backend env vars: Railway → Service → Variables
- Frontend env vars: Vercel → Project → Settings → Environment Variables
- Never commit `.env` files

---

## MONETISATION TIERS

| Tier | Name | Price | Coach quota |
|---|---|---|---|
| Free | The Spark | $0 | 5 messages/day |
| Pro | The Forge | $3.99/month | Unlimited |
| Elite | The Identity | $8.99/month | Unlimited + re-interview |

Stripe is integrated in code. Billing DB migration is the blocker to going live.

---

## DATABASE — KEY TABLES (CONFIRMED EXISTING)

- `users` — core user record
- `goals` — user's one goal (refined_statement, not title)
- `identity_profiles` — identity anchor, bio, transformation score, streak, days_active
- `tasks` — daily tasks (task_type: identity_anchor, micro_action)
- `coaching_sessions` — AI coach session records (7 total across all users)
- `reflections` — task reflection submissions
- `progress_metrics` — scoring data (depth_score column, NOT avg_depth_score)
- `user_embeddings` — pgvector embeddings for coach memory retrieval

### MISSING (pending migration)
- `subscriptions` — Stripe subscription data
- `invoices` — payment history

---

## AI SYSTEMS

### Interview Engine V2
3-phase psychological funnel — never announced to user:
1. Find the tension ("What's the one area... you'll be disappointed in yourself?")
2. Find the real goal (probe past attempts, obstacles, identity)
3. Crystallise (AI names the goal, user corrects; identity anchor question)

### Coach V2 (PMOS + Psychological Frameworks)
Upgraded March 20. Includes PMOS framework and psychological coaching models.
Uses pgvector for semantic retrieval of past sessions.
Streaming response via FastAPI `StreamingResponse`.
Quota-enforced by tier (5/day free, unlimited pro/elite).

### Task Types
- `identity_anchor` — who you are becoming
- `micro_action` — small concrete action aligned to identity

### Scoring
Real-time triggers on task completion. Repaired March 20 with proper columns and triggers.

---

## SESSION OPERATING PROCEDURE

**At the start of every session:**
1. Read this file completely
2. Read `TODO.md` to know the current sprint focus
3. Ask Pelumi: "What are we working on today?" if TODO is ambiguous
4. Do not start coding until you understand the specific task

**During a session:**
- Explain the problem in plain English before writing code
- Deliver complete files, not diffs
- Test logic mentally before delivering — check for asyncpg gotchas, route ordering, type casts
- After each completed task, update `TODO.md` to reflect current state

**Debugging order:**
1. Check Railway logs first
2. Check Supabase query results
3. Reproduce the logic flow manually
4. Fix root cause, not symptoms

**When touching billing:**
- Check if `subscriptions` table exists before writing any billing code
- Billing DB migration must happen before any billing feature is testable

---

## CURRENT SPRINT — CHECK TODO.md FOR LIVE VERSION

Phase 1 — MVP Close (target: 4 weeks from March 25, 2026):
1. ✅ Core user journey
2. ✅ AI coach V2
3. ✅ Stripe integration (code)
4. ⬜ Billing DB migration (subscriptions + invoices tables)
5. ⬜ Stripe webhook live testing
6. ⬜ Web push notifications
7. ⬜ Email notifications (daily task reminder)
8. ⬜ Mobile QA pass
9. ⬜ Remove .claude/worktrees/ from repo
10. ⬜ Verify posthog.ts not imported in live code

Phase 2 — Growth (Months 2–3):
- Expand to 50+ real users
- Re-interview flow (Elite feature)
- React Native / Capacitor mobile wrapper
- Analytics dashboard (PostHog or equivalent)
- A/B test onboarding conversion

Phase 3 — Mobile App (Month 3):
- iOS + Android via Capacitor wrapper on existing Next.js
- App Store + Play Store submission
- Push notifications via native APIs

---

## AI AGENTS ROSTER (to be built)

### Agent 1 — PM Agent (Product Manager)
**Trigger:** "Ask the PM agent" or start of any planning session
**Role:** Maintains PRD, updates TODO.md, tracks sprint progress, writes tickets
**Personality:** Organised, direct, no fluff

### Agent 2 — Marketing Agent
**Trigger:** "Ask the marketing agent" or any content/growth task
**Role:** Writes copy, social posts, email sequences, growth experiments
**Knows:** OneGoal Pro positioning, IIC Networks brand, Pelumi's author voice
**Personality:** Sharp, identity-driven, Pelumi's voice

### Agent 3 — QA Agent
**Trigger:** "Ask the QA agent" or before any deployment
**Role:** Reviews code for bugs, checks against engineering rules, writes test cases
**Personality:** Paranoid, thorough, catches what others miss

### Agent 4 — Support Agent
**Trigger:** "Ask the support agent" or any user feedback/response task
**Role:** Drafts user responses, handles feedback, escalates real bugs
**Personality:** Warm, identity-language fluent, human

---

## OTHER PELUMI BRANDS (AI agents support these too)

### IIC Networks
Influence, Impact, Change. Coaching, speaking, leadership development.
Brand voice: Authoritative, practical, faith-informed, African professional context.

### Author Brand (@PelumiOlawole)
Book: *Petty Little Things* — 50 habits quietly ruining your life.
Voice: Conversational, honest, sometimes sharp, always constructive.
Platform: Primarily LinkedIn + Instagram.

---

## HOW TO UPDATE THIS FILE

When something significant changes — new feature shipped, bug pattern discovered,
new engineering rule, stack change — update the relevant section and commit:

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — [what changed]"
git push origin main
```

Then paste the updated contents into this Claude Project's custom instructions to keep
the live session version in sync.

---

*This file is the single source of truth for all Claude sessions on OneGoal Pro.*
*If something contradicts this file, this file wins unless Pelumi says otherwise.*