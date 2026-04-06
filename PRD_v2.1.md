# OneGoal Pro — Product Requirements Document (PRD)
# Version: 2.1 — Post-Security Hardening Edition
# Date: April 6, 2026
# Owner: Pelumi Olawole, One Goal Pro Ltd (Company No. 17127527)
# Status: MVP live. 78 registered users. 1 paying subscriber. MRR: £3.74.

---

## CHANGELOG FROM v2.0

| Section | Change |
|---|---|
| Company | One Goal Pro Ltd incorporated, company number added |
| Security | Full auth security overhaul documented |
| Tiers | Pricing framework rewritten — outcome-based differentiation |
| Auth | JWT lifetime, token hashing, JTI blocklist, email cooldowns |
| Billing | Cancellation grace period fix documented |
| Analytics | PostHog live and confirmed |
| Agents | Two new agents added (Learning, Funding, Behaviour) |
| Roadmap | Phase 1 updated to reflect current state |
| Legal | Company, trademark, bank account status updated |
| Users | User count updated to 78 |

---

## 1. PRODUCT OVERVIEW

### 1.1 What It Is
OneGoal Pro is an identity-based goal transformation system. It helps people commit to the one goal that will genuinely change who they are — not just what they do. Unlike conventional goal-setting tools that track tasks, OneGoal Pro tracks identity evolution.

### 1.2 Core Philosophy
Most goal-setting fails because people set the wrong goal, or the right goal with the wrong framing. OneGoal Pro operates on three principles:
1. You don't have a focus problem. You have an identity problem.
2. Behaviour follows identity. Change who you are, and the actions follow.
3. One goal, pursued with full commitment, beats ten goals pursued with divided attention.

### 1.3 Tagline
**"One goal. Full commitment. No excuses."**

### 1.4 What Makes It Different
- The user does not enter their goal. They discover it through an AI-guided psychological interview.
- Progress is measured as identity transformation, not task completion rate.
- The AI coach (Coach PO) knows who you are becoming — it has memory, context, and a consistent point of view.
- The product is built around a single constraint: one goal, indefinite horizon.
- Only single-goal platform in the identity-based goal space. Every competitor supports multiple goals.

### 1.5 Company
- **Legal name:** One Goal Pro Ltd
- **Company number:** 17127527
- **Registered address:** 5 Brayford Square, London, E1 0SG
- **SIC codes:** 62012, 85590
- **Incorporated:** 31 March 2026
- **Founder:** Pelumi Olawole
- **IIC Networks and Petty Little Things are legally and structurally separate.**

---

## 2. TARGET USERS

### 2.1 Primary Persona — The Committed Changer
- Age: 25–45
- Ambitious professional, solopreneur, or creative
- Has tried other apps and abandoned them
- Knows what they want to change but keeps failing to sustain it
- Motivated by identity and who they're becoming, not just productivity metrics
- Willing to pay for something that actually works

### 2.2 Secondary Persona — The Seeker
- Knows something needs to change but hasn't articulated what
- Looking for clarity, not just accountability
- The AI interview is specifically designed for this person

### 2.3 Who It Is Not For
- People who want a task manager with more features
- People who want social accountability feeds
- People who want to track multiple goals simultaneously

---

## 3. USER FLOWS

### 3.1 Discovery & Sign Up
```
Landing page
  → View pricing tiers (The Spark / The Forge / The Identity)
  → Click "Start the interview" or "Start Free"
  → Sign up: email+password OR Google OAuth
  → Email verification sent (token stored as SHA-256 hash in DB)
  → Verify email → account activated
  → Enter onboarding flow
```

### 3.2 Onboarding Flow (One-time)
```
Interview page (/interview)
  → AI Discovery Interview (V2 — 3-phase psychological funnel)
     Phase 1: Find the tension
     Phase 2: Find the real goal
     Phase 3: Crystallise identity anchor
  → Goal setup page
  → Strategy preview
  → Activate (triggers first 3 days of task generation)
  → Dashboard
```

### 3.3 Daily Loop (Core Engagement)
```
Dashboard
  → View today's task (identity_anchor or micro_action type)
  → Complete task → Reflection modal → Submit reflection
  → Streak updates immediately
  → Transformation score updates
  → AI Coach tab available (quota-enforced by tier)
  → Progress tab for weekly review + traits timeline
```

