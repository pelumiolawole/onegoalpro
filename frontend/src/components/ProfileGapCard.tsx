'use client'

/**
 * One-time dashboard card for facts the product needs but the user hasn't
 * given yet. Shows one card at a time and can't be dismissed: it goes away
 * once the user answers.
 */

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { validateDisplayName, cleanDisplayName, apiErrorMessage } from '@/lib/names'
import TimeBudgetPicker from '@/components/TimeBudgetPicker'

export default function ProfileGapCard() {
  const user = useAuthStore(s => s.user)
  const refreshUser = useAuthStore(s => s.refreshUser)

  // null = not checked yet; only fetched once the name is answered (one card at a time)
  const [needsTime, setNeedsTime] = useState<boolean | null>(null)
  const hasName = !!(user?.display_name || '').trim()

  useEffect(() => {
    if (!user || !hasName || needsTime !== null) return
    api.profile.getTimeBudget()
      .then(b => setNeedsTime(!b.daily_minutes || !b.preferred_time))
      .catch(() => setNeedsTime(false))
  }, [user, hasName, needsTime])

  if (!user) return null
  if (!hasName) return <NameCard onSaved={refreshUser} />
  if (needsTime) return <TimeCard onSaved={() => setNeedsTime(false)} />
  return null
}

function TimeCard({ onSaved }: { onSaved: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-6 rounded-2xl border border-[#F59E0B]/20 bg-[#141210] p-5"
    >
      <p className="font-display text-xl text-[#F5F1ED] mb-1">Your daily time</p>
      <p className="text-[#7A6E65] text-sm mb-4">Your tasks will be sized to fit. Pick what's true on a normal day.</p>
      <TimeBudgetPicker compact onSaved={onSaved} />
    </motion.div>
  )
}

function NameCard({ onSaved }: { onSaved: () => Promise<void> }) {
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function save(e: React.FormEvent) {
    e.preventDefault()
    const problem = validateDisplayName(name)
    if (problem) { setError(problem); return }
    setSaving(true)
    setError(null)
    try {
      await api.auth.updateMe({ display_name: cleanDisplayName(name) })
      await onSaved()
    } catch (err) {
      setError(apiErrorMessage(err, "That didn't save. Please try again."))
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.form
      onSubmit={save}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-6 rounded-2xl border border-[#F59E0B]/20 bg-[#141210] p-5"
    >
      <label htmlFor="gap-name" className="block font-display text-xl text-[#F5F1ED] mb-1">
        What should we call you?
      </label>
      <p className="text-[#7A6E65] text-sm mb-4">Your first name, or the name you go by. Your coach will use it.</p>
      <div className="flex gap-3">
        <input
          id="gap-name"
          type="text"
          value={name}
          onChange={e => { setName(e.target.value); setError(null) }}
          autoComplete="given-name"
          maxLength={50}
          className="input-base flex-1"
        />
        <button type="submit" disabled={saving || !name.trim()} className="btn btn-primary h-11 px-5">
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
      {error && <p className="text-[#F87171] text-sm mt-2">{error}</p>}
    </motion.form>
  )
}
