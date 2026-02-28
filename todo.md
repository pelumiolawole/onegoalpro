# TODO: Fix Login Redirect Routing

## Issue
After login, the app checks `onboarding_step` and redirects users who haven't completed onboarding.
Currently it redirects all incomplete users to `/onboarding` — a route that **does not exist** — causing a 404.

## Present Error
- User logs in
- `onboarding_step < 5` → `router.push('/onboarding')` fires
- Page 404s because the Next.js route group is `(onboarding)` (parentheses = no URL prefix)
- Real routes are: `/interview`, `/goal-setup`, `/preview`, `/activate`

**File:** `frontend/src/app/(auth)/login/page.tsx` lines 29–33

```typescript
// CURRENT (BROKEN):
const step = data.user.onboarding_step
if (step < 5) {
  router.push('/onboarding')   // ← does not exist
} else {
  router.push('/dashboard')
}
```

## Fix Required
Replace the redirect logic with step-aware routing:

```typescript
// FIXED:
const step = data.user.onboarding_step
if (step === 0 || step === 1) {
  router.push('/interview')
} else if (step === 2) {
  router.push('/goal-setup')
} else if (step === 3) {
  router.push('/preview')
} else if (step === 4) {
  router.push('/activate')
} else {
  router.push('/dashboard')
}
```

## Step → Status Mapping (for reference)
| Step | onboarding_status     | Route        |
|------|-----------------------|--------------|
| 0    | created               | /interview   |
| 1    | interview_started     | /interview   |
| 2    | interview_complete    | /goal-setup  |
| 3    | goal_defined          | /preview     |
| 4    | strategy_generated    | /activate    |
| 5    | active                | /dashboard   |

## Also check
- `src/app/(onboarding)/interview/page.tsx` — post-interview redirect should go to `/goal-setup` not `/onboarding/goal`
- `src/app/(onboarding)/layout.tsx` — nav path should be `/goal-setup` not `/onboarding/goal`
- `src/app/(onboarding)/preview/page.tsx` — back-navigation should use `/goal-setup` not `/onboarding/goal`
