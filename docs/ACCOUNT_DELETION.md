# Account deletion: plan

Written 15 October 2026, before implementation. Mapped against the live schema (Supabase project `guqlwplztxxiseyenbye`).

## How deletion works

**On request** (Settings, confirmed by typing `DELETE`, or by email to support):
1. Cancel any active Stripe subscription immediately, so the user is not charged again. If Stripe cannot be reached, the request fails and nothing is marked, so a user is never told their account is deleted while still being billed.
2. Set `users.is_active = false` and `users.deletion_scheduled_at = now()`. Every scheduled job (task generation, emails, push, nudges, reviews) already filters on `is_active = TRUE`, so all of them stop at once.
3. Delete the user's push subscriptions immediately.
4. Revoke the refresh token and blocklist the current access token. Any other access token still in use is rejected because `get_current_user` now refuses accounts with a pending deletion.
5. Record a `deletion_requests` row (status `pending`).

**Purge** (nightly job at 03:00 UTC, so within 24 hours, inside the 30 days the privacy policy states):
1. Cancel the Stripe subscription again if one is still active (idempotent safety net).
2. Delete every avatar object under `avatars/{user_id}/` using the supabase-py client.
3. Delete the Supabase Auth user (sign-in identity, including Google) found by email.
4. Anonymise `ai_interactions` for the user (clear `error_message` and `request_hash`).
5. `DELETE FROM users WHERE id = :user_id`. ON DELETE CASCADE removes the rows listed below.
6. Mark the `deletion_requests` row `completed` with `completed_at = now()`.

Steps 1 to 3 run before the database delete. If any of them fails, that user is skipped, the error goes to Sentry, and the purge retries the next night. Every step tolerates already-deleted state, so the purge is safe to re-run.

## Table by table (31 tables and 3 views with a `user_id` column)

| Table | Foreign key to users | Action | Reason |
|---|---|---|---|
| ai_coach_messages | CASCADE | Delete | Coach conversation content |
| ai_coach_sessions | CASCADE | Delete | Coach sessions |
| ai_safety_flags | CASCADE | Delete | Personal content |
| behavioral_patterns | CASCADE | Delete | Profile data |
| behavioral_snapshots | CASCADE | Delete | Profile data |
| coach_interventions | CASCADE | Delete | Personal content |
| coach_moments | CASCADE (also via coach_sessions) | Delete | Personal content |
| coach_patterns | CASCADE | Delete | Profile data |
| coach_safety_flags | CASCADE | Delete | Personal content |
| coach_sessions | CASCADE | Delete | Personal content |
| coaching_sessions | CASCADE | Delete | Personal content |
| daily_tasks | CASCADE | Delete | Personal content |
| data_processing_consent | CASCADE | Delete | Linked to the person |
| engagement_events | CASCADE | Delete | Behavioural data |
| goals | CASCADE | Delete | Personal content |
| identity_profiles | CASCADE | Delete | Includes commitment statements |
| identity_traits | CASCADE | Delete | Profile data |
| integration_configs | CASCADE | Delete | Linked to the person |
| invoices | CASCADE | Delete | Empty table; Stripe holds the real invoices |
| milestones | CASCADE (also via objectives) | Delete | Personal content |
| notification_queue | CASCADE | Delete | Queued messages |
| objectives | CASCADE | Delete | Personal content |
| onboarding_interview_state | CASCADE | Delete | Raw interview answers |
| progress_metrics | CASCADE | Delete | Behavioural data |
| push_subscriptions | CASCADE | Delete at request time | Device endpoint |
| reflections | CASCADE | Delete | Personal content |
| subscriptions | CASCADE | Delete | Plan and Stripe IDs |
| user_embeddings | CASCADE | Delete | Vector embeddings of personal text |
| weekly_reviews | CASCADE | Delete | Personal content |
| ai_interactions | SET NULL | **Anonymise** | Token counts and cost per AI call, kept for cost accounting. `user_id` becomes NULL through the foreign key; `error_message` and `request_hash` are cleared first because they could relate to the request content. |
| deletion_requests | removed by migration 012 | **Retain** | Record that the deletion was requested and completed: user UUID, timestamps, status. No name, email or content. |
| trait_progress_summary, user_dashboard, users_needing_intervention | views | Nothing to do | Views over the tables above |
| users | | Delete | The row itself |

`processed_webhook_events` holds Stripe event IDs only, with no user reference.

## Outside the database

| System | Action | Reason |
|---|---|---|
| Stripe | Cancel the subscription immediately. The customer record and its invoices stay in Stripe. | UK tax records (HMRC generally requires 6 years). Stripe is the record holder, so nothing local needs keeping for tax. |
| Supabase Storage (`avatars`, public bucket) | Delete `avatars/{user_id}/*` | Profile photo |
| Supabase Auth (`auth.users`) | Delete the user found by email (matched by email, not ID; 54 of 54 Auth users match a `users.email`) | Sign-in identity, including the Google account link |
| PostHog | **Manual step.** No PostHog personal API key is configured, so the purge logs `posthog_person_delete_manual` with the user ID. Delete the person in PostHog → Persons. | Analytics person profile |
| Redis | Refresh token revoked at request; rate-limit keys expire on their TTL | Session state |
| Supabase database backups | Not altered; deleted data ages out with the backup window | Backups cannot be edited row by row |
| Sentry, Railway and Resend logs | Not altered; they contain user IDs or email addresses in log lines and age out on each provider's retention | Operational logs |
