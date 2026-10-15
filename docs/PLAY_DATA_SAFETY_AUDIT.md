# Play data safety audit: PostHog and third-party data

Prepared 15 October 2026. Report only. No code was changed for this audit.

Evidence labels used throughout:

- **Confirmed (code):** read in the repository at commit `81c0cb0`.
- **Confirmed (live):** read from the production site (onegoalpro.app) on 15 October 2026.
- **Library default:** not set in our code, so the installed library's default applies. Read from the installed package source.
- **Assumed:** depends on a dashboard setting or vendor behaviour that cannot be seen from code. Pelumi should check these before submitting the form.

## Summary

1. The cookie banner is not accurate. PostHog sets an analytics cookie on every visit, starts before the visitor makes any choice, and the Decline button does nothing to stop it. The privacy policy's Cookies section has the same problem.
2. PostHog runs in the **US** region and receives each signed-in user's **email address**.
3. Interview, coach and reflection text is sent to **OpenAI**. The privacy policy already says this.
4. Sentry session replay is **not** active in practice. The sample rates are set, but the replay integration is never added.
5. The Sentry scrubbing of AI routes is still in place and does match the live routes.
6. A decision on PostHog consent is needed before the data safety form is final, because it changes the answer to "is analytics data collection optional?".

## 1. PostHog configuration (frontend)

Files: `frontend/src/lib/posthog.ts`, `frontend/src/components/PostHogInit.tsx`, `frontend/src/components/CookieBanner.tsx`, `frontend/src/app/layout.tsx`, `frontend/src/stores/auth.ts`. Installed `posthog-js` version: 1.359.1.

| Setting | Value | Evidence |
|---|---|---|
| API host | `https://us.posthog.com` (US region) | Confirmed (live): the production layout bundle contains `api_host:"https://us.posthog.com"`. The code falls back to `https://app.posthog.com`, also US, if the env var is missing. |
| `persistence` | `localStorage+cookie`: one first-party cookie named `ph_<project key>_posthog` plus a localStorage entry with the same key | Library default; our init passes no `persistence` option. |
| `autocapture` | On: clicks, form submits and element text are captured automatically | Library default |
| `capture_pageview` | On | Library default (no `defaults` date is set, so the classic pageview behaviour applies) |
| `capture_pageleave` | On (`if_capture_pageview`) | Library default |
| Session recording | Not disabled in code (`disable_session_recording` defaults to false). Whether it actually records depends on the PostHog project setting. | Library default; project setting is **Assumed / unknown** |
| `person_profiles` | `identified_only` | Library default |
| What `identify()` sends | Frontend: user ID **and email**, plus `tier` (plan) after login (`stores/auth.ts` lines 29 and 33). Backend: user ID, **email**, `signup_provider`, `verified` (`services/analytics.py`, called from `api/routers/auth.py`). | Confirmed (code) |
| IP capture | Not disabled in code. PostHog stores the client IP, and derives approximate location from it, unless the project setting "Discard client IP data" is on. | Project setting **Assumed / unknown** |
| Init timing vs the cookie banner | PostHog initialises on page mount from `PostHogInit` in the root layout, **before** the visitor clicks anything. | Confirmed (code and live) |
| Does Decline stop it? | **No.** Accept and Decline both only write `ogp_cookie_consent` to localStorage. Nothing reads that value. PostHog is never told to opt out. | Confirmed (code and live) |

If session recording is turned on in the PostHog project, note that PostHog masks form inputs by default but not rendered text. Coach replies and interview questions shown on screen would be captured in recordings.

Custom events sent (confirmed in code): `interview_completed`, `reinterview_completed`, `upgrade_initiated` (plan, billing cycle), `subscription_activated` (tier), `task_completed` (task ID), and from the backend `user_signed_up` (provider) and login tracking.

## 2. Other client-side third parties and browser storage

