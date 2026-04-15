'use client'

import { motion } from 'framer-motion'

interface DayData {
  date: string
  completed: boolean
  reflected: boolean
  score: number | null
}

export function WeekGrid({ days }: { days: DayData[] }) {
  const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

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
      completed: data?.completed ?? false,
      reflected: data?.reflected ?? false,
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
            {day.completed && <span className="text-[#009e97] text-xs">✓</span>}
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

export default WeekGrid
