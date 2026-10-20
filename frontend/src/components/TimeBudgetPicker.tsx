'use client'

/**
 * "How much time can you give your goal on a typical day?" and "When do you
 * usually have that time?". Used on the activate screen, in Settings and on
 * the dashboard card. Both answers are required; tasks are sized to them.
 */

import { useState } from 'react'
import { api, DailyMinutes, PreferredTime } from '@/lib/api'
import { apiErrorMessage } from '@/lib/names'

export const MINUTE_OPTIONS: { value: DailyMinutes; label: string }[] = [
  { value: 10, label: '10 min' },
  { value: 20, label: '20 min' },
  { value: 30, label: '30 min' },
  { value: 45, label: '45 min' },
  { value: 60, label: '1 hour+' },
]

export const TIME_OPTIONS: { value: PreferredTime; label: string }[] = [
  { value: 'morning', label: 'Morning' },
  { value: 'midday', label: 'Midday' },
  { value: 'evening', label: 'Evening' },
  { value: 'varies', label: 'It varies' },
]

interface Props {
  initialMinutes?: DailyMinutes | null
  initialTime?: PreferredTime | null
  submitLabel?: string
  onSaved: (minutes: DailyMinutes, time: PreferredTime) => void | Promise<void>
  compact?: boolean
}

export default function TimeBudgetPicker({
  initialMinutes = null, initialTime = null, submitLabel = 'Save', onSaved, compact = false,
}: Props) {
  const [minutes, setMinutes] = useState<DailyMinutes | null>(initialMinutes)
  const [time, setTime] = useState<PreferredTime | null>(initialTime)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save() {
    if (minutes === null || time === null || saving) return
    setSaving(true)
    setError(null)
    try {
      await api.profile.saveTimeBudget({ daily_minutes: minutes, preferred_time: time })
      await onSaved(minutes, time)
    } catch (err) {
      setError(apiErrorMessage(err, "That didn't save. Please try again."))
    } finally {
      setSaving(false)
    }
  }

  const heading = compact ? 'text-sm text-[#C4BBB5] mb-2' : 'text-base text-[#F5F1ED] mb-3'

  return (
    <div className="text-left">
      <fieldset className="mb-5">
        <legend className={heading}>How much time can you give your goal on a typical day?</legend>
        <div role="radiogroup" aria-label="Minutes a day" className="flex flex-wrap gap-2">
          {MINUTE_OPTIONS.map(o => (
            <Choice key={o.value} selected={minutes === o.value} onClick={() => setMinutes(o.value)} label={o.label} />
          ))}
        </div>
      </fieldset>

      <fieldset className="mb-6">
        <legend className={heading}>When do you usually have that time?</legend>
        <div role="radiogroup" aria-label="Time of day" className="flex flex-wrap gap-2">
          {TIME_OPTIONS.map(o => (
            <Choice key={o.value} selected={time === o.value} onClick={() => setTime(o.value)} label={o.label} />
          ))}
        </div>
      </fieldset>

      {error && <p className="text-[#F87171] text-sm mb-3">{error}</p>}

      <button
        type="button"
        onClick={save}
        disabled={minutes === null || time === null || saving}
        className={compact ? 'btn btn-primary h-10 px-5 text-sm' : 'btn btn-primary w-full h-12 text-base'}
      >
        {saving ? 'Saving…' : submitLabel}
      </button>
    </div>
  )
}

function Choice({ selected, onClick, label }: { selected: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onClick}
      className={`px-4 h-10 rounded-xl border text-sm transition-colors ${
        selected
          ? 'border-[#F59E0B]/60 bg-[#F59E0B]/15 text-[#F5F1ED]'
          : 'border-white/10 bg-[#141210] text-[#A09690] hover:border-white/20'
      }`}
    >
      {label}
    </button>
  )
}