| Item | What it does | Cookies / storage | Evidence |
|---|---|---|---|
| PostHog | Product analytics (section 1) | Cookie `ph_<key>_posthog` + localStorage | Confirmed (live) for host and init; library default for persistence |
| Sentry browser SDK (`@sentry/nextjs` 10.42.0) | Error reports, 10% performance tracing | No cookies set by our config. `sendDefaultPii` is not enabled. | Confirmed (code), `instrumentation-client.ts` |
| Sentry session replay | `replaysSessionSampleRate: 0.1` and `replaysOnErrorSampleRate: 1.0` are set, but `Sentry.replayIntegration()` is never added, so replay does not run. If someone adds the integration later, replay starts immediately at those rates. | n/a | Confirmed (code) |
| Fonts (Playfair Display, DM Sans, DM Mono) | `next/font/google` downloads them at build time and serves them from our own domain. No request to Google at runtime. | None | Confirmed (live): font files load from `/_next/static/media/` |
| Cormorant Garamond on `/evolution` | `@import` from `fonts.googleapis.com` in the page's inline styles. Our own Content-Security-Policy (`style-src 'self' 'unsafe-inline'`, `font-src 'self'`) blocks it, so the browser never contacts Google and the font silently fails to load. Not a data issue, but a visual bug. | None | Confirmed (code and live CSP header) |
| Stripe | Stripe.js is **not** loaded. Upgrading redirects to Stripe's hosted checkout page. Stripe sets its own cookies there, on Stripe's domain, not ours. | None on our domain | Confirmed (code), `settings/upgrade/page.tsx` line 71 |
| Google sign-in | Redirect through Supabase Auth to Google's consent screen. Nothing Google-owned loads on our pages. | None on our domain | Confirmed (code), `login/page.tsx` line 65 |
| Our own localStorage | `access_token`, `refresh_token`, `one-goal-auth` (login state), `ogp_cookie_consent`, `ogp_install_banner`, `ogp_pre_answer` (the landing-page answer, removed once the interview loads it) | localStorage only. **Our code sets no cookies at all.** | Confirmed (code) |
| Service worker | Caches `/offline.html` only | Cache Storage | Confirmed (code) |

## 3. Backend processors

| Service | Data it receives | Evidence |
|---|---|---|
| Supabase (Postgres, Auth, Storage) | Everything stored by the product: account, goals, tasks, reflections, coach sessions, interview state, embeddings, avatars, push subscriptions | Confirmed (code) |
| OpenAI | Interview messages, coach messages, reflection answers, the user's display name, goal, identity traits, task history and profile context (`ai/memory/context_builder.py`, `ai/engines/*`). Text is also sent for embeddings. Email is **not** included in the AI context. | Confirmed (code) |
| Resend | Recipient email address and email content, including the daily task's identity statement | Confirmed (code), `services/email.py` and `core/email.py` |
| Stripe | Customer email and internal user ID (as metadata), plan. Card details go only to Stripe's hosted checkout. | Confirmed (code), `services/billing.py` |
| PostHog (server-side) | User ID, email, signup provider, verified flag, signup and login events. Host defaults to `https://us.posthog.com`. | Confirmed (code), `services/analytics.py`, `core/config.py` |
| Sentry (backend) | Exceptions with stack traces and request metadata; 5% tracing; profiling disabled. `before_send` strips request bodies and cookies for any URL containing `/api/coach/`, `/api/onboarding/interview` or `/api/reflections`. Routes are mounted under `/api`, so these prefixes do match live traffic. | Confirmed (code), `main.py` lines 23 to 60 |
| Sentry (backend), residual risk | The Python SDK attaches local variables to stack frames by default. An exception inside the coach or interview code could still carry message text in those variables, because `before_send` only removes the request body. | Inferred from SDK default behaviour, not observed |
| Railway | Hosts the backend and Redis cache | Confirmed (code and CLAUDE.md) |
| Vercel | Hosts the frontend; standard request logs (IP, URL) | Assumed (standard hosting behaviour) |
| Browser push services (for example Google FCM for Chrome) | Push subscription endpoint, plus a notification payload that is encrypted end to end under the Web Push standard | Confirmed (code) uses `pywebpush`; encryption is part of the standard |
| Google (sign-in) | Standard OAuth sign-in through Supabase | Confirmed (code) |

## 4. Verdict on the cookie banner

The banner text is: "We use essential cookies to keep you logged in and remember your preferences. No tracking or advertising cookies."

- **"No tracking or advertising cookies." is false.** The advertising part is true. The tracking part is not: PostHog sets an analytics cookie (`ph_<key>_posthog`) that identifies the browser across visits, and it does so before the visitor responds. Under UK PECR, analytics cookies are not "strictly necessary", so they need consent first.
- **"We use essential cookies to keep you logged in" is inaccurate.** Login state is kept in localStorage, not cookies. Our code sets no cookies at all. The only cookie on our domain is PostHog's.
- **The Decline button is non-functional.** It records the choice and changes nothing. A Decline button that doesn't decline is arguably worse than having no banner.
- The privacy policy's section 8 ("We use only functional cookies required for authentication and session management") has the same problem and should be corrected together with the banner.

## 5. Options (none implemented)

**(a) PostHog with `persistence: 'memory'` (or cookieless mode).** No cookie and no localStorage, so the banner's cookie claim becomes true. Trade-off: each page load looks like a new anonymous visitor until login, so anonymous funnels (landing page to signup) become unreliable. Events and IP still go to PostHog, so the privacy policy and data safety form still have to declare analytics collection.

**(b) Initialise PostHog only after Accept, and opt out on Decline.** This is the standard compliant pattern and makes the existing Accept/Decline buttons mean something. Trade-off: you lose analytics for everyone who declines or ignores the banner, often a large share of visitors. The `identifyUser` and `trackEvent` calls also need to check consent. The data safety form can then honestly mark analytics as optional.