### 3.4 Billing & Upgrade Flow
```
Settings → Upgrade tab (/settings/upgrade)
  → View tier comparison
  → Select The Forge (£4.99/mo) or The Identity (£10.99/mo)
  → Stripe Checkout session created
  → Payment → Stripe webhook → subscriptions + users tables updated (dual-write)
  → User redirected to /billing/success → verify-session called
  → Plan upgrades immediately (quota enforcement updates in real-time)
```

### 3.5 Cancellation Flow
```
Settings → Subscription → Cancel
  → Stripe sets cancel_at_period_end = true
  → Status stays "active" until period end (user retains access)
  → At period end: status → "ended", downgraded to Spark
```

### 3.6 Account Management
```
Settings
  → Export my data (GDPR Art. 20 — downloads JSON)
  → Delete account (soft delete → 30-day grace period → hard delete)
```

---

## 4. FEATURE SPECIFICATIONS

### 4.1 Authentication

**Current state as of April 6, 2026:**
- JWT access token lifetime: **1 hour** (was 24h, reduced April 5)
- Refresh token: 7 days, rotates on use
- JTI (unique token ID) in every access token — logout blocklists JTI in Redis
- Password reset tokens: stored as SHA-256 hash, plaintext only in email link
- Email verification tokens: same hash pattern
- Per-email 5-minute cooldown on forgot-password and resend-verification
- Failed login logs use truncated SHA-256 hash of email (not plaintext)
- Admin emails: read from `ADMIN_EMAILS` Railway env var (not hardcoded)

#### Sign Up
- Fields: email, password (min 8 chars), optional display name
- Google OAuth option (Supabase)
- Email verification required — user set `is_active=False` until verified
- On verify: `is_active=True`, onboarding_status → INTERVIEW_STARTED

#### Login
- Email+password or Google OAuth
- Returns JWT access + refresh token pair
- Requires `email_verified_at` to be set (403 if not verified)

#### Password Reset
- Token stored as SHA-256 hash — existing plaintext tokens from before April 5 no longer valid
- Reset link expires in 1 hour
- Token cleared after use

---

### 4.2 AI Discovery Interview

**Engine:** `backend/ai/engines/interview.py`
**Route:** `/interview` (frontend path — NOT `/onboarding/interview`)
**Quota:** 50 messages per interview (enforced as of April 5, 2026)

#### Rules
- One question at a time. Non-negotiable.
- Reflect before asking. Every response acknowledges what was said.
- Never announce phases to the user.
- 8–15 message exchanges typical.
- Phases never surfaced to user.

#### Phases (internal)
1. Find the tension
2. Find the real goal
3. Crystallise identity anchor

#### Completion Output
```json
{
  "refined_statement": "string",
  "identity_anchor": "string",
  "core_values": ["string"],
  "self_reported_strengths": ["string"],
  "key_tension": "string",
  "motivation_style": "string"
}
```

---

### 4.3 Dashboard

**Route:** `/dashboard`

#### Components
- Today's task card — title, description, complete/skip buttons
- Streak counter — real-time update on completion
- Transformation score ring — 0–100 visual arc
- Traits panel — identity traits with timeline
- Task history panel — last 30 tasks, colour-coded (green/amber/red)
- Week grid — 7-day completion view

---

### 4.4 AI Coach (Coach PO)

**Route:** `/coach`
**Engine:** `backend/ai/engines/coach.py` (V2)
**Personality:** Coach PO — warm but direct, identity-language fluent, challenges comfortable excuses, references user's specific goal and identity anchor always.

#### V2 Features
- PMOS framework (Purpose, Momentum, Obstacles, Strategy)
- Psychological coaching frameworks
- Session memory via pgvector semantic retrieval
- Streaming responses (SSE)
- Moment tracking (breakthroughs, resistance, commitments, vulnerability)
- Session continuity (opening/closing insights, next session hooks)
- Safety filter with crisis escalation
- Prompt injection detection

#### Quota Enforcement
| Tier | Daily coach messages |
|---|---|
| The Spark (Free) | 5 |
| The Forge | Unlimited |
| The Identity | Unlimited |

