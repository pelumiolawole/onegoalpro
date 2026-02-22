# One Goal — Project Map & Status Report

**Author:** Pelumi Olawole  
**Date:** Sunday, 22 February 2026 — 20:35 GMT  
**Status:** Backend deployment in progress 🔧

---

## What We Built

One Goal is an AI-powered personal coaching app. The concept: one user, one goal, one AI coach that tracks your progress, interviews you to understand your life deeply, and generates a personalised strategy to help you achieve your goal.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | Python FastAPI, async SQLAlchemy |
| Database | PostgreSQL via Supabase (with pgvector for AI embeddings) |
| AI | OpenAI GPT-4, LangChain |
| Auth | JWT tokens + Supabase Auth |
| Hosting (backend) | Railway |
| Hosting (frontend) | Vercel (pending) |
| Cache | Redis (configured, not yet provisioned) |

### Backend Structure

```
backend/
├── main.py                    # FastAPI app factory
├── requirements.txt           # Python dependencies
├── procfile                   # Railway start command
├── api/
│   ├── routers/               # 7 route modules
│   │   ├── auth.py            # Signup, login, JWT, OAuth
│   │   ├── onboarding.py      # AI interview flow
│   │   ├── goals.py           # Goal CRUD
│   │   ├── tasks.py           # Task management
│   │   ├── reflections.py     # Daily check-ins
│   │   ├── coach.py           # AI coaching chat
│   │   └── progress.py        # Progress tracking
│   ├── schemas/               # Pydantic request/response models
│   └── dependencies/          # Auth middleware, DB sessions
├── core/
│   ├── config.py              # Settings from env vars
│   ├── database.py            # Async SQLAlchemy engine
│   ├── security.py            # JWT + password hashing
│   ├── cache.py               # Redis client
│   └── middleware.py          # CORS, logging
├── db/
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── goal.py
│   │   ├── task.py
│   │   └── identity_profile.py
│   └── migrations/            # 4 Alembic SQL migrations
├── services/                  # Business logic
│   ├── scoring.py
│   └── scheduler.py
└── ai/                        # AI/LangChain logic
```

### Frontend Structure

```
frontend/
├── app/
│   ├── login/                 # Login page
│   ├── signup/                # Signup page
│   └── dashboard/             # Main app (pending)
├── components/
└── lib/
    └── api.ts                 # API client
```

### Database (Supabase)

- **Project:** one-goal
- **Region:** Europe West
- **URL:** https://wozqwbbdsaxbbxzxihic.supabase.co
- **Tables created:** ~15 tables via 4 migration files
- **Extensions:** pgvector enabled

---

## What Has Been Completed ✅

1. **Full backend codebase** — all routes, models, schemas, core modules written
2. **Full frontend codebase** — login and signup pages built and rendering
3. **Supabase database** — project created, all migrations executed, tables live
4. **Railway account** — project created, GitHub repo connected, root directory set to `backend`
5. **Environment variables** — all 8 variables configured in Railway (DATABASE_URL, JWT_SECRET_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, ENVIRONMENT, ALLOWED_ORIGINS)
6. **GitHub repository** — `github.com/pelumiolawole/onegoalclaude`

---

## Errors & Constraints Faced

### Deployment Battle Log (Railway Backend)

| # | Error | Cause | Fix |
|---|-------|-------|-----|
| 1 | `ModuleNotFoundError: No module named 'db.models'` | `db/models/` folder missing from GitHub | Created and pushed `db/models/` with all 4 model files |
| 2 | `ImportError: cannot import name 'router' from 'api.routers.auth'` | GitHub had old version of auth.py using `routers` not `router` | Replaced all 7 router files from source |
| 3 | `ImportError: cannot import name 'ChangePasswordRequest'` | GitHub had outdated `api/schemas/auth.py` missing new classes | Replaced all schema + core files |
| 4 | `ImportError: email-validator is not installed` | `email-validator` package missing from `requirements.txt` | Added `email-validator==2.2.0` |
| 5 | `Could not find version supabase==2.10.1` | Version 2.10.1 was never published to PyPI (yanked) | Downgraded to `supabase==2.9.1` |

### Root Cause
GitHub repo was populated by uploading files manually rather than using `git push` from VS Code. This caused many files to be out of sync — GitHub had older versions while the correct versions existed locally. Each Railway deploy revealed a new mismatch. Going forward, all changes pushed via git CLI.

### Key Constraints
- Railway uses Python 3.13 by default — some packages behave differently
- `supabase` package has several yanked versions between 2.10–2.22
- `httpx` must stay at `0.27.x` for supabase 2.9.1 compatibility (`<0.28` required)
- Redis is in the config but no Redis instance is provisioned yet — this will cause a startup warning but not a crash if handled gracefully

---

## What Is Left 📋

### Immediate (tonight)
- [ ] Get Railway deployment to succeed (currently on error 5 of unknown total)
- [ ] Verify backend starts and `/docs` endpoint loads
- [ ] Test `/api/auth/signup` returns a valid response

### Next Steps
- [ ] Deploy frontend to Vercel
- [ ] Set `NEXT_PUBLIC_API_URL` in Vercel to Railway URL
- [ ] Update `ALLOWED_ORIGINS` in Railway to include Vercel URL
- [ ] End-to-end test: signup → login → dashboard

### Later (Product)
- [ ] Onboarding AI interview flow
- [ ] Goal definition and strategy generation
- [ ] Daily task + reflection system
- [ ] AI coaching chat
- [ ] Progress dashboard
- [ ] Redis for token caching (or swap to DB-backed sessions)
- [ ] Google OAuth integration
- [ ] Mobile responsiveness
- [ ] Production hardening (rate limiting, proper error handling)

---

## Environment Variables Reference

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | postgresql+asyncpg://postgres:[password]@db.wozqwbbdsaxbbxzxihic.supabase.co:5432/postgres |
| `JWT_SECRET_KEY` | onegoal-secret-jwt-key-2026-production |
| `SUPABASE_URL` | https://wozqwbbdsaxbbxzxihic.supabase.co |
| `SUPABASE_ANON_KEY` | [from Supabase Settings → API] |
| `SUPABASE_SERVICE_ROLE_KEY` | [from Supabase Settings → API] |
| `OPENAI_API_KEY` | [from platform.openai.com] |
| `ENVIRONMENT` | production |
| `ALLOWED_ORIGINS` | http://localhost:3000 (update to Vercel URL after deploy) |

---

*This document is a living record of the One Goal build. Updated as the project progresses.*

— **Pelumi Olawole**  
*22 February 2026, 20:35 GMT*