**(c) Change the banner wording only.** Cheapest. Trade-off: it doesn't fix the consent requirement for analytics cookies, and it leaves a Decline button that does nothing. On its own it only makes the false statement less specific.

**Recommendation (Pelumi decides):** (b), plus dropping `email` from both `identify()` calls (the user ID is enough to join PostHog data back to the database). Update the banner and privacy-policy wording at the same time. With 0 signups in the last 30 days, the analytics lost to declines is close to zero today, and it's cheaper to fix this before the Play listing goes public.

## 6. Draft Google Play data safety answers

Play's definition: transferring data to a service provider that processes it on our behalf (OpenAI, Resend, Stripe, Supabase, Sentry, PostHog, Railway, Vercel) is **not** "sharing". So every row below is "Shared: No". "Optional" means a user can use the app without providing it.

| Data type (Play category) | Collected | Shared | Purpose | Optional | Evidence |
|---|---|---|---|---|---|
| Name | Yes (display name) | No | App functionality, Account management, Personalisation (used in AI coaching) | Required | Confirmed (code) |
| Email address | Yes | No | Account management, App functionality, Developer communications (task and re-engagement emails), **Analytics** (sent to PostHog) | Required | Confirmed (code) |
| User IDs | Yes (internal user ID) | No | App functionality, Analytics | Required | Confirmed (code) |
| Photos | Yes, only if the user uploads an avatar | No | App functionality | **Optional** | Confirmed (code, Supabase avatars bucket) |
| App interactions | Yes (PostHog pageviews, autocapture, custom events) | No | Analytics | Required today. **Optional only if option (b) ships first.** | Confirmed (code and live) |
| In-app search history | No (the app has no search) | n/a | n/a | n/a | Confirmed (code) |
| Other user-generated content (interview answers, coach messages, reflections, goal and commitment statements) | Yes | No (OpenAI is a processor) | App functionality, Personalisation | Required: the product cannot work without it | Confirmed (code) |
| Purchase history (subscription plan and status) | Yes | No | App functionality, Account management | Only for paying users | Confirmed (code) |
| Financial info (card details) | No. Collected by Stripe on Stripe's hosted page, never by our app or servers | n/a | n/a | n/a | Confirmed (code) |
| Crash logs | Yes (Sentry, frontend and backend) | No | App functionality, Analytics | Required | Confirmed (code) |
| Diagnostics (performance traces) | Yes (Sentry tracing 10% frontend, 5% backend) | No | App functionality, Analytics | Required | Confirmed (code) |
| Device or other IDs | Yes: PostHog anonymous device ID (cookie/localStorage), push subscription endpoint | No | Analytics, App functionality (notifications) | Push is optional; the PostHog ID is required today | Confirmed (code) for push; library default for the PostHog ID |
| Approximate location (derived from IP) | Probably yes, through PostHog GeoIP, unless "Discard client IP data" is enabled in the PostHog project | No | Analytics | Required today | **Assumed:** check the PostHog project settings |
| Precise location | No | n/a | n/a | n/a | Confirmed (code): no geolocation API use, and the Permissions-Policy header blocks it |

**Is data encrypted in transit? Yes.**
- The site sends HSTS (`max-age=63072000`); confirmed live.
- The Content-Security-Policy only allows HTTPS connections, to `api.onegoalpro.app`, Stripe, PostHog and Sentry; confirmed live.
- Every backend SDK (OpenAI, Resend, Stripe, PostHog, Sentry) uses HTTPS endpoints; confirmed in code.
- **Assumed:** the backend's Postgres connection to Supabase uses SSL. `core/database.py` sets no explicit `sslmode`, so this depends on the `DATABASE_URL` value and the Supabase project's SSL enforcement setting. Check "Enforce SSL" in Supabase.

**Can users request deletion? Yes.** In-app deletion exists, and a public deletion page is being added at `https://onegoalpro.app/delete-account` (Task C). That task also reports exactly what the deletion removes.

## Other findings from this audit

- **Dead code with fake testimonials:** `frontend/src/components/landing/fallback/StaticLanding.tsx` still contains the fabricated testimonials ("Marcus C.", "Sarah M.", "Aisha P.") that were removed from the live landing page. Nothing imports the file, so it is not shipped today. Delete it so it can't be wired back in by accident.
- **Contact address mismatch:** the privacy policy uses `hello@onegoalpro.app`. The deletion page brief uses `support@onegoalpro.app`. Make sure both addresses are routed in Cloudflare, or pick one.
- **The privacy policy doesn't mention international transfers.** PostHog (US region, with email addresses) and OpenAI (US) both receive personal data. UK GDPR expects a privacy policy to say this and name the safeguard, for example the UK Extension to the EU-US Data Privacy Framework or standard contractual clauses.
