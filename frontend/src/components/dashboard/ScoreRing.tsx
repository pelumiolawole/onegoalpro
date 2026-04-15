'use client'

import { motion } from 'framer-motion'

// ── Score Ring ─────────────────────────────────────────────────────────────

interface ScoreRingProps {
  label: string
  value: number     // 0–100
  primary?: boolean
}

export default function ScoreRing({ label, value, primary }: ScoreRingProps) {
  const r    = 28
  const circ = 2 * Math.PI * r
  const dash = (value / 100) * circ

  return (
    <div className={`bg-[#F8F8F7] border rounded-2xl p-4 flex flex-col items-center gap-2 ${
      primary ? 'border-[#009e97]/20' : 'border-black/5'
    }`}>
      <p className="text-[#C8C7C5] text-xs uppercase tracking-wider font-mono text-center">
        {label}
      </p>
      <div className="relative w-16 h-16">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 72 72">
          {/* Track */}
          <circle
            cx="36" cy="36" r={r}
            fill="none"
            stroke="#F0EFED"
            strokeWidth="4"
          />
          {/* Progress */}
          <motion.circle
            cx="36" cy="36" r={r}
            fill="none"
            stroke={primary ? '#009e97' : '#C8C7C5'}
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={circ}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: circ - dash }}
            transition={{ duration: 1, delay: 0.2, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`font-mono text-sm font-medium ${primary ? 'text-[#009e97]' : 'text-[#5C5B57]'}`}>
            {value.toFixed(0)}
          </span>
        </div>
      </div>
    </div>
  )
}

// ── Week Grid ──────────────────────────────────────────────────────────────

interface DayData {
  date: string
  completed: boolean
  reflected: boolean
  score: number | null
}

export function WeekGrid({ days }: { days: DayData[] }) {
  const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  // Build a 7-day array ending today
  const today = new Date()
  const grid = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today)
    d.setDate(today.getDate() - (6 - i))
    const dateStr = d.toISOString().split('T')[0]
    const data = days.find(day => day.date === dateStr)
    return {
      label: dayLabels[d.getDay()],
      dateStr,
      isToday: i === 6,
      ...data,
    }
  })

  return (
    <div className="grid grid-cols-7 gap-1.5">
      {grid.map((day, i) => (
        <div key={day.dateStr} className="flex flex-col items-center gap-1.5">
          <span className="text-[#C8C7C5] text-[10px] font-mono">{day.label}</span>
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.04 }}
            className={`w-8 h-8 rounded-lg flex items-center justify-center relative ${
              day.completed
                ? 'bg-[#009e97]/20 border border-[#009e97]/30'
                : day.isToday
                ? 'bg-[#F0EFED] border border-black/10 border-dashed'
                : 'bg-[#FFFFFF] border border-black/5'
            }`}
          >
            {day.completed && (
              <span className="text-[#009e97] text-xs">✓</span>
            )}
            {day.reflected && day.completed && (
              <div className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-[#009e97]" />
            )}
            {day.isToday && !day.completed && (
              <div className="w-1.5 h-1.5 rounded-full bg-[#C8C7C5]" />
            )}
          </motion.div>
        </div>
      ))}
    </div>
  )
}