#### Quota Banner UX
- Shows remaining messages at 3, 2, 1, 0
- Styled by severity: amber (notice) → orange (urgent) → red (critical)
- Upgrade CTA: "Upgrade to Forge" → `/settings/upgrade`
- Banner is dismissible

---

### 4.5 Progress

**Route:** `/progress`

#### Transformation Score
- 0–100 scale
- Calculated from: task completion rate, reflection depth, streak consistency, coach engagement
- Updates in real-time on task completion
- Full breakdown: Forge and Identity tiers only

#### Traits Timeline
- Identity traits tracked over time
- Data from `progress_metrics` table

#### Weekly AI Review
- Generated Monday 2am UTC by scheduler
- AI summary: week's progress, patterns, next week focus
- Available in Progress tab and as email (Forge + Identity)

---

### 4.6 Notifications

#### Email (Live)
- Daily task email: sent at midnight user's local time (hourly sweep)
- Re-engagement email: 3 days inactive, throttled by `notification_queue` (3-day cooldown)
- Interview nudge: 24h and 72h after signup if no interview completed
- Verification reminder: 24h after signup if unverified
- All email via Resend (`services/email.py`)
- **Correct interview link: `https://onegoalpro.app/interview`** (fixed April 6)

#### Web Push (Live)
- Service worker registered on app load
- Tokens stored in `push_subscriptions` table
- Daily push at 8am UTC for users with pending tasks
- Stale subscriptions (HTTP 410) auto-deleted
- Nudge pushes at 24h and 72h for users who haven't completed interview

---

### 4.7 Settings

**Route:** `/settings`

#### Profile
- Avatar upload — magic byte validated (JPEG/PNG/WebP only, max 5MB)
- AI bio generation — generated once on first visit, never regenerated
- Display name, timezone

#### Subscription
- View current plan and billing cycle
- Upgrade → `/settings/upgrade`
- Cancel → keeps access until period end (cancel_at_period_end)
- Invoice history

#### Account
- Export data (GDPR)
- Delete account

#### Share
- AI-generated invite message
- Share URL uses `settings.frontend_url` (not hardcoded)

---

### 4.8 Billing

**Files:** `backend/api/routers/billing.py`, `backend/services/billing.py`

#### Tiers (Updated Framework — April 6, 2026)

| Tier | Name | Price | Position |
|---|---|---|---|
| Free | The Spark | £0 | Taster — genuine progress with a visible ceiling |
| Pro | The Forge | £4.99/mo | The real product — for users who've proved it works |
| Elite | The Identity | £10.99/mo | Full commitment — for users building a new self |

#### Tier Differentiation (Outcome-Based)

**The Spark — What it feels like:**
- Full interview and goal discovery
- One daily identity task
- Coach with 5 messages/day — enough to feel the value, limited enough to create friction at the right moment
- Transformation score visible, breakdown locked
- No weekly review — progress is happening but there's no ritual acknowledgement of it
- **Upgrade trigger:** Hit coach limit mid-conversation when genuinely engaged. See score improving but can't access the full picture. Complete a week of tasks and receive no review.

**The Forge — What justifies £4.99:**
- Coach PO that knows you — full session memory, no limits, real continuity between sessions
- Weekly review every Monday — a ritual that makes users feel seen
- Full transformation score breakdown — see exactly what's changing and why
- Reflection insights — patterns surfaced from past reflections
- Goal history and archive
- **Positioning:** "I'm serious now. Give me the full system." Less than a coffee a month for something actively working on you.
- **CTA:** "Go deeper"

**The Identity — What justifies £10.99:**
- Everything in Forge
- Re-interview when goal is achieved or outgrown — the ability to evolve, not just improve
- Behavioural pattern summary — what the system has learned about you specifically, surfaced visibly
- Priority task generation
- Early feature access
- Priority support
- **Positioning:** For people fully committed to identity change, not just testing if it works.
- **CTA:** "Commit fully"

#### Cancellation
- `cancel_at_period_end=True` keeps status as "active"
- User retains full paid access until period end
- Status only changes to "ended" after Stripe fires `customer.subscription.deleted`

#### Webhook Events Handled
- `checkout.session.completed` → activate subscription (dual-write: users + subscriptions)
- `customer.subscription.updated` → update plan/status
- `customer.subscription.deleted` → set status to "ended"
- `invoice.payment_succeeded` → log invoice
- `invoice.payment_failed` → flag for retry

