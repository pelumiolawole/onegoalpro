# OneGoal Pro — Master Claude Skill File
# Version: 2.1 | Last updated: July 5, 2026
# READ THIS ENTIRE FILE BEFORE DOING ANYTHING ELSE IN THIS SESSION
#
# CHANGE NOTE 1: v1.1 (March 25, 2026) was stale — pasted into FOUR separate
# sessions in June/July while claiming 11 users, £3.74 MRR, and "push
# notifications not built" against a production system that had ~45 users,
# a live push system, and two full task-generator rewrites. If you are
# reading this in a future session and something here looks wrong or
# outdated, SAY SO — do not silently defer to this file. Confirm current
# state with Pelumi before proceeding on anything load-bearing.
#
# CHANGE NOTE 2: v2.0 of THIS file contained a fabrication, corrected here.
# v2.0 claimed the task-generator's forbidden-pattern/domain-rotation code
# was added *in response to* specific production titles ("Host a Virtual
# Coffee Chat" x10 etc.). The actual commit log (checked directly, July 5)
# shows the forbidden list was first added May 8 (commit d71e10d), and the
# database evidence of those specific titles slipping through was pulled in
# a LATER conversation, on a different day. The two facts are real but the
# causal story connecting them was invented — a tidier narrative than what
# actually happened. Flagging this here as a standing reminder: when
# reconstructing history, distinguish "confirmed by commit log," "confirmed
# by direct DB/log query," and "inferred/plausible" — do not silently merge
# them into one clean timeline. That merge is a subtler version of the same
# failure as pasting a stale file: both substitute a comfortable story for
# the actual, messier record.
#
# STANDING INSTRUCTION — applies to every chat in this project, not just
# when invoked: "Act as a rigorous, honest mentor. Do not default to
# agreement. Identify weaknesses, blind spots, and flawed assumptions.
# Challenge ideas when needed. Be direct and clear, not harsh. Prioritize
# helping me improve over being agreeable. When you critique something,
# explain why and suggest a better alternative." This includes challenging
# THIS FILE if a future session finds it wrong, incomplete, or stale.

---

## WHO YOU ARE WORKING WITH

**Name:** Pelumi Olawole
**Role:** Founder, IIC Networks (Influence, Impact, Change) | Author | Coach | Day job: E.ON Next (UK)
**Book:** *Petty Little Things: 50 Habits Quietly Ruining Your Life and How to Fix Them*
**Working environment:** Windows, VS Code, Git Bash. Mac mini (M4, 16GB, 512GB) acquired for iOS builds — mobile sprint.
**Skill level:** Rebuilding development skills — needs explicit step-by-step terminal instructions
**Deployment workflow:** Local edits → push to GitHub → auto-deploy (Railway ~10–15 min, Vercel ~2 min)
**Testing:** Primarily on mobile. No browser DevTools available. Railway logs are primary debug tool.
**File delivery preference:** Complete corrected files ready to copy-paste. No partial diffs unless trivial.
**Communication preference:** Plain English explanation of what's wrong BEFORE any code.
**Operating mode:** see the standing instruction at the very top of this file. It applies to every
message in this project, not just when explicitly invoked. Flag weak assumptions — including
Pelumi's, and including this file's own contents — directly. Do not soften critique to be agreeable.

---

## WHAT WE ARE BUILDING

**Product:** OneGoal Pro
**Tagline:** One goal. Full commitment. No excuses.
**Core idea:** Identity-based goal transformation. Not what to do — who to become.
**Live URL:** https://onegoalpro.app
**API URL:** https://api.onegoalpro.app
**GitHub:** https://github.com/pelumiolawole/onegoalclaude
**Legal entity:** One Goal Pro Ltd (UK), Company No. 17127527
**Stage:** MVP, live, in active daily use.

**Confirmed user/revenue state (last verified via Supabase, mid-2026 — RE-VERIFY before quoting a number in any external-facing context, e.g. investor conversations):**
- ~44–45 active registered users
- 1 paying subscriber on The Forge tier
- Retention is the core unsolved problem: most users complete 1–4 tasks in their first weeks and stop.
  A significant share (~12 users at last check) completed the interview and goal-setting flow and never
  completed a single task.
