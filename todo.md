# OneGoal Pro — Current Status

## ✅ Completed
- Supabase DB (one-goal-v2) with pgvector
- All migrations executed
- Railway backend deployed and running
- Redis connected
- OpenAI API key configured
- Login / signup flow working
- Interview engine working (SQL CAST fix applied)
- Interview completes and saves to DB
- Routing fixed: login now routes by onboarding_step

## 🔧 In Progress
- Login redirect to /onboarding bug
  - app-layout.tsx and login/page.tsx cleaned up and provided
  - Awaiting commit + deploy

## ⏭️ Next Steps (in order)

### 1. Verify login routing works after deploy
- Visit onegoalpro.vercel.app
- Sign in → should land on /goal-setup (your step is 2)

### 2. Test /goal-setup page
- This is where the user defines their One Goal from interview data
- Backend endpoint: POST /api/onboarding/goal-setup
- Check if page loads and goal submission works

### 3. Test /preview page
- Shows the AI-generated strategy
- Backend endpoint: GET /api/onboarding/goal-setup/preview

### 4. Test /activate page
- Confirms goal and generates first tasks
- Backend endpoint: POST /api/onboarding/activate

### 5. Verify dashboard loads after activation
- onboarding_step should be 5
- Tasks, scores, streak should render

## Known Issues
- "od" display bug on dashboard streak/days (cosmetic, low priority)
- Interview history still visible but AI returns "I didn't catch that"
  after completion (expected — interview is done, state is is_complete=true)

## Deployments
- Frontend: onegoalpro.vercel.app (Vercel)
- Backend:  onegoalclaude-production.up.railway.app (Railway)
- Database: Supabase one-goal-v2

## Your Account
- Email: olawolepelumisunday@gmail.com
- onboarding_step: 2 (interview_complete → should route to /goal-setup)

## 🐛 Active Bug — Fix in Next Session

**`invalid input syntax for type date: "999"`**
- Triggered by: `POST /api/onboarding/goal-setup` → "Build my strategy"
- Error location: `get_user_ai_context` Postgres function, called from `context_builder.py` line 65
- Cause: A date column is storing "999" (likely AI returning a number instead of a date for estimated_timeline or target_date)
- Suspect tables: goals.target_date, identity_profiles.last_active_date
- Fix: Clean bad data in Supabase OR patch the function to handle non-date values safely
- Diagnose with:
  SELECT target_date FROM goals WHERE user_id = 'fa5a16ab-e6ed-4217-bffd-73447c22459c';
  SELECT last_active_date FROM identity_profiles WHERE user_id = 'fa5a16ab-e6ed-4217-bffd-73447c22459c';
  SELECT * FROM identity_profiles WHERE user_id = 'fa5a16ab-e6ed-4217-bffd-73447c22459c';