---

### 4.9 Security (Updated April 5, 2026)

#### Auth Security
- bcrypt 12 rounds for passwords
- JTI blocklist in Redis — logout immediately invalidates token
- JWT access token: 1 hour lifetime
- Refresh token: 7 days, rotation on use
- Password reset tokens: SHA-256 hashed in DB
- Admin access: ADMIN_EMAILS env var only (not in source code)

#### Rate Limiting
- Auth routes: fail **closed** when Redis unavailable (returns 503)
- API routes: fail open (availability priority)
- Per-email cooldowns: 5 minutes on password reset and verification resend

#### Frontend Security
- Content-Security-Policy header on all routes
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin
- Avatar upload: magic byte validation (not client MIME type)

#### Privacy
- Sentry: 5% sample rate (was 100%)
- AI route bodies scrubbed before Sentry transmission
- Failed login logs: email hash only (not plaintext)
- Share URL uses env var (not hardcoded old Vercel domain)

---

### 4.10 Analytics

#### PostHog (Live as of April 2026)
- `NEXT_PUBLIC_POSTHOG_KEY` set in Vercel
- `PostHogInit` component in `layout.tsx`
- User identification on login: `posthog.identify(user.id, {email, tier})`
- Key events tracked: `interview_completed`, `task_completed`, `coach_session_started`, `upgrade_modal_viewed`, `subscription_activated`
- Core funnel configured: pageview → signup → interview_completed → task_completed → coach_session_started

#### Sentry (Live)
- Frontend: `NEXT_PUBLIC_SENTRY_DSN` in Vercel
- Backend: `SENTRY_DSN` in Railway
- Sample rate: 5% (reduced from 100%)
- AI routes scrubbed before send

---

### 4.11 Admin

**File:** `backend/api/routers/admin.py`
**Access:** `ADMIN_EMAILS` Railway env var

- View and action safety-flagged content
- Bulk welcome email to existing users
- User list (internal only)

---

## 5. API SPECIFICATION

### 5.1 Base URL
Production: `https://api.onegoalpro.app/api`

### 5.2 Authentication
All protected endpoints: `Authorization: Bearer <jwt_token>`

### 5.3 Key Endpoint Notes
- Interview route: `POST /onboarding/interview/message` — quota enforced (50 msgs)
- Coach streaming: `POST /coach/sessions/{id}/message` — SSE, quota enforced by tier
- Frontend interview URL: `/interview` (NOT `/onboarding/interview`)
- Billing verify: `POST /billing/verify-session` — called by success page

---

## 6. DATABASE

### 6.1 Confirmed Tables (as of April 2026)

**Core:** `users`, `goals`, `identity_profiles`, `daily_tasks`, `coaching_sessions`, `reflections`, `progress_metrics`, `user_embeddings`

**Billing:** `subscriptions` (unique on user_id, all users seeded), `invoices`

**Notifications:** `notification_queue`, `push_subscriptions`

**AI/Analytics:** `ai_coach_messages`, `ai_coach_sessions`, `ai_interactions`, `ai_safety_flags`, `behavioral_patterns`, `behavioral_snapshots`, `coach_interventions`, `coach_moments`, `coach_patterns`, `coach_safety_flags`, `engagement_events`, `identity_traits`, `milestones`, `objectives`, `onboarding_interview_state`, `trait_progress_summary`, `weekly_reviews`

**Views:** `users_needing_intervention`, `user_dashboard`

**Other:** `data_processing_consent`, `deletion_requests`, `integration_configs`, `system_config`

### 6.2 Key Column Notes
- `goals.refined_statement` (not `title`)
- `reflections.depth_score` (not `avg_depth_score`)
- `goals.required_identity` (used in daily task email query)
- `daily_tasks.task_type`: values are `identity_anchor`, `micro_action` (not `becoming`)

---

## 7. SECURITY & PRIVACY

See Section 4.9 for full security specification.

### 7.1 GDPR
- Data export: `/auth/export` returns full JSON
- Account deletion: soft → 30-day grace → hard cascade
- Sentry scrubbing: AI routes excluded from payload capture
- No data sold or shared

