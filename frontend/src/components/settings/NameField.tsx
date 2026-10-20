'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { validateDisplayName, cleanDisplayName, apiErrorMessage } from '@/lib/names'

/** Display name with an inline editor, for Settings > Profile. */
export default function NameField({ displayName }: { displayName: string }) {
  const refreshUser = useAuthStore(s => s.refreshUser)
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(displayName)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function save(e: React.FormEvent) {
    e.preventDefault()
    const problem = validateDisplayName(value)
    if (problem) { setError(problem); return }
    setSaving(true)
    setError(null)
    try {
      await api.auth.updateMe({ display_name: cleanDisplayName(value) })
      await refreshUser()
      setEditing(false)
    } catch (err) {
      setError(apiErrorMessage(err, "That didn't save. Please try again."))
    } finally {
      setSaving(false)
    }
  }

  if (!editing) {
    return (
      <div className="flex items-center gap-2">
        <p className="text-[#E8E2DC] text-base font-medium">{displayName || 'No name set'}</p>
        <button
          type="button"
          onClick={() => { setValue(displayName); setEditing(true) }}
          className="text-[#F59E0B]/70 hover:text-[#F59E0B] text-xs"
        >
          {displayName ? 'Edit' : 'Add name'}
        </button>
      </div>
    )
  }

  return (
    <form onSubmit={save} className="mb-1">
      <label htmlFor="settings-name" className="sr-only">What should we call you?</label>
      <div className="flex gap-2">
        <input
          id="settings-name"
          type="text"
          value={value}
          onChange={e => { setValue(e.target.value); setError(null) }}
          placeholder="What should we call you?"
          autoComplete="given-name"
          maxLength={50}
          autoFocus
          className="input-base h-9 text-sm flex-1 min-w-0"
        />
        <button type="submit" disabled={saving} className="btn btn-primary h-9 px-3 text-sm">
          {saving ? 'Saving…' : 'Save'}
        </button>
        <button type="button" onClick={() => { setEditing(false); setError(null) }} className="btn btn-ghost h-9 px-3 text-sm">
          Cancel
        </button>
      </div>
      {error && <p className="text-[#F87171] text-xs mt-1">{error}</p>}
    </form>
  )
}