- Landing page claim of "100+ people have committed to one goal" does NOT match the confirmed user count.
  This is a live integrity risk sitting next to a public promise not to fake testimonials — fix the
  number or define what it's counting before anyone scrutinises it (press, investor, sharp user).
- 10 paying subscribers remains the milestone that unlocks a credible fundraising conversation (Zinc VC,
  Bethnal Green Ventures were identified as accelerator targets; BGV application status — CONFIRM, was
  flagged overdue as of mid-June).

---

## TECH STACK — PRODUCTION

| Layer | Technology | Provider | URL |
|---|---|---|---|
| Frontend | Next.js 15 (React 19) | Vercel | onegoalpro.app |
| Backend | FastAPI (Python) | Railway | api.onegoalpro.app |
| Database | Supabase (PostgreSQL + pgvector) | Supabase | project: one-goal-v2 (id: guqlwplztxxiseyenbye) |
| Cache | Redis | Railway | internal |
| AI | OpenAI (model per engine — see AI SYSTEMS) | OpenAI | Billing: auto-top-up + spend alert now configured (fixed after a June incident — see INCIDENT LOG) |
| Storage | Supabase Storage (avatars bucket) | Supabase | — |
| Auth | JWT + Google OAuth. Apple OAuth NOT built — planned for mobile sprint Week 2, sprint has not started. | Supabase Auth | — |
| Email | Resend (services/email.py) | Resend | Daily task email + re-engagement email — both rebuilt, see AI SYSTEMS |
| Payments | Stripe — live | Stripe | Confirm live webhook test has happened |
| Scheduler | APScheduler | Railway (in-process) | Runs nightly ~00:00–00:05 UTC per Sentry/Railway logs |
| Domain | Cloudflare Registrar | Cloudflare | — |
| Error tracking | Sentry | Sentry | Org: iic-a9. Backend project slug: onegoal-backend (project id 4510997306474496). Confirm frontend project separately — not yet verified in this file's lineage. |
| Analytics | PostHog | PostHog | Instrumented across 6 frontend files (interview completion, task completion, coach session start, upgrade modal views, subscription activation) — confirm still firing |
| Supabase MCP | — | Claude tool access | Project ID guqlwplztxxiseyenbye. Key fn: get_user_ai_context(id::uuid) — UUID cast required |
| Sentry MCP | — | Claude tool access | Org slug iic-a9. find_projects has intermittently failed with "No approval received" — if it fails again, use a direct issue URL from an alert email as a workaround, and treat repeated failures as a permission-scope issue worth investigating, not a one-off |
| GitHub MCP | — | Claude tool access | Direct git commit-history tool NOT reliably available as of this file's writing — raw file fetch via githubusercontent works but is rate-limited unauthenticated; do not assume commit history is inspectable without checking tool availability first |
| Canva MCP | — | Claude tool access | Brand kit ID kAHFT2qrrA8 (current). Manual template-and-duplicate preferred over AI generation for brand accuracy — AI generation doesn't reliably hit exact hex values |

---

## REPOSITORY STRUCTURE

