/**
 * Display-name rules, matching backend/core/names.py:
 * trimmed, 1-50 characters, letters plus spaces, hyphens and apostrophes.
 */

export const MAX_NAME_LENGTH = 50

/** Returns an error message, or null if the name is acceptable. */
export function validateDisplayName(value: string): string | null {
  const name = value.trim().replace(/\s+/g, ' ')
  if (!name || !/\p{L}/u.test(name)) return 'Please tell us what to call you.'
  if (name.length > MAX_NAME_LENGTH) return `Please keep your name to ${MAX_NAME_LENGTH} characters or fewer.`
  if (!/^[\p{L}\p{M} '’-]+$/u.test(name)) return 'Please use letters only. Spaces, hyphens and apostrophes are fine.'
  return null
}

export function cleanDisplayName(value: string): string {
  return value.trim().replace(/\s+/g, ' ')
}

/** First word of the display name, or null when there is no usable name. */
export function firstName(displayName: string | null | undefined): string | null {
  const first = (displayName || '').trim().split(/\s+/)[0]
  return first && /\p{L}/u.test(first) ? first : null
}

/** Turn a backend validation error into a readable message. */
export function apiErrorMessage(err: any, fallback: string): string {
  const detail = err?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]) {
    const msg = detail[0].message || detail[0].msg
    if (typeof msg === 'string') return msg.replace(/^Value error, /, '')
  }
  return fallback
}