### 7.2 Pending Legal/Compliance
- ICO registration as data controller (£40 at ico.org.uk/registration)
- Data Processing Agreements with: Supabase, OpenAI, Railway, Resend, Vercel
- 18+ age declaration checkbox on signup form
- Company details in website footer (legally required for Ltd companies)

---

## 8. ERROR HANDLING

### 8.1 Backend Error Responses
```json
{ "detail": "Human-readable message" }
```

| Code | Meaning |
|---|---|
| 400 | Bad request |
| 401 | Unauthenticated or token revoked |
| 403 | Forbidden (wrong role, tier, or unverified email) |
| 404 | Not found |
| 429 | Rate limit or quota exceeded |
| 503 | Service unavailable (Redis down on auth routes) |

### 8.2 AI Failure States
- OpenAI down → "Coach is unavailable right now"
- Interview interrupted → resume from last message on reload
- Task generation fails → fallback template task, retry on morning sweep

---

## 9. ANALYTICS & TRACKING

### 9.1 PostHog Events
| Event | Trigger |
|---|---|
| `signup_completed` | Account created |
| `interview_completed` | Interview data submitted |
| `task_completed` | Task marked done |
| `coach_session_started` | First message in session |
| `upgrade_modal_viewed` | Upgrade page viewed |
| `subscription_activated` | Stripe webhook: checkout complete |

### 9.2 Key Metrics
- Daily active users
- Interview completion rate
- Daily task completion rate
- Coach sessions per user per week
- Free → Forge conversion rate
- 30-day retention (target: measure first cohort by end of April)

---

## 10. MONETISATION

### 10.1 Tiers
See Section 4.8 for full tier differentiation framework.

| Tier | Price | Coach | Weekly Review | Score Breakdown | Re-interview |
|---|---|---|---|---|---|
| The Spark | £0 | 5/day | No | No | No |
| The Forge | £4.99/mo | Unlimited | Yes | Yes | No |
| The Identity | £10.99/mo | Unlimited | Yes | Yes | Yes + behaviour patterns |

### 10.2 Revenue
- Monthly recurring via Stripe (live, 1 active subscriber)
- No annual plan in UI yet (Stripe product exists, not surfaced)
- No ads. No data monetisation.
- 14-day money-back guarantee on all paid plans

### 10.3 Growth Targets (Revised)
- **Now:** 1 paying subscriber, £3.74 MRR, 78 registered users
- **Near-term:** 10 paying subscribers (key milestone for funding readiness)
- **Funding readiness:** 10 paying subscribers + one clear organic acquisition story + 30-day retention data

---

## 11. LEGAL & COMPANY STATUS

| Item | Status |
|---|---|
| Company incorporation | ✅ Done — One Goal Pro Ltd, No. 17127527 |
| Registered office | ✅ Ghost Mail, 5 Brayford Square, London E1 0SG |
| Terms of Service | ✅ Live at /terms |
| Privacy Policy | ✅ Live at /privacy |
| IP Assignment Agreement | ✅ Executed 31 March 2026 |
| Trademark — "One Goal Pro" (Classes 41+42) | ⏳ Pending Companies House certificate |
| Trademark — "Coach PO" (Classes 41+42) | ⏳ Pending Companies House certificate |
| Starling business bank account | ⏳ Pending UTR from HMRC |
| SEIS advance assurance | ⏳ Ready to submit via Government Gateway |
| ICO data controller registration | ⏳ Pending (£40) |
| DPAs with processors | ⏳ Pending |

---

## 12. ROADMAP

### Phase 1 — MVP Close (Target: April 22, 2026)

**Completed:**
- ✅ Core user journey end-to-end
- ✅ AI Interview V2
- ✅ AI Coach V2 (PMOS + memory)
- ✅ Transformation scoring
- ✅ Tier-based quota enforcement
- ✅ Google OAuth
- ✅ Email verification + password reset
- ✅ Avatar upload (magic byte validated)
- ✅ AI bio generation
- ✅ Streak real-time updates
- ✅ Task history panel
- ✅ GDPR data export + account deletion
- ✅ Admin endpoints
- ✅ Billing — Stripe checkout, webhooks, cancel, resume, invoices
- ✅ Email notifications — daily task, re-engagement, interview nudge, verification reminder
- ✅ Web push notifications
- ✅ Landing page — all marketing brief changes
- ✅ Security hardening — JTI blocklist, token hashing, CSP headers, rate limiting
- ✅ PostHog analytics live
- ✅ Sentry error tracking live