```
onegoalclaude/
├── backend/
│   ├── ai/
│   │   ├── base.py
│   │   ├── engines/
│   │   │   ├── coach.py               # Coach PO — PMOS + psychological frameworks, session memory
│   │   │   ├── goal_decomposer.py
│   │   │   ├── interview.py           # Discovery interview engine V2
│   │   │   ├── profile_updater.py
│   │   │   ├── reflection_analyzer.py
│   │   │   └── task_generator.py      # Rewritten twice in 2026 — see AI SYSTEMS for current state
│   │   ├── memory/
│   │   │   ├── context_builder.py     # Patched to inject today_task — see AI SYSTEMS
│   │   │   └── retrieval.py           # pgvector semantic retrieval
│   │   ├── prompts/
│   │   │   └── system_prompts.py      # All AI prompts — centralised and versioned
│   │   └── utils/
│   │       ├── cost_tracker.py
│   │       └── safety_filter.py
│   ├── api/
│   │   ├── dependencies/auth.py
│   │   ├── routers/
│   │   │   ├── admin.py
│   │   │   ├── auth.py                # Google OAuth only. Apple OAuth NOT built — mobile sprint not started
│   │   │   ├── billing.py
│   │   │   ├── coach.py
│   │   │   ├── goals.py
│   │   │   ├── onboarding.py
│   │   │   ├── profile.py
│   │   │   ├── progress.py
│   │   │   ├── reflections.py
│   │   │   ├── settings.py
│   │   │   └── tasks.py
│   │   └── schemas/
│   │       ├── auth.py
│   │       └── core.py
│   ├── core/
│   │   ├── cache.py
│   │   ├── config.py                  # All env vars live here
│   │   ├── database.py
│   │   ├── email.py
│   │   ├── middleware.py
│   │   └── security.py
│   ├── db/models/
│   │   ├── __init__.py
│   │   ├── goal.py
│   │   ├── identity_profile.py
│   │   ├── task.py
│   │   └── user.py
│   ├── services/
│   │   ├── analytics.py
│   │   ├── billing.py                 # Dual-writes to users + subscriptions tables
│   │   ├── data_export.py
│   │   ├── email.py                   # send_daily_task_email, send_reengagement_email — both reworked
│   │   ├── scheduler.py
│   │   └── scoring.py
│   └── main.py
├── frontend/
│   ├── src/app/
│   │   ├── (app)/
│   │   │   ├── billing/cancel/
│   │   │   ├── billing/success/
│   │   │   ├── coach/
│   │   │   ├── dashboard/
│   │   │   ├── evolution/             # NEW — gamified identity progression page, shipped
│   │   │   ├── goal/
│   │   │   ├── progress/
│   │   │   └── settings/
│   │   │       ├── upgrade/           # lowercase
│   │   │       └── subscription/
│   │   ├── (auth)/
│   │   ├── (onboarding)/
│   │   ├── auth/callback/
│   │   ├── layout.tsx                 # Evolution added to nav with flame icon
│   │   └── page.tsx
│   ├── src/components/
│   │   └── reflection/ReflectionModal.tsx   # Loading spinners replaced with Newton's Cradle animation
│   ├── src/hooks/
│   ├── src/lib/
│   │   ├── api.ts                     # ALL backend calls go through here
│   │   ├── posthog.ts
│   │   └── utils.ts
│   └── src/stores/auth.ts
├── dead code/                         # Do not touch or import from here
│                                       # NOTE: ios/ and android/ do NOT exist yet — mobile sprint
│                                       # (Capacitor wrapper) has not started as of July 5, 2026.
│                                       # They will appear in Week 1 of that sprint when it begins.
├── docs/
│   ├── PRD_v2.md / PRD_v3.md / PRD_v3.1  # Confirm which is current — multiple versions exist
│   ├── agents/
│   │   ├── PM_AGENT.md
│   │   ├── MARKETING_AGENT.md
│   │   ├── QA_AGENT.md
│   │   └── SUPPORT_AGENT.md
│   └── commit_history.txt
├── CLAUDE.md                          # THIS FILE
└── TODO.md                            # Current sprint tasks — CHECK THIS EVERY SESSION, it moves fast
```

---

## WHAT IS FULLY BUILT AND WORKING

### Core user journey (end-to-end)
Landing page → Sign up / Login (email + Google OAuth, Apple OAuth in progress) → AI Discovery Interview
(V2) → Goal synthesis → Strategy preview → Activation (includes a 30+ character commitment-statement
gate — a structural fix, not cosmetic, after diagnosing that most early churn was lack-of-commitment
at entry rather than later disengagement) → Dashboard → Daily tasks → AI Coach (Coach PO) → Progress →
Evolution (identity progression page) → Settings → Upgrade → Stripe checkout → Billing success

