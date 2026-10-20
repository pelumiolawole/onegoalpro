'use client'

import { useEffect, useState } from 'react'
import { api, TimeBudget } from '@/lib/api'
import TimeBudgetPicker, { MINUTE_OPTIONS, TIME_OPTIONS } from '@/components/TimeBudgetPicker'

/** Settings: change daily minutes and preferred time at any time. */
export default function TimeBudgetSection() {
  const [budget, setBudget] = useState<TimeBudget | null>(null)
  const [editing, setEditing] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.profile.getTimeBudget().then(setBudget).catch(() => setBudget({ daily_minutes: null, preferred_time: null }))
  }, [])

  if (!budget) return null

  const minutesLabel = MINUTE_OPTIONS.find(o => o.value === budget.daily_minutes)?.label
  const timeLabel = TIME_OPTIONS.find(o => o.value === budget.preferred_time)?.label

  return (
    <section className="bg-[#141210] border border-white/5 rounded-2xl p-6">
      <h2 className="text-lg font-medium text-[#F5F1ED] mb-1">Daily time</h2>
      <p className="text-[#5C524A] text-sm mb-5">Your tasks are sized to this, starting with your next task.</p>
      {editing || !budget.daily_minutes ? (
        <TimeBudgetPicker
          compact
          initialMinutes={budget.daily_minutes}
          initialTime={budget.preferred_time}
          onSaved={(daily_minutes, preferred_time) => {
            setBudget({ daily_minutes, preferred_time })
            setEditing(false)
            setSaved(true)
          }}
        />
      ) : (
        <div className="flex items-center justify-between gap-4">
          <p className="text-[#C4BBB5] text-sm">
            {minutesLabel} a day{timeLabel ? `, ${timeLabel.toLowerCase()}` : ''}
            {saved && <span className="text-[#5C524A] ml-2">Saved</span>}
          </p>
          <button type="button" onClick={() => { setEditing(true); setSaved(false) }} className="text-[#F59E0B]/70 hover:text-[#F59E0B] text-sm">
            Change
          </button>
        </div>
      )}
    </section>
  )
}