**Remaining:**
- [ ] Tier feature differentiation implementation (upgrade page copy, quota enforcement updates)
- [ ] Stripe live end-to-end test
- [ ] Password reset end-to-end test
- [ ] Mobile QA pass
- [ ] ICO registration
- [ ] DPAs with processors
- [ ] Company details in footer
- [ ] PostHog funnel review and optimisation
- [ ] SEIS advance assurance submission
- [ ] Zinc VC application

### Phase 2 — Growth (Months 2–3)
- Grow to 50+ real users
- Re-interview flow (The Identity tier)
- Annual billing option (surfaced in UI)
- A/B test onboarding completion rate
- Referral mechanics
- Apple OAuth
- Weekly email digest
- Behavioural pattern summary visible to Identity users

### Phase 3 — Mobile App (Month 3+)
- Capacitor wrapper on Next.js codebase
- iOS + Android builds
- App Store + Play Store submission
- Native push notifications (APNs + FCM)

---

## 13. AI AGENT ROSTER

All agent files live in `docs/agents/`. Open new Claude conversation, paste agent file, give task.

| Agent | File | Purpose |
|---|---|---|
| PM Agent | docs/agents/PM_AGENT.md | Sprint management, documentation, prioritisation |
| Marketing Agent | docs/agents/MARKETING_AGENT.md | Copy, content, brand, social media |
| QA Agent | docs/agents/QA_AGENT.md | Code review, bug detection, pre-deploy checklist |
| Support Agent | docs/agents/SUPPORT_AGENT.md | User communication, feedback handling |
| Learning Agent | docs/agents/LEARNING_AGENT.md | SaaS/founder education |
| Funding Agent | docs/agents/FUNDING_AGENT.md | Pre-seed fundraising preparation |
| Behaviour Agent | docs/agents/BEHAVIOUR_AGENT.md | Daily Railway log analysis |

---

## 14. ENGINEERING RULES

1. **asyncpg vector syntax** — never `::vector`. Always f-string inline or `CAST(:param AS vector)`
2. **asyncpg type casts** — avoid `::jsonb`, `::text[]` with named params. Use `CAST()` syntax
3. **FastAPI route ordering** — named routes BEFORE catch-all routes (`/{date}`)
4. **Streak updates** — immediate on user action, never deferred
5. **Task queries** — never filter on specific `task_type` values unless deliberately excluding
6. **JSON serialisation** — always `json.dumps()`, never `str()` on structured data
7. **Environment variables** — never hardcode. All config in `backend/core/config.py`
8. **File delivery** — always deliver complete files. Pelumi deploys by replacing whole files
9. **Billing dual-write** — webhook handlers write to BOTH `users` AND `subscriptions` tables
10. **Frontend routing** — all Next.js folder names lowercase (Vercel is case-sensitive on Linux)
11. **Import before file** — never import a file before it exists in the repo. Commit both together.
12. **Avatar upload** — validate by magic bytes, not client-supplied content_type
13. **Token storage** — reset and verification tokens stored as SHA-256 hashes, never plaintext
14. **Admin emails** — read from `settings.admin_emails_list`, never hardcoded in source

---

## 15. TECH STACK

| Layer | Technology | Provider |
|---|---|---|
| Frontend | Next.js 15 (React 19) | Vercel |
| Backend | FastAPI (Python) | Railway |
| Database | Supabase (PostgreSQL + pgvector) | Supabase |
| Cache | Redis | Railway |
| AI | OpenAI GPT-4o-mini | OpenAI |
| Storage | Supabase Storage (avatars bucket) | Supabase |
| Auth | JWT + Google OAuth via Supabase | Supabase |
| Email | Resend | Resend |
| Payments | Stripe (live) | Stripe |
| Scheduler | APScheduler (in-process) | Railway |
| Error tracking | Sentry | Sentry |
| Analytics | PostHog | PostHog |
| Domain | Cloudflare Registrar | Cloudflare |
| GitHub | github.com/pelumiolawole/onegoalpro | GitHub |

---

*End of PRD v2.1*
*Next review: after Phase 1 close (April 22, 2026)*
*Owner: Pelumi Olawole, One Goal Pro Ltd*