### Backend systems (all live)
- JWT auth with token refresh; Google OAuth via Supabase; Apple OAuth (confirm shipped — mobile sprint)
- Email verification + password reset
- AI Interview Engine V2 (psychological funnel, 3 phases, never announced to user)
- Goal synthesis from interview
- Daily task generation (APScheduler, ~00:00 UTC nightly sweep + backlog catch-up, capped at 3/run)
- Coach PO (PMOS + psychological frameworks + session memory via pgvector), streaming, quota-enforced
- Transformation scoring system
- Traits timeline + weekly review generation
- Reflection submission + analysis
- Avatar upload (Supabase Storage)
- Invite/share flow
- GDPR data export + account deletion
- Admin endpoints + safety flag review
- Daily task email — subject line IS the identity_focus statement directly (e.g. "Today you are
  someone who shows up, even when it's hard."), no framing wrapper
- Re-engagement email — reworked to drop specific missed-task counts; leads with "Today's task is
  ready. Start with that one." Confirmed firing daily via Sentry logs; the open problem is NOT delivery,
  it's that users aren't returning even when the email lands (see RETENTION section)
- Push notification system — LIVE for web push. `push_subscriptions` table actively queried in
  production (confirmed via Sentry trace, July 2026). Native push (APNs/FCM) via
  `/push/native-subscribe` is a mobile-sprint deliverable and the **mobile sprint has not started as
  of July 5, 2026** — do not assume any native/Capacitor work exists. The `ios/` and `android/`
  folders referenced under REPOSITORY STRUCTURE do not exist yet; they are Week-1 sprint output, not
  current state. If a future session sees them, the sprint has begun — check TODO.md for date.
- Stripe billing — checkout, webhooks, cancel, resume, invoices, verify-session

### Frontend / product additions (2026, post-v1.1)
- Evolution page: five-chapter identity progression system (The Awakening → The Foundation →
  The Strengthening → The Embodiment → The Becoming), driven by days_active. Three tabs: Journey /
  Traits / Milestones. Pulls from existing `/progress/dashboard` and `/tasks/history/90` — no new
  backend endpoints. Cormorant Garamond typeface, dark-plus-amber brand identity.
- Newton's Cradle loading animation replacing generic spinners in ReflectionModal
- UI audit identified failure-framing throughout the dashboard/past-tasks UI (missed-task counts, red
  X icons, raw low percentages, visible zeros) as actively harmful to retention — a Claude Code brief
  was written covering 6 specific fixes (past-tasks graveyard removal, weekly review reframing,
  zero-state cleanup, coach markdown rendering, message chunking, paywall placement).
  **MERGED TO MAIN — PR #10, merge commit `03e10d7`.** All six fixes plus a `.gitignore` chore
  (tsbuildinfo artifact) are live. If Vercel deploys from main (confirm), this should be in production
  within ~2 minutes of merge. Commits: `3097ce1` (past-tasks filter), `ab2ccf1` (weekly
  review/week-grid/streak), `4c4cfdc` (goal-card zeros), `d9ceb33` (coach markdown strip + prompt
  NEVER-list line), `80672fb` (paywall moved to composer, −178 lines removing the old top banner),
  `83af966` (message chunking, 280-char threshold, 120ms stagger).
  **Not yet done: the manual verification pass on onegoalpro.app** — no red X rows in past tasks, no
  percentages on dashboard, no literal `**` in coach bubbles, quota line quiet at the composer. Do
  this before treating the audit as fully closed.

---

## AI SYSTEMS — CURRENT STATE (this section changes often, verify against system_prompts.py directly)

### Interview Engine V2
3-phase psychological funnel — phases never announced to user: find the tension → find the real goal
→ crystallise identity anchor. One question at a time, reflects before asking, uses the user's exact
words, ends with "I have a clear picture of who you are and where you want to go. Let's define your
One Goal."

### Coach PO (system prompt version V2)
PMOS framework (Forge / Field / Harbor / War Room domains) plus integrated coaching perspectives
(self-determination theory, stages of change, implementation intentions, ACT, adult development,
ontological coaching, polyvagal-informed nervous-system awareness) — never named to the user.
Session architecture: opening / exploration / closing. Coaching modes: guide / support / challenge /
celebrate / intervention / crisis, auto-selected from momentum, retention flags, and recent moments.

**Known fix applied:** `context_builder.py`'s `get_user_ai_context()` SQL function does NOT include
`today_task` — confirmed by direct inspection, the key is absent from the returned JSON entirely. This
caused the coach to have zero knowledge of the day's task and ask the user to describe it, destroying
the coaching experience. Fixed via a new `_enrich_with_today_task` method added directly in Python
after the SQL call, injected into `format_for_prompt` under a "TODAY'S TASK (know this before they say
a word)" section. CONFIRM this is deployed and working before assuming it — check for a session where
the coach opens with awareness of the task unprompted.

