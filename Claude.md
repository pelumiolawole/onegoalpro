OneGoal Pro — Master Claude Skill File
Version: 2.2 | Last updated: July 12, 2026
READ THIS ENTIRE FILE BEFORE DOING ANYTHING ELSE IN THIS SESSION

CHANGE NOTE 1: v1.1 (March 25, 2026) was stale — pasted into FOUR separate
sessions in June/July while claiming 11 users, £3.74 MRR, and "push
notifications not built" against a production system that had ~45 users,
a live push system, and two full task-generator rewrites. If you are
reading this in a future session and something here looks wrong or
outdated, SAY SO — do not silently defer to this file. Confirm current
state with Pelumi before proceeding on anything load-bearing.

CHANGE NOTE 2: v2.0 of this file contained a fabrication, corrected in v2.1.
v2.0 claimed the task-generator's forbidden-pattern/domain-rotation code
was added in response to specific production titles ("Host a Virtual
Coffee Chat" x10 etc.). The actual commit log (checked directly, July 5)
shows the forbidden list was first added May 8 (commit d71e10d), and the
database evidence of those specific titles slipping through was pulled in
a LATER conversation, on a different day. The two facts are real but the
causal story connecting them was invented — a tidier narrative than what
actually happened. Standing reminder: when reconstructing history,
distinguish "confirmed by commit log," "confirmed by direct DB/log
query," and "inferred/plausible" — do not silently merge them into one
clean timeline.

CHANGE NOTE 3 (July 12, 2026): v2.1's confirmed user/revenue numbers were
themselves imprecise ("~44–45 active registered users") and the landing
page's "100+ people have committed to one goal" claim was flagged but
unresolved. Both are now fixed. A direct Supabase query (July 12) gives
exact figures: 99 total registered users, 49 with an active goal, 3 who
have passed the actual commitment gate (30+ character commitment
statement). The landing page claim has been corrected to match reality —
see LANDING PAGE / MARKETING INTEGRITY below. Do not round these numbers
up in future conversations without re-querying; "99" and "49" are exact
as of July 12, not estimates.

STANDING INSTRUCTION — applies to every chat in this project, not just
when invoked: "Act as a rigorous, honest mentor. Do not default to
agreement. Identify weaknesses, blind spots, and flawed assumptions.
Challenge ideas when needed. Be direct and clear, not harsh. Prioritize
helping me improve over being agreeable. When you critique something,
explain why and suggest a better alternative." This includes challenging
THIS FILE if a future session finds it wrong, incomplete, or stale.

WHO YOU ARE WORKING WITH
Name: Pelumi Olawole
Role: Founder, IIC Networks (Influence, Impact, Change) | Author | Coach | Day job: E.ON Next (UK)
Book: Petty Little Things: 50 Habits Quietly Ruining Your Life and How to Fix Them
Working environment: Windows, VS Code, Git Bash / PowerShell. Mac mini (M4, 16GB, 512GB) acquired for iOS builds — mobile sprint.
Skill level: Rebuilding development skills — needs explicit step-by-step terminal instructions.
Note: multi-line commit messages with embedded quotes break in PowerShell
(it doesn't parse them like bash). Use `git commit -F message.txt` for any
commit message with more than one line or a quoted word inside it.
Deployment workflow: Local edits → push to GitHub → auto-deploy (Railway ~10–15 min, Vercel ~2 min)
Testing: Primarily on mobile. No browser DevTools available. Railway logs are primary debug tool.
File delivery preference: Complete corrected files ready to copy-paste. No partial diffs unless trivial.
Communication preference: Plain English explanation of what's wrong BEFORE any code.
Operating mode: see the standing instruction at the very top of this file. It applies to every
message in this project, not just when explicitly invoked. Flag weak assumptions — including
Pelumi's, and including this file's own contents — directly. Do not soften critique to be agreeable.

WHAT WE ARE BUILDING
Product: OneGoal Pro
Tagline: One goal. Full commitment. No excuses.
Core idea: Identity-based goal transformation. Not what to do — who to become.
Live URL: https://onegoalpro.app
API URL: https://api.onegoalpro.app
GitHub: https://github.com/pelumiolawole/onegoalpro
Legal entity: One Goal Pro Ltd (UK), Company No. 17127527
Stage: MVP, live, in active daily use.

Confirmed user/revenue state (verified via direct Supabase query, July 12, 2026 —
RE-QUERY before quoting any number in an external-facing context, e.g. investor
conversations; these are exact counts, not estimates, but they move daily):

99 total registered users
49 users have set an active goal (i.e. completed onboarding through goal synthesis)
3 users have passed the actual commitment gate (30+ character commitment statement)
1 paying subscriber on The Forge tier
Retention is the core unsolved problem: most users complete 1–4 tasks in their first weeks and stop.
A significant share completed the interview and goal-setting flow and never completed a single task.
10 paying subscribers remains the milestone that unlocks a credible fundraising conversation (Zinc VC,
Bethnal Green Ventures were identified as accelerator targets; BGV application status — STILL
UNCONFIRMED, flagged overdue since mid-June, ask directly, do not assume).

LANDING PAGE / MARKETING INTEGRITY
Fixed July 12, 2026. The landing page previously claimed "100+ people have committed to
one goal" — this matched none of the three real readings of the data (99 registered, 49
with a goal, 3 past the commitment gate) and sat directly next to the product's own stated
rule against fabricating social proof. Corrected to: "99 people have started their
transformation. And counting." — an exact, non-rounded, verifiable number paired with an
accurate verb ("started," not "committed," since "committed" specifically overclaims
against the 3-user commitment-gate figure). This number is now hardcoded text in
frontend/src/app/page.tsx and will drift stale exactly like every other unmonitored number
in this file has. Re-verify it periodically, or better: wire it to a live query instead of
hardcoded text next time this page is touched. Never restore "100+" or any number that
hasn't been freshly queried against Supabase.


TECH STACK — PRODUCTION
LayerTechnologyProviderURLFrontendNext.js 15 (React 19)Vercelonegoalpro.appBackendFastAPI (Python)Railwayapi.onegoalpro.appDatabaseSupabase (PostgreSQL + pgvector)Supabaseproject: one-goal-v2 (id: guqlwplztxxiseyenbye)CacheRedisRailwayinternalAIOpenAI (model per engine — see AI SYSTEMS)OpenAIBilling: auto-top-up + spend alert now configured (fixed after a June incident — see INCIDENT LOG)StorageSupabase Storage (avatars bucket)Supabase—AuthJWT + Google OAuth. Apple OAuth NOT built — planned for mobile sprint Week 2, sprint has not started.Supabase Auth—EmailResend (services/email.py)ResendDaily task email + re-engagement email — both rebuilt, see AI SYSTEMSPaymentsStripe — liveStripeConfirm live webhook test has happenedSchedulerAPSchedulerRailway (in-process)Runs nightly ~00:00–00:05 UTC per Sentry/Railway logs, fifteen cron jobs total (task generation, sweep, scoring, weekly review/digest, goal-completion check, interventions, behavioural snapshots, data purge, verification reminders, two re-engagement jobs, daily push, 24h/72h interview nudges)DomainCloudflare RegistrarCloudflare—Error trackingSentrySentryOrg: iic-a9. Backend project slug: onegoal-backend (project id 4510997306474496). Confirm frontend project separately — not yet verified in this file's lineage.AnalyticsPostHogPostHogInstrumented across 6 frontend files (interview completion, task completion, coach session start, upgrade modal views, subscription activation) — confirm still firingSupabase MCP—Claude tool accessProject ID guqlwplztxxiseyenbye. Key fn: get_user_ai_context(id::uuid) — UUID cast required. execute_sql confirmed reliable for direct verification queries (used July 12 to get exact user/goal/commitment counts).Sentry MCP—Claude tool accessOrg slug iic-a9. search_issues, get_sentry_resource, and search_sentry_tools all confirmed working July 12. analyze_issue_with_seer (Autofix) returned HTTP 402 "No budget for Seer Autofix" on July 12 — that feature needs billing attention if you want to use it again; do not assume it works without checking first.GitHub MCP—Not available as an in-chat toolNo GitHub MCP tool is loaded in standard Claude Projects sessions. The repo IS accessible via `git clone` inside the bash/computer-use tool when that tool is available in the session — confirmed working July 12 (cloned github.com/pelumiolawole/onegoalpro, read the full backend and frontend tree directly). If bash/computer-use is not available in a given session, direct repo reading is not possible and Pelumi needs to paste file contents.Canva MCP—Claude tool accessBrand kit ID kAHFT2qrrA8 (current). Manual template-and-duplicate preferred over AI generation for brand accuracy — AI generation doesn't reliably hit exact hex values

REPOSITORY STRUCTURE
onegoalpro/
├── backend/
│   ├── ai/
│   │   ├── base.py
│   │   ├── engines/
│   │   │   ├── coach.py               # Coach PO — PMOS + psychological frameworks, session memory
│   │   │   ├── goal_decomposer.py
│   │   │   ├── interview.py           # Discovery interview engine V2
│   │   │   ├── profile_updater.py
│   │   │   ├── reflection_analyzer.py
│   │   │   └── task_generator.py      # Rewritten twice, patched three times in 2026 — see AI SYSTEMS for current state
│   │   ├── memory/
│   │   │   ├── context_builder.py     # Patched to inject today_task — see AI SYSTEMS
│   │   │   └── retrieval.py           # pgvector semantic retrieval
│   │   ├── prompts/
│   │   │   └── system_prompts.py      # All AI prompts — centralised and versioned. task_generator now V2 (current), V1 retained for rollback.
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
│   │   │   ├── push.py                # Web push subscribe/unsubscribe
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
│   │   ├── middleware.py              # Also carries IP-blocking defence against credential-scan patterns
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
│   │   ├── email.py                   # send_daily_task_email, send_reengagement_email
│   │   ├── push.py                    # FIXED July 12 — see INCIDENT LOG. Web push send + 410/404 expiry detection.
│   │   ├── scheduler.py               # FIXED July 12 — interview-nudge job now actually cleans up expired push subs
│   │   └── scoring.py
│   └── main.py
├── frontend/
│   ├── src/app/
│   │   ├── (app)/
│   │   │   ├── billing/cancel/
│   │   │   ├── billing/success/
│   │   │   ├── coach/
│   │   │   ├── dashboard/
│   │   │   ├── evolution/             # FIXED July 12 — "Today" date mislabel, see INCIDENT LOG
│   │   │   ├── goal/
│   │   │   ├── progress/
│   │   │   └── settings/
│   │   │       ├── upgrade/           # lowercase
│   │   │       └── subscription/
│   │   ├── (auth)/
│   │   ├── (onboarding)/
│   │   ├── auth/callback/
│   │   ├── layout.tsx                 # Evolution added to nav with flame icon
│   │   └── page.tsx                   # Landing page. Social-proof stat FIXED July 12 — see LANDING PAGE / MARKETING INTEGRITY
│   ├── src/components/
│   │   └── reflection/ReflectionModal.tsx   # Loading spinners replaced with Newton's Cradle animation
│   ├── src/hooks/
│   ├── src/lib/
│   │   ├── api.ts                     # ALL backend calls go through here
│   │   ├── posthog.ts
│   │   └── utils.ts
│   ├── src/stores/auth.ts
│   └── public/
│       └── robots.txt                 # FIXED July 12 — was misnamed robot.txt (singular), search engines were ignoring it entirely
├── dead code/                         # Do not touch or import from here
│                                       # NOTE: ios/ and android/ do NOT exist yet — mobile sprint
│                                       # (Capacitor wrapper) has not started as of July 12, 2026.
│                                       # They will appear in Week 1 of that sprint when it begins.
├── docs/
│   ├── commit_history_full.txt / commit_history_v1.txt / file_tree.txt
│   └── agents/
│       ├── PM_AGENT.md
│       ├── MARKETING_AGENT.md
│       ├── QA_AGENT.md
│       └── SUPPORT_AGENT.md
├── CLAUDE.md                          # THIS FILE
└── TODO.md                            # Current sprint tasks — CHECK THIS EVERY SESSION, it moves fast

WHAT IS FULLY BUILT AND WORKING
Core user journey (end-to-end)
Landing page → Sign up / Login (email + Google OAuth, Apple OAuth in progress) → AI Discovery Interview
(V2) → Goal synthesis → Strategy preview → Activation (includes a 30+ character commitment-statement
gate — a structural fix, not cosmetic, after diagnosing that most early churn was lack-of-commitment
at entry rather than later disengagement; confirmed July 12 that only 3 of 99 registered users have
actually passed this gate, so activation remains the single biggest drop-off point in the funnel) →
Dashboard → Daily tasks → AI Coach (Coach PO) → Progress → Evolution (identity progression page) →
Settings → Upgrade → Stripe checkout → Billing success

Backend systems (all live)

JWT auth with token refresh; Google OAuth via Supabase; Apple OAuth (confirm shipped — mobile sprint)
Email verification + password reset
AI Interview Engine V2 (psychological funnel, 3 phases, never announced to user)
Goal synthesis from interview
Daily task generation (APScheduler, ~00:00 UTC nightly sweep + backlog catch-up, capped at 3/run) —
see AI SYSTEMS, task generator now on prompt V2 with reason-coded retry guidance (July 12)
Coach PO (PMOS + psychological frameworks + session memory via pgvector), streaming, quota-enforced
Transformation scoring system
Traits timeline + weekly review generation
Reflection submission + analysis
Avatar upload (Supabase Storage)
Invite/share flow
GDPR data export + account deletion
Admin endpoints + safety flag review
Daily task email — subject line IS the identity_focus statement directly, no framing wrapper
Re-engagement email — reworked to drop specific missed-task counts; leads with "Today's task is
ready. Start with that one." Confirmed firing daily via Sentry logs; the open problem is NOT delivery,
it's that users aren't returning even when the email lands (see RETENTION section)
Push notification system — LIVE for web push, and as of July 12 the 410/404 expiry-detection bug is
FIXED (see INCIDENT LOG). Native push (APNs/FCM) via /push/native-subscribe is a mobile-sprint
deliverable and the mobile sprint has not started. The ios/ and android/ folders referenced under
REPOSITORY STRUCTURE do not exist yet.
Stripe billing — checkout, webhooks, cancel, resume, invoices, verify-session

Frontend / product additions (2026, post-v1.1)

Evolution page: five-chapter identity progression system (The Awakening → The Foundation →
The Strengthening → The Embodiment → The Becoming), driven by days_active. Three tabs: Journey /
Traits / Milestones. Pulls from existing /progress/dashboard and /tasks/history/90 — no new
backend endpoints. Cormorant Garamond typeface, dark-plus-amber brand identity. "Today" date
mislabel bug FIXED July 12 — see INCIDENT LOG.
Newton's Cradle loading animation replacing generic spinners in ReflectionModal
UI audit (six fixes: past-tasks graveyard removal, weekly review reframing, zero-state cleanup,
coach markdown rendering, message chunking, paywall placement) — MERGED TO MAIN (PR #10, commit
03e10d7) AND manually verified live on onegoalpro.app as of July 2026. This item is closed; do not
re-open without new evidence of regression.


AI SYSTEMS — CURRENT STATE (this section changes often, verify against system_prompts.py directly)
Interview Engine V2
3-phase psychological funnel — phases never announced to user: find the tension → find the real goal
→ crystallise identity anchor. One question at a time, reflects before asking, uses the user's exact
words, ends with "I have a clear picture of who you are and where you want to go. Let's define your
One Goal."
Coach PO (system prompt version V2)
PMOS framework (Forge / Field / Harbor / War Room domains) plus integrated coaching perspectives
(self-determination theory, stages of change, implementation intentions, ACT, adult development,
ontological coaching, polyvagal-informed nervous-system awareness) — never named to the user.
Session architecture: opening / exploration / closing. Coaching modes: guide / support / challenge /
celebrate / intervention / crisis, auto-selected from momentum, retention flags, and recent moments.
Known fix, deployed and stable: context_builder.py's get_user_ai_context() SQL function does NOT
include today_task. Fixed via a new _enrich_with_today_task method added directly in Python after the
SQL call. If the underlying SQL function is ever changed, this patch needs re-checking.
Task Generator — rewritten twice, then patched three further times in July 2026. Current architecture
(prompt V2, code current as of July 12):

STAGE 1 (May 8, commit d71e10d): hardened task_type selection rules, solo-executability gate,
ALWAYS-FORBIDDEN task list, non-repetition rule via core-verb/object matching.
STAGE 2 (May 26–27): dual-window history query, database-level exact-match duplicate detection,
semantic domain rotation with retry-on-duplicate.
STAGE 3 (July 5): fixed a confirmed production bug where the AI's "domain" field was silently
written as null when the model omitted it, breaking rotation with no error. Missing domain is now
itself a validation failure. Verified via direct Supabase query July 12: domain population went
from 0/46 tasks (July 2–4) to 46/46 tasks every day since July 5. Holding, not regressed.
STAGE 4 (July 12, prompt V2 + reason-coded retries): Sentry showed 14 double-failures (first
attempt AND retry both rejected) across July 5–11 — 8 forbidden-pattern, 3 domain-saturation (all
one user, stuck on the non-canonical domain name "community engagement" for three consecutive
days), 3 duplicate-title. Root cause: retries only named the violation ("generate something
different") without giving the model concrete alternative material, so it kept re-sampling from
the same failed pool. Fixed with four changes: (1) a canonical domain vocabulary shared between
prompt and code, so saturation retries can name specific alternative domains instead of "pick a
different one"; (2) a solo-task-shape library injected into forbidden-pattern retries, including
technical/security-field material, reframing social goals around "what you build/publish alone
that makes you worth connecting with" rather than banning coordination verbs with nothing to
replace them; (3) retry temperature lowered from 0.95 to 0.8 (the failure mode is non-compliance,
not lack of creativity — raising temperature was backwards); (4) each of the three FALLBACK_TASKS
templates now carries an explicit domain, so a user stuck in repeated fallbacks doesn't stay
permanently "stuck" in saturation because their fallback tasks carried no domain signal.
STAGE 5 (July 12, same day, found via post-deploy verification): the duplicate-title retry path
was left with the old vague "be different" guidance from Stage 2, and it recurred in production
the very first day post-Stage-4-deploy — a retry reproduced the exact same title verbatim.
Diagnosis: Stage 4's lower retry temperature (0.8) improves compliance when paired with concrete
material, but can backfire into MORE repetition when the guidance is vague, which is exactly what
the duplicate path still was. Fixed to match the treatment given to forbidden-pattern and
saturation: the retry now receives the rejected title's primary verb (explicitly forbidden), a
short list of approved alternative verbs pulled from the prompt's own VERB CONSTRAINT, and the
user's actual last five task titles named explicitly, rather than relying on the model to re-scan
the full task-history block already in the system prompt.
POST-DEPLOY VERIFICATION (July 12, done same day as Stage 4/5): pre-fix week (July 5–11) had 14
double-failures. Post-fix (July 12 partial day) had 1, and it was the exact failure mode Stage 5
then fixed within hours. One day is not enough data to declare victory on Stage 4's specific
targets (forbidden-pattern, saturation) — re-run this check a few days out. Query pattern:
compare Sentry issues matching "ai_task_generation_failed" / "Retry also failed validation"
before and after July 12, and cross-check daily_tasks.generation_context->>'is_fallback' rate.
KNOWN OBSERVABILITY GAP (not yet fixed): generation_context for fallback tasks created via the
main nightly path (generate_task_for_user's except block) does not write a "reason" key — only
the backlog path (_create_fallback_task) does. You can currently only learn WHY a given fallback
happened by cross-referencing Sentry, not from the database alone. Minor, not urgent, worth fixing
if fallback-rate analysis becomes a regular activity.
KNOWN RESIDUAL GAP, PARTIALLY ADDRESSED: for goal domains that are inherently social (community,
networking, security/tech fields with strong community culture), first-attempt AND retry
forbidden-pattern double-failures were observed repeatedly before July 12. The Stage 4 fix targets
this directly (solo-task library, reframe language, technical/security-specific shapes). Watch
Sentry for recurrence in these specific domains before considering this fully closed.

Reflection Analyzer
Scores depth 1–10, detects sentiment/resistance/breakthrough, extracts trait evidence, feeds
tomorrow_signal back into task generation via progress context.

RETENTION — THE ACTUAL UNSOLVED PROBLEM (do not let engineering polish substitute for this)
As of last full audit: the large majority of active users have significant missed-task counts.
Only 3 of 99 registered users have passed the actual commitment gate (verified July 12) — this is a
sharper and more concerning number than "~44-45 active users" suggested, and reframes where the
biggest leak in the funnel actually is: entry/commitment, not later-stage task quality. The
activation re-engagement email fires once per user (throttled by activation_reengagement_sent_at)
and is not repeated — correct behaviour, not a bug, but it means one email is the entire
intervention for someone who never activated.

Three distinct failure modes exist and likely need different fixes:

Never activated — completed onboarding, zero tasks ever. Re-engagement email fired once, no
further intervention exists. Given only 3/99 pass the commitment gate, THIS is probably the
largest lever in the entire product right now, larger than task-generator quality.
Activated once, then stopped — 1–4 tasks completed then silence. Task repetition/quality was
the leading hypothesis here; the task generator rewrites (see AI SYSTEMS, Stages 3-5) target this
directly. Post-fix completion-rate validation for this specific cohort is still outstanding —
check actual completion rates for previously-churned users a few days after Stage 4/5, not just
whether generation failures dropped.
Active but inconsistent — the small group of engaged users, still below the consistency needed
for the product's own retention math to work.

Do not treat "we improved the task generator" as "we solved retention." It's a necessary condition,
not sufficient — and as of July 12 the sharper diagnosis is that the commitment gate (3/99) is the
biggest unsolved leak, ahead of task quality.

INCIDENT LOG (keep this section, it prevents repeat mistakes)

June 2026 — OpenAI quota outage. insufficient_quota (HTTP 429, billing wall, NOT a rate limit)
took the product down for AI generation overnight, all users got fallback template tasks. Fix:
OpenAI spend alert + auto top-up now configured — if this recurs, check the alert/auto-top-up
config itself, not just re-topping-up manually.
Recurring — stale CLAUDE.md pasted into live sessions. The v1.1 file was pasted into at least
four separate chats through June and July while claiming figures and build-status months out of
date. v2.1 was confirmed pasted into this project's Custom Instructions field July 5; a fresh chat
should now load it automatically without manual pasting. If a future session still sees stale
content pasted as literal text, say so immediately and do not treat it as ground truth.
Sentry MCP find_projects — intermittent tool failure, historically. As of July 12, search_issues,
get_sentry_resource, and search_sentry_tools all confirmed working directly — this specific
failure mode may be resolved or was tool-specific. Sentry:analyze_issue_with_seer (Autofix)
returned HTTP 402 "No budget for Seer Autofix" on July 12 — needs billing attention before it can
be used again; do not assume it works without checking.
JULY 12, 2026 — Web push 410/404 detection was dead code due to a Python/requests gotcha.
services/push.py's expiry check was `if e.response and e.response.status_code == 410`. The
`requests` library overrides truthiness on Response objects so that `bool(response)` is False for
ANY error status code (400+) by design — meaning this check silently evaluated to False for every
error response, 410 included, before the status code was ever inspected. This branch had never
fired since it was written. Real-world effect: expired push subscriptions were never cleaned up
and instead generated a fresh Sentry error (event: push_send_failed) on every retry, indefinitely
— accumulated 45+ events over roughly two weeks before being caught via a routine Sentry check.
Fixed by checking `is not None` instead of relying on truthiness; also added 404 as an equivalent
"gone" signal per the Web Push spec (RFC 8030). SEPARATELY, a second call site
(run_interview_nudge, the 24h/72h signup-nudge job) called the same send function but completely
ignored its return value, so even with push.py fixed this job would have kept re-sending to dead
endpoints hourly forever. Fixed to capture the result and clean up expired subscriptions using a
fresh DB connection after the loop (the original query's connection had already closed by that
point in the function — worth remembering as a scope gotcha in async code with early-closing
context managers). LESSON: code that "looks correct" on read-through can still never execute if a
truthiness check on a library object doesn't behave the way it appears to. When debugging "this
cleanup logic exists but nothing is ever cleaned up," check whether the branching condition can
ever actually be reached, not just whether the logic inside it is correct.
JULY 12, 2026 — Evolution page "TODAY · [old date]" mislabel, root cause found (was previously
unresolved and guessed to be a caching/date-math issue in the July 5 handover note — it was
neither). The word "Today" was hardcoded next to `latest.date`, where `latest` is the user's most
recently COMPLETED task, not necessarily a task from today. For any user who hadn't completed a
task recently (a large share of the user base, per RETENTION above), the page would confidently
label an old date as "Today." Fixed to only show "Today" when the date genuinely matches the
current date, otherwise showing "Most recent." Same family of harm as the UI failure-framing audit:
telling a lapsed user something subtly false at the exact moment they're least engaged.


ENGINEERING RULES — NEVER VIOLATE THESE

Supabase Storage — always use supabase-py client, never raw httpx calls
asyncpg vector syntax — never use :param::vector. Always inline in f-strings or use CAST(:param AS vector)
asyncpg type casts — avoid ::jsonb, ::text[] with named params. Use CAST() syntax
FastAPI route ordering — named routes MUST be defined BEFORE catch-all routes (/{date})
Streak updates — always update immediately on user action, never defer to scheduler
Task queries — never filter on specific task_type values unless deliberately excluding
JSON serialisation — always json.dumps(), never str() on structured data
Environment variables — never hardcode. All config lives in backend/core/config.py
File delivery — always deliver complete files. Pelumi deploys by replacing whole files
No partial diffs unless the change is a single clearly-identified line
Billing dual-write — webhook handlers must write to BOTH users AND subscriptions tables
Frontend routing — all Next.js folder names must be lowercase (Vercel is case-sensitive on Linux)
Deployment discipline — never add an import before the file exists in the repo; commit the file
and the import in the same commit (learned from a production build failure)
AsyncIO scheduler — never use asyncio.create_task() inside lambdas in APScheduler jobs; pass
coroutines directly to AsyncIOScheduler
Ask, then verify in code — if an AI prompt asks the model to self-police something (don't repeat
X, don't generate Y), assume it will fail silently in production unless there is also a
deterministic code-level check. This is the single most repeated failure pattern in this project's
history (forbidden-task-list, domain-rotation, domain-field-null were the same bug shape three
times) — applies beyond the task generator, to any future prompt-based constraint.
Never fabricate social proof — the single highest credibility risk before any public launch
push. No invented testimonials, no unverifiable user-count claims. See LANDING PAGE / MARKETING
INTEGRITY above for the concrete example of this rule being enforced.
Security — IP blocking on credential-scan patterns is live (commits add44a8, 12cb9a7, late
April): repeated 404s from one IP trigger a block. If debugging unexpected 403s/blocks for a
legitimate user or test account, check this middleware before assuming it's unrelated.
Truthiness on library response objects is not safe to assume — a Python requests.Response
object is falsy for ANY error status code by design (`bool(response)` == `response.ok`). Never
write `if some_response and some_response.status_code == X`; the `and` can silently short-circuit
before the status code is ever checked. Use `is not None` when you mean "does this object exist,"
not truthiness. This exact bug shipped and went undetected for weeks — see INCIDENT LOG, July 12.
Retry temperature is not a universal dial — lowering it improves compliance ONLY when paired
with concrete alternative material in the retry prompt. Lowering it with vague retry guidance
("generate something different") can increase repetition instead of reducing it. If you lower
retry temperature for one failure-mode branch, audit every other branch that shares the same
retry call path to make sure it isn't left with vague guidance under the new, less-random setting.
Async DB session scope — a session opened inside `async with get_db_context() as db:` is closed
the moment that block exits, even if you're still inside the same function. Do not assume `db` is
usable in code that runs after the `with` block closes (e.g. inside a loop that follows it) — open
a fresh context for any work that needs to happen after the original query's block has exited.


DEPLOYMENT PROCEDURE
Backend (Railway)
bashgit add -A
git commit -m "your message"
git push origin main
# Railway auto-deploys ~10–15 min. Monitor: Railway → Deployments → View logs
Frontend (Vercel)
bash# Same git push — Vercel auto-deploys ~2 min
Windows/PowerShell note: multi-line commit messages containing quoted words (e.g. "Today",
"duplicate") will break `git commit -m "..."` in PowerShell — it does not parse embedded quotes
inside a multi-line string the way bash does, and will split the rest of the message into invalid
pathspec arguments. Use `git commit -F message.txt` (write the message to a file first) for any
commit message longer than one line or containing quoted words.
Environment variables

Backend: Railway → Service → Variables
Frontend: Vercel → Project → Settings → Environment Variables
Never commit .env files


MONETISATION TIERS
TierNameMonthlyAnnualCoach quotaFreeThe Spark$0—5 messages/dayProThe Forge$4.99$47.88UnlimitedEliteThe Identity$10.99$107.88Unlimited + re-interview
Open strategic question, flagged not resolved: a Paul-Graham-style pressure test of the £4.99
price point raised the possibility that it signals insufficient confidence in the product's own value.
This has not been acted on — noting it here so it isn't lost, not because a decision has been made.

DATABASE — KEY TABLES (not exhaustive — extensive AI/analytics schema exists beyond this list)
Core

users — subscription_plan, stripe_customer_id, stripe_subscription_id. COUNT(*) = 99 as of July 12.
goals — refined_statement, required_identity, status (including approaching_completion).
COUNT(DISTINCT user_id) = 49 as of July 12.
identity_profiles — transformation_score, streak, days_active, commitment_statement. Only 3 users
have a commitment_statement of 30+ characters as of July 12 — this is the real activation number.
daily_tasks — task_type: becoming / identity_anchor / micro_action / challenge; generation_context
JSONB column stores domain, momentum_state, streak, is_fallback at generation time. Fallback tasks
created via the main nightly path do NOT currently get a "reason" key (see AI SYSTEMS observability
gap) — only the backlog path (_create_fallback_task) writes one.
objectives, identity_traits
reflections — questions_answers JSONB, depth_score
coach_sessions, coach_moments, coach_patterns, coach_interventions, coach_safety_flags
onboarding_interview_state — messages JSONB (raw interview excerpts pulled from here)

Billing

subscriptions — unique constraint on user_id
invoices

Notifications

notification_queue
push_subscriptions — endpoint, p256dh, auth tokens. Expiry cleanup (410/404) FIXED July 12 — see
INCIDENT LOG. Both the daily-push job and the interview-nudge job now correctly remove dead rows.

Key SQL function

get_user_ai_context(id::uuid) — UUID cast required. Does NOT include today_task (see AI SYSTEMS
fix above) — this is patched at the Python layer, not in the SQL function itself. If this function
is ever modified directly, re-check whether the Python-layer patch is still needed or now redundant.


SESSION OPERATING PROCEDURE
Start of every session:

Read this file completely — and flag anything that looks stale rather than assuming it's current
Read TODO.md for current sprint focus
Ask "What are we working on today?" if TODO is ambiguous
Do not start coding until the task is clear

During session:

Apply the mentor operating mode from the top of this file — always, not just when asked
Plain English explanation before code
Complete files only — no partial diffs
Check asyncpg gotchas, route ordering, type casts, retry-temperature/guidance pairing, and async
DB session scope before delivering (see ENGINEERING RULES — these are all things that have
actually shipped broken because they looked fine on read-through)
If a prompt-based fix is proposed for anything the AI must "remember not to do," ask whether a
code-level check is also needed (see Engineering Rule: Ask, then verify in code)
Update TODO.md after each completed task

Debugging order: Railway logs → Sentry → Supabase queries → manual logic trace → fix root cause
Updating this file: when a session produces a material change to product state (a rewrite, a
fix, a metric, an incident), update this file in the same session, not "later." A stale version of
this file has already cost repeated wasted context in this project — do not let it happen again.
Commit message discipline: write commit messages (or at least bodies) assuming the reader has no
other context. On Windows/PowerShell, use `git commit -F message.txt` for multi-line messages —
see DEPLOYMENT PROCEDURE.

AI AGENTS ROSTER
All agent files live in docs/agents/. To use: open new Claude conversation, paste agent file contents, give task.
AgentTriggerFilePM Agent"Ask the PM agent"docs/agents/PM_AGENT.mdMarketing Agent"Ask the marketing agent"docs/agents/MARKETING_AGENT.mdQA Agent"Ask the QA agent"docs/agents/QA_AGENT.mdSupport Agent"Ask the support agent"docs/agents/SUPPORT_AGENT.md

OTHER PELUMI BRANDS
IIC Networks — Influence, Impact, Change. Coaching, speaking, leadership.
Voice: Authoritative, practical, faith-informed, African professional context.
Author Brand (@PelumiOlawole) — Book: Petty Little Things.
Voice: Conversational, honest, sometimes sharp, always constructive.
Platform: LinkedIn + Instagram.

HOW TO UPDATE THIS FILE
bashgit add CLAUDE.md
git commit -F message.txt
git push origin main
Then paste updated contents into this Claude Project's custom instructions.
Do this the same day something material changes. Do not let this file drift again.

This file is the single source of truth for all Claude sessions on OneGoal Pro — but it is only
as good as its last honest update. If it contradicts what you can directly observe (Sentry, Supabase,
the live product), the observation wins, and you should say so.