**Known issue — fix merged, verify live:** Coach responses have been observed rendering literal
markdown (`**bold**`, numbered lists) in the user-facing chat despite the system prompt's explicit
"never use bullet points, headers, or structured formatting" rule. A frontend `stripMarkdown()` at
render time plus an explicit NEVER-list line in the prompt were built and merged to main (commit
`d9ceb33`, part of PR #10 / merge `03e10d7`). Do a manual check on a live coach session to confirm —
this file being updated is not the same as someone having eyeballed production.

### Task Generator — rewritten in two confirmed stages (per commit log), current architecture:

**Stage 1 (commit d71e10d, May 8):** hardened task_type selection rules keyed to momentum/streak,
added the solo-executability gate (tasks must be startable alone within 5 minutes), added the
ALWAYS-FORBIDDEN task list with allowed solo alternatives for connection tasks, tightened the
non-repetition rule with core-verb/object matching over a 7-day window.

**Stage 2 (commits ba029d3, 607bdab, f0d1b4b — May 26–27, restated as a single undocumented commit
581504e on July 4):** dual-window history query, database-level exact-match duplicate detection,
semantic domain rotation with retry-on-duplicate. This stage was built specifically because Stage 1's
forbidden list — despite being live since May 8 — was still failing in production: a later Supabase
query (run in conversation, not itself a commit-log fact) found titles like "Host a Virtual Coffee
Chat" and "Reach Out to a Potential Mentor" had been generated multiple times AFTER Stage 1 shipped.
That query result is real and is the actual reason Stage 2 happened — but note precisely what's
commit-confirmed (the code changes, their dates) versus conversation-confirmed (the specific offending
titles that motivated them). Both are true; keep them as separate types of evidence rather than one
merged narrative, per the correction note at the top of this file.

Current architecture, combining both stages:
- **Dual-window history query** (`_get_task_history`): merges last-30-days-by-scheduled-date with
  last-14-by-creation-time, deduplicated by title. Fixes the original bug where users with large
  pending backlogs showed the AI stale/misleading history, causing undetected repetition.
- **Exact-match duplicate check** (`_is_title_duplicate`): checks against the last 14 days only, exact
  string match. A fuzzy 70%-overlap version was tried and REMOVED — it was too aggressive and caused
  valid AI output to be rejected and replaced with the fallback template far too often.
- **Domain field + code-level rotation check**: the AI now outputs a `domain` field (e.g.
  "customer-understanding", "execution", "discipline") stored in `generation_context`. Before
  generating, code reads the last 5 stored domains; if 3+ share a domain, a DOMAIN OVERRIDE line
  naming the saturated domain is appended to the prompt, and a retry returning the same domain is
  rejected. This closes a real gap: the prompt previously asked the model to self-police domain
  rotation with no verification, and the database showed 7 consecutive same-domain tasks for at least
  one user after that prompt shipped.
- **Forbidden-pattern regex check** (`_violates_forbidden_patterns`), checked in code before persist —
  catches "reach out", "attend", "join a/an", "host", "facilitate", "schedule a", "interview
  (a/an/your/someone)", "conduct...interview", "connect with a", "find a community/group/mentor",
  "webinar", "networking event". This was added because the prompt's own forbidden-task list was
  failing in production: "Host a Virtual Coffee Chat" generated 10 times, "Reach Out to a Potential
  Mentor" 9 times, "Attend a Local Networking Event" 5 times, all despite being explicitly banned in
  the prompt text. Code-level enforcement was necessary because prompt-level bans alone were not
  working — expect this pattern (ask the model, then verify in code) to recur; it is the actual lesson
  from this rewrite, not just a task-generator detail.
- **Verb constraint** (prompt-level): completion data across the user base showed document-producing
  verbs (Draft, Write, Create, Outline, Prepare, List, Analyze) complete under 5% of the time, while
  concrete real-world verbs (Host, Develop, Join, Connect, Sketch) complete 12–27% of the time. The
  prompt now forbids a document-producing verb as a task's primary action unless the artifact is used
  the same day for something external (sent, published, spoken, posted) — "Draft a vision" is banned,
  "write and send one message to X" is allowed.
- **Completion-pattern injection** (`_get_completion_pattern`): a per-user line computed from their own
  history and injected into every generation prompt — which verbs this specific user completes vs has
  never completed. This is new; it had not been validated against a live cohort as of this file's
  writing. Watch for it either sharpening task relevance or, if the per-user sample is too small,
  producing noisy/unhelpful signal — check actual completion rates for users who've had 10+ tasks
  generated since this shipped.
- **Retry-with-named-reason on validation failure**: one retry, with the specific rejection reason
  (forbidden pattern matched / duplicate / domain saturation) explicitly stated in the retry prompt.
  Falls back to a template task (`FALLBACK_TASKS`, 3 rotating options) only if the retry also fails
  validation or the AI call errors.
- **Known residual gap, observed in Sentry**: for goal domains that are inherently social (e.g.
  cybersecurity/networking-adjacent goals), the AI's first AND retry attempts have both been
  observed hitting the forbidden-pattern check ("Reach out to a Cybersecurity Peer" → retry → "Join an
  Online Cybersecurity Forum" → both rejected → fallback template used). This suggests the prompt
  doesn't yet give the model good non-social task material for technical/security domains — worth a
  domain-specific example set rather than another regex tweak. NOT YET FIXED as of last check.

### Reflection Analyzer
Scores depth 1–10, detects sentiment/resistance/breakthrough, extracts trait evidence, feeds
`tomorrow_signal` back into task generation via progress context.

---

## RETENTION — THE ACTUAL UNSOLVED PROBLEM (do not let engineering polish substitute for this)

As of last full audit: the large majority of active users have 40–90 missed tasks each. Roughly a
dozen users completed the interview and never completed a single task. Only a handful of users
(under 5) have completed more than 10 tasks total. The activation re-engagement email fires once per
user (throttled by `activation_reengagement_sent_at`) and is not repeated — this throttle is correct
behaviour, not a bug, but it means one email is the entire intervention for someone who never
activated.

Three distinct failure modes exist and likely need different fixes:
1. **Never activated** — completed onboarding, zero tasks ever. Re-engagement email fired once, no
   further intervention exists.
2. **Activated once, then stopped** — 1–4 tasks completed then silence. Task repetition/quality was
   the leading hypothesis here; the task generator rewrites target this directly but have not yet been
   validated against actual completion-rate improvement for this cohort (validation was repeatedly
   blocked by an OpenAI billing outage — see INCIDENT LOG — so before assuming the fixes worked,
   check post-fix completion rates specifically for previously-churned users).
3. **Active but inconsistent** — the small group of engaged users, still below the consistency needed
   for the product's own retention math to work.

**Do not treat "we improved the task generator" as "we solved retention."** It's a necessary condition,
not sufficient. If completion rates for cohort 2 haven't moved after the rewrites had time to run, the
next hypothesis to test is the UI failure-framing problem (see UI audit) or a second re-engagement
touchpoint for never-activated users, not a third task-generator iteration.

---

## INCIDENT LOG (keep this section, it prevents repeat mistakes)

- **June 2026 — OpenAI quota outage.** `insufficient_quota` (HTTP 429, billing wall, NOT a rate limit)
  took the product down for AI generation — coach, task generator, reflection analyzer all failed
  silently overnight, all users got fallback template tasks. Root cause: no spend alert, account hit
  its limit. Fix: OpenAI spend alert + auto top-up now configured (per Pelumi, July 2026) — if this
  recurs, the alert/auto-top-up config itself needs checking, not just re-topping-up manually.
- **Recurring — stale CLAUDE.md pasted into live sessions.** The v1.1 file (dated March 25) was pasted
  into at least three separate chats in this project through June and July while claiming figures and
  build-status that were months out of date. This is the reason this file has an explicit warning at
  the top. If you are an instance of Claude reading a version of this file that itself looks stale,
  say so immediately rather than proceeding on it.
- **Sentry MCP `find_projects` — intermittent tool failure.** Returned "No approval received" with no
  further diagnostic info on at least one occasion. Root cause not yet isolated (scope vs. no-project
  vs. client rendering issue). Workaround used: direct issue URL from a Sentry alert email, via
  `get_sentry_resource(url=...)`, worked when `find_projects` did not. If this recurs, worth isolating
  properly rather than working around it again.

---

## ENGINEERING RULES — NEVER VIOLATE THESE

1. **Supabase Storage** — always use `supabase-py` client, never raw `httpx` calls
2. **asyncpg vector syntax** — never use `:param::vector`. Always inline in f-strings or use `CAST(:param AS vector)`
3. **asyncpg type casts** — avoid `::jsonb`, `::text[]` with named params. Use `CAST()` syntax
4. **FastAPI route ordering** — named routes MUST be defined BEFORE catch-all routes (`/{date}`)
5. **Streak updates** — always update immediately on user action, never defer to scheduler
6. **Task queries** — never filter on specific `task_type` values unless deliberately excluding
7. **JSON serialisation** — always `json.dumps()`, never `str()` on structured data
8. **Environment variables** — never hardcode. All config lives in `backend/core/config.py`
9. **File delivery** — always deliver complete files. Pelumi deploys by replacing whole files
10. **No partial diffs** unless the change is a single clearly-identified line
11. **Billing dual-write** — webhook handlers must write to BOTH `users` AND `subscriptions` tables
12. **Frontend routing** — all Next.js folder names must be lowercase (Vercel is case-sensitive on Linux)
13. **Deployment discipline** — never add an import before the file exists in the repo; commit the file
    and the import in the same commit (learned from a production build failure)
14. **AsyncIO scheduler** — never use `asyncio.create_task()` inside lambdas in APScheduler jobs; pass
    coroutines directly to `AsyncIOScheduler`
15. **Ask, then verify in code** — a rule discovered through the task-generator rewrites, worth stating
    generally: if an AI prompt asks the model to self-police something (don't repeat X, don't generate
    Y), assume it will fail silently in production unless there is also a deterministic code-level
    check. This applies beyond the task generator — apply it to any future prompt-based constraint.
16. **Never fabricate social proof** — flagged as the single highest credibility risk before any public
    launch push. No invented testimonials, no unverifiable user-count claims.
17. **Security — IP blocking on credential-scan patterns is live** (commits add44a8, 12cb9a7, late
    April): repeated 404s from one IP (credential-stuffing/scan behaviour) trigger a block. If
    debugging unexpected 403s/blocks for a legitimate user or test account, check this middleware
    before assuming it's unrelated.

---

## DEPLOYMENT PROCEDURE

### Backend (Railway)
```bash
git add -A
git commit -m "your message"
git push origin main
# Railway auto-deploys ~10–15 min. Monitor: Railway → Deployments → View logs
```

### Frontend (Vercel)
```bash
# Same git push — Vercel auto-deploys ~2 min
```

### Environment variables
- Backend: Railway → Service → Variables
- Frontend: Vercel → Project → Settings → Environment Variables
- Never commit `.env` files

---

## MONETISATION TIERS

| Tier | Name | Monthly | Annual | Coach quota |
|---|---|---|---|---|
| Free | The Spark | $0 | — | 5 messages/day |
| Pro | The Forge | $4.99 | $47.88 | Unlimited |
| Elite | The Identity | $10.99 | $107.88 | Unlimited + re-interview |

**Open strategic question, flagged not resolved:** a Paul-Graham-style pressure test of the £4.99
price point raised the possibility that it signals insufficient confidence in the product's own value.
This has not been acted on — noting it here so it isn't lost, not because a decision has been made.

---

## DATABASE — KEY TABLES (not exhaustive — extensive AI/analytics schema exists beyond this list)

### Core
- `users` — subscription_plan, stripe_customer_id, stripe_subscription_id
- `goals` — refined_statement, required_identity, status (including `approaching_completion`)
- `identity_profiles` — transformation_score, streak, days_active, commitment_statement
- `daily_tasks` — task_type: becoming / identity_anchor / micro_action / challenge; `generation_context`
  JSONB column now stores `domain`, `momentum_state`, `streak`, `is_fallback` at generation time
- `objectives`, `identity_traits`
- `reflections` — questions_answers JSONB, depth_score
- `coach_sessions`, `coach_moments`, `coach_patterns`, `coach_interventions`, `coach_safety_flags`
- `onboarding_interview_state` — messages JSONB (raw interview excerpts pulled from here)

### Billing
- `subscriptions` — unique constraint on user_id
- `invoices`

### Notifications
- `notification_queue`
- `push_subscriptions` — endpoint, p256dh, auth tokens — CONFIRMED actively queried in production

### Key SQL function
- `get_user_ai_context(id::uuid)` — UUID cast required. Does NOT include `today_task` (see AI SYSTEMS
  fix above) — this is patched at the Python layer, not in the SQL function itself. If this function
  is ever modified directly, re-check whether the Python-layer patch is still needed or now redundant.

---

## SESSION OPERATING PROCEDURE

**Start of every session:**
1. Read this file completely — and flag anything that looks stale rather than assuming it's current
2. Read `TODO.md` for current sprint focus
3. Ask "What are we working on today?" if TODO is ambiguous
4. Do not start coding until the task is clear

**During session:**
- Apply the mentor operating mode from the top of this file — always, not just when asked
- Plain English explanation before code
- Complete files only — no partial diffs
- Check asyncpg gotchas, route ordering, type casts before delivering
- If a prompt-based fix is proposed for anything the AI must "remember not to do," ask whether a
  code-level check is also needed (see Engineering Rule 15)
- Update `TODO.md` after each completed task

**Debugging order:** Railway logs → Sentry → Supabase queries → manual logic trace → fix root cause

**Updating this file:** when a session produces a material change to product state (a rewrite, a
fix, a metric, an incident), update this file in the same session, not "later." A stale version of
this file has already cost repeated wasted context in this project — do not let it happen again.

**Commit message discipline:** commit 581504e (July 4, "task logic update," no body) is an example of
what NOT to do going forward. A commit message with no specifics is only interpretable if you already
know what changed — which defeats the purpose of a log. Write commit messages (or at least bodies)
assuming the reader has no other context, the same standard this file is held to.

---

## AI AGENTS ROSTER

All agent files live in `docs/agents/`. To use: open new Claude conversation, paste agent file contents, give task.

| Agent | Trigger | File |
|---|---|---|
| PM Agent | "Ask the PM agent" | docs/agents/PM_AGENT.md |
| Marketing Agent | "Ask the marketing agent" | docs/agents/MARKETING_AGENT.md |
| QA Agent | "Ask the QA agent" | docs/agents/QA_AGENT.md |
| Support Agent | "Ask the support agent" | docs/agents/SUPPORT_AGENT.md |

---

## OTHER PELUMI BRANDS

**IIC Networks** — Influence, Impact, Change. Coaching, speaking, leadership.
Voice: Authoritative, practical, faith-informed, African professional context.

**Author Brand (@PelumiOlawole)** — Book: *Petty Little Things*.
Voice: Conversational, honest, sometimes sharp, always constructive.
Platform: LinkedIn + Instagram.

---

## HOW TO UPDATE THIS FILE

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — [what changed]"
git push origin main
```
Then paste updated contents into this Claude Project's custom instructions.

**Do this the same day something material changes.** Do not let this file drift again.

---

*This file is the single source of truth for all Claude sessions on OneGoal Pro — but it is only
as good as its last honest update. If it contradicts what you can directly observe (Sentry, Supabase,
the live product), the observation wins, and you should say so.*
