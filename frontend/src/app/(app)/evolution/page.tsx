'use client'

import { useState, useEffect, useRef, useMemo } from 'react'
import useSWR from 'swr'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

// ─── Chapter system ───────────────────────────────────────────────────────────

const CHAPTERS = [
  { id: 1, name: 'The Awakening',     range: [0, 13]  as [number,number], desc: 'You chose to begin. That alone sets you apart.' },
  { id: 2, name: 'The Foundation',    range: [14, 29] as [number,number], desc: 'The habits of your new identity are taking root.' },
  { id: 3, name: 'The Strengthening', range: [30, 59] as [number,number], desc: 'Consistency is rewriting who you are at the core.' },
  { id: 4, name: 'The Embodiment',    range: [60, 89] as [number,number], desc: 'You are no longer becoming. You are being.' },
  { id: 5, name: 'The Becoming',      range: [90, Infinity] as [number,number], desc: 'This is who you are now. Own it.' },
]

const TRAIT_LEVELS = ['Dormant', 'Awakening', 'Forming', 'Strengthening', 'Embodied']

function getChapter(daysActive: number) {
  return CHAPTERS.find(c => daysActive >= c.range[0] && daysActive <= c.range[1]) || CHAPTERS[0]
}

function getTraitLevel(pct: number) {
  if (pct < 20) return 0
  if (pct < 40) return 1
  if (pct < 60) return 2
  if (pct < 80) return 3
  return 4
}

function getNextChapter(current: typeof CHAPTERS[0]) {
  const idx = CHAPTERS.indexOf(current)
  return idx < CHAPTERS.length - 1 ? CHAPTERS[idx + 1] : null
}

function daysToNextChapter(daysActive: number, chapter: typeof CHAPTERS[0]) {
  if (chapter.range[1] === Infinity) return 0
  return Math.max(0, chapter.range[1] + 1 - daysActive)
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface Trait { name: string; progress_pct: number; trend: string }
interface Task {
  id: string; date: string; title: string; identity_focus: string
  status: string; reflection_depth: number | null
  reflection_sentiment: string | null; reflection_insight: string | null
}

// ─── Animated score ring ──────────────────────────────────────────────────────

function ScoreRing({ value }: { value: number }) {
  const rafRef = useRef<number>(0)
  const [dotAngle, setDotAngle] = useState(-90)
  const r = 64
  const circ = 2 * Math.PI * r
  const filled = (value / 100) * circ
  const targetAngle = (value / 100) * 360 - 90

  useEffect(() => {
    let current = -90
    const step = () => {
      current += 2
      if (current < targetAngle) {
        setDotAngle(current)
        rafRef.current = requestAnimationFrame(step)
      } else {
        setDotAngle(targetAngle)
      }
    }
    const timer = setTimeout(() => { rafRef.current = requestAnimationFrame(step) }, 400)
    return () => { clearTimeout(timer); cancelAnimationFrame(rafRef.current) }
  }, [targetAngle])

  const dotX = 90 + r * Math.cos((dotAngle * Math.PI) / 180)
  const dotY = 90 + r * Math.sin((dotAngle * Math.PI) / 180)

  return (
    <div className="relative w-44 h-44 mx-auto">
      <svg width="180" height="180" viewBox="0 0 180 180" className="absolute inset-0">
        <defs>
          <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#E8A83E" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#C8693E" stopOpacity="0.7" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="dotGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <circle cx="90" cy="90" r="82" fill="none" stroke="rgba(200,150,62,0.06)" strokeWidth="1" strokeDasharray="3 9" />
        <circle cx="90" cy="90" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
        <motion.circle
          cx="90" cy="90" r={r}
          fill="none" stroke="url(#ringGrad)" strokeWidth="10" strokeLinecap="round"
          strokeDasharray={`${circ}`}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - filled }}
          transition={{ duration: 1.6, delay: 0.3, ease: 'easeOut' }}
          transform="rotate(-90 90 90)"
          filter="url(#glow)"
        />
        <motion.circle
          cx={dotX} cy={dotY} r="5" fill="#F59E0B"
          filter="url(#dotGlow)"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className="text-[#F5ECD7] text-5xl font-bold leading-none"
          style={{ fontFamily: "'Cormorant Garamond', serif", textShadow: '0 0 30px rgba(200,150,62,0.4)' }}
          initial={{ opacity: 0, scale: 0.7 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4, type: 'spring', stiffness: 200 }}
        >
          {value}
        </motion.span>
        <span className="text-[#7A6040] text-[10px] font-mono tracking-[0.15em] uppercase mt-1">Transform</span>
      </div>
    </div>
  )
}

// ─── Chapter card ─────────────────────────────────────────────────────────────

function ChapterCard({ chapter, daysActive }: { chapter: typeof CHAPTERS[0]; daysActive: number }) {
  const next = getNextChapter(chapter)
  const daysLeft = daysToNextChapter(daysActive, chapter)
  const chapterProgress = chapter.range[1] === Infinity
    ? 100
    : Math.min(100, Math.round(((daysActive - chapter.range[0]) / (chapter.range[1] - chapter.range[0] + 1)) * 100))

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
      className="rounded-2xl p-5 border"
      style={{
        background: 'linear-gradient(135deg, rgba(200,150,62,0.1) 0%, rgba(20,12,5,0.95) 100%)',
        borderColor: 'rgba(200,150,62,0.25)',
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-[#C8963E] text-[10px] font-mono tracking-[0.18em] uppercase">
          Chapter {chapter.id} of {CHAPTERS.length}
        </span>
        {next && daysLeft > 0 && (
          <span className="text-[#5C4020] text-[10px] font-mono">
            {daysLeft}d to {next.name}
          </span>
        )}
      </div>
      <h2 style={{ fontFamily: "'Cormorant Garamond', serif" }} className="text-2xl text-[#F5ECD7] font-bold mb-1.5">
        {chapter.name}
      </h2>
      <p className="text-[#8B6040] text-sm italic mb-4 leading-relaxed" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
        {chapter.desc}
      </p>
      <div className="space-y-1.5">
        <div className="flex justify-between">
          <span className="text-[#5C4020] text-[10px] font-mono uppercase tracking-widest">Progress</span>
          <span className="text-[#C8963E] text-[10px] font-mono">{chapterProgress}%</span>
        </div>
        <div className="h-1.5 bg-[#1A0F05] rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: 'linear-gradient(90deg, #C8963E, #E8A83E)' }}
            initial={{ width: 0 }}
            animate={{ width: `${chapterProgress}%` }}
            transition={{ duration: 1.2, delay: 0.5, ease: 'easeOut' }}
          />
        </div>
        <div className="flex gap-1.5 mt-2">
          {CHAPTERS.map((c, i) => (
            <div key={c.id} className="flex-1 h-1 rounded-full" style={{
              background: i < chapter.id - 1
                ? 'linear-gradient(90deg, #C8963E, #E8A83E)'
                : i === chapter.id - 1
                  ? 'rgba(200,150,62,0.4)'
                  : 'rgba(255,255,255,0.05)',
            }} />
          ))}
        </div>
      </div>
    </motion.div>
  )
}

// ─── Identity arc ─────────────────────────────────────────────────────────────

function IdentityArc({ first, latest }: { first: Task | null; latest: Task | null }) {
  if (!first) return null
  const daysBetween = first && latest && first.id !== latest.id
    ? Math.round((new Date(latest!.date).getTime() - new Date(first.date).getTime()) / 86400000)
    : 0
  const fmt = (d: string) => new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="rounded-2xl border overflow-hidden"
      style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(15,8,3,0.9)' }}
    >
      <div className="px-5 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
        <p className="text-[#5C4020] text-[10px] font-mono tracking-[0.18em] uppercase">Who you were → Who you are</p>
      </div>
      <div className="p-5 space-y-4">
        <div className="pl-3 border-l-2" style={{ borderColor: 'rgba(200,150,62,0.2)' }}>
          <p className="text-[#3D2810] text-[10px] font-mono uppercase tracking-widest mb-1.5">Day 1 · {fmt(first.date)}</p>
          <p className="text-[#7A6040] text-sm italic leading-relaxed" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {first.identity_focus || first.title}
          </p>
        </div>
        {daysBetween > 0 && (
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px" style={{ background: 'linear-gradient(90deg, transparent, rgba(200,150,62,0.3), transparent)' }} />
            <span className="text-[#C8963E] text-xs font-mono shrink-0">{daysBetween} days</span>
            <div className="flex-1 h-px" style={{ background: 'linear-gradient(90deg, transparent, rgba(200,150,62,0.3), transparent)' }} />
          </div>
        )}
        {latest && latest.id !== first.id && (
          <div className="pl-3 border-l-2" style={{ borderColor: 'rgba(200,150,62,0.6)' }}>
            <p className="text-[#C8963E] text-[10px] font-mono uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#E8A83E] inline-block" style={{ animation: 'pulse 2s ease infinite' }} />
              Today · {fmt(latest.date)}
            </p>
            <p className="text-[#F5ECD7] text-sm italic leading-relaxed" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
              {latest.identity_focus || latest.title}
            </p>
          </div>
        )}
      </div>
    </motion.div>
  )
}

// ─── Coach witness ────────────────────────────────────────────────────────────

function CoachWitness({ tasks }: { tasks: Task[] }) {
  const insight = tasks.find(t => t.reflection_insight && t.status === 'completed')
  if (!insight) return null
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 }}
      className="rounded-2xl border p-5"
      style={{ background: 'linear-gradient(135deg, rgba(20,12,5,0.98), rgba(30,18,8,0.95))', borderColor: 'rgba(200,150,62,0.2)' }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0"
          style={{
            background: 'radial-gradient(circle, rgba(200,150,62,0.35), rgba(200,150,62,0.08))',
            border: '1px solid rgba(200,150,62,0.4)',
            boxShadow: '0 0 16px rgba(200,150,62,0.2)',
            color: '#E8A83E',
          }}
        >◉</div>
        <div>
          <p className="text-[#C8963E] text-[10px] font-mono tracking-[0.15em] uppercase">Coach Witness</p>
          <p className="text-[#5C4020] text-[9px] font-mono">
            {new Date(insight.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
          </p>
        </div>
      </div>
      <p className="text-[#C4BBB5] text-sm italic leading-[1.75]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
        "{insight.reflection_insight}"
      </p>
    </motion.div>
  )
}

// ─── Trait mastery ────────────────────────────────────────────────────────────

function TraitMastery({ traits }: { traits: Trait[] }) {
  const [hovered, setHovered] = useState<string | null>(null)
  if (!traits.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="rounded-2xl border overflow-hidden"
      style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(15,8,3,0.9)' }}
    >
      <div className="px-5 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
        <p className="text-[#5C4020] text-[10px] font-mono tracking-[0.18em] uppercase">Identity traits · Mastery</p>
      </div>
      <div className="p-5 space-y-5">
        {traits.map((trait, i) => {
          const level = getTraitLevel(trait.progress_pct)
          const isHovered = hovered === trait.name
          const pctToNext = level < 4
            ? Math.round(((trait.progress_pct - level * 20) / 20) * 100)
            : 100
          return (
            <motion.div
              key={trait.name}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 + i * 0.08 }}
              onMouseEnter={() => setHovered(trait.name)}
              onMouseLeave={() => setHovered(null)}
              onTouchStart={() => setHovered(t => t === trait.name ? null : trait.name)}
              className="cursor-default"
            >
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[#C4BBB5] text-sm capitalize" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                    {trait.name}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border" style={{
                    color: level >= 3 ? '#E8A83E' : level >= 2 ? '#C8963E' : '#5C4020',
                    borderColor: level >= 3 ? 'rgba(232,168,62,0.3)' : 'rgba(255,255,255,0.06)',
                    background: level >= 3 ? 'rgba(232,168,62,0.08)' : 'transparent',
                  }}>
                    {TRAIT_LEVELS[level]}
                  </span>
                </div>
                <span className={`text-xs font-mono flex items-center gap-1 ${
                  trait.trend === 'growing' ? 'text-[#4ADE80]' :
                  trait.trend === 'declining' ? 'text-[#F87171]' : 'text-[#5C524A]'
                }`}>
                  {trait.trend === 'growing' ? '↑' : trait.trend === 'declining' ? '↓' : '→'}
                  {trait.progress_pct.toFixed(0)}%
                </span>
              </div>
              <div className="relative h-2 bg-[#1A0F05] rounded-full overflow-hidden">
                {[20,40,60,80].map(mark => (
                  <div key={mark} className="absolute top-0 w-px h-full" style={{ left: `${mark}%`, background: 'rgba(255,255,255,0.08)' }} />
                ))}
                <motion.div
                  className="h-full rounded-full"
                  style={{
                    background: trait.trend === 'growing'
                      ? 'linear-gradient(90deg, #C8963E88, #E8A83E)'
                      : trait.trend === 'declining' ? 'rgba(248,113,113,0.4)' : 'rgba(200,150,62,0.3)',
                    boxShadow: trait.trend === 'growing' ? '0 0 8px rgba(232,168,62,0.4)' : 'none',
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${trait.progress_pct}%` }}
                  transition={{ duration: 1.2, delay: 0.3 + i * 0.1, ease: 'easeOut' }}
                />
              </div>
              <AnimatePresence>
                {isHovered && level < 4 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden mt-2"
                  >
                    <div className="text-xs py-2 px-3 rounded-lg italic"
                      style={{ color: 'rgba(200,150,62,0.7)', background: 'rgba(200,150,62,0.06)', borderLeft: '2px solid rgba(200,150,62,0.3)' }}>
                      {pctToNext}% to {TRAIT_LEVELS[level + 1]} — keep reflecting and showing up
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </div>
    </motion.div>
  )
}

// ─── Depth arc ────────────────────────────────────────────────────────────────

function DepthArc({ tasks }: { tasks: Task[] }) {
  const data = useMemo(() => {
    const byWeek: Record<string, number[]> = {}
    tasks.forEach(t => {
      if (!t.reflection_depth) return
      const d = new Date(t.date)
      const mon = new Date(d)
      mon.setDate(d.getDate() - ((d.getDay() + 6) % 7))
      const key = mon.toISOString().slice(0, 10)
      if (!byWeek[key]) byWeek[key] = []
      byWeek[key].push(t.reflection_depth)
    })
    return Object.entries(byWeek)
      .sort(([a],[b]) => a.localeCompare(b))
      .map(([week, depths]) => ({ week, avg: depths.reduce((s,d) => s+d,0) / depths.length }))
  }, [tasks])

  if (data.length < 1) return null

  const W = 300; const H = 80; const pad = 12; const max = 10
  const xs = data.length === 1
    ? [pad, W - pad]
    : data.map((_,i) => pad + (i / (data.length-1)) * (W - pad*2))
  const vals = data.length === 1 ? [data[0], data[0]] : data
  const ys = vals.map(d => H - pad - ((d.avg / max) * (H - pad*2)))
  const pathD = xs.map((x,i) => `${i===0?'M':'L'} ${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(' ')
  const fillD = `${pathD} L ${xs[xs.length-1].toFixed(1)} ${H} L ${xs[0].toFixed(1)} ${H} Z`
  const rising = data.length > 1 && data[data.length-1].avg > data[0].avg

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.18 }}
      className="rounded-2xl border overflow-hidden"
      style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(15,8,3,0.9)' }}
    >
      <div className="px-5 py-4 border-b flex items-center justify-between" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
        <p className="text-[#5C4020] text-[10px] font-mono tracking-[0.18em] uppercase">Reflection depth</p>
        <span className="text-[10px] font-mono" style={{ color: rising ? '#4ADE80' : '#5C524A' }}>
          {rising ? '↑ Going deeper' : '→ Building'}
        </span>
      </div>
      <div className="p-5">
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height: 80 }} className="overflow-visible">
          <defs>
            <linearGradient id="dFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#E8A83E" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#E8A83E" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="dLine" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#C8963E" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#E8A83E" stopOpacity="1" />
            </linearGradient>
          </defs>
          <path d={fillD} fill="url(#dFill)" />
          <motion.path d={pathD} fill="none" stroke="url(#dLine)" strokeWidth="2" strokeLinecap="round"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 1.4, delay: 0.4, ease: 'easeInOut' }}
          />
          {xs.map((x,i) => (
            <motion.circle key={i} cx={x} cy={ys[i]} r={i===xs.length-1?5:3}
              fill={i===xs.length-1?'#E8A83E':'#C8963E'}
              initial={{ scale: 0 }} animate={{ scale: 1 }}
              transition={{ delay: 0.8 + i*0.06 }}
              style={i===xs.length-1?{filter:'drop-shadow(0 0 6px rgba(232,168,62,0.8))'}:{}}
            />
          ))}
        </svg>
        <div className="flex justify-between mt-3">
          <span className="text-[#3D2010] text-[9px] font-mono">
            {new Date(data[0].week).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
          </span>
          <span className="text-[9px] font-mono" style={{ color: 'rgba(200,150,62,0.5)' }}>
            Latest: {data[data.length-1].avg.toFixed(1)} / 10
          </span>
          <span className="text-[#3D2010] text-[9px] font-mono">
            {new Date(data[data.length-1].week).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
          </span>
        </div>
        <p className="text-[#3D2010] text-[10px] mt-2 italic">Higher means more honest, more specific answers.</p>
      </div>
    </motion.div>
  )
}

// ─── Milestones ───────────────────────────────────────────────────────────────

function Milestones({ tasks, streak, daysActive }: { tasks: Task[]; streak: number; daysActive: number }) {
  const completed = tasks.filter(t => t.status === 'completed')

  const milestones = useMemo(() => [
    {
      icon: '✦', label: 'First task completed',
      detail: completed[completed.length-1]?.title || 'Your journey began',
      date: completed[completed.length-1]?.date,
      unlocked: completed.length > 0, amber: true,
    },
    {
      icon: '◈', label: 'First honest reflection',
      detail: completed.some(t => t.reflection_depth && t.reflection_depth > 5)
        ? `Depth score: ${completed.find(t => t.reflection_depth && t.reflection_depth > 5)?.reflection_depth?.toFixed(1)}`
        : 'Complete a deep reflection to unlock',
      date: completed.find(t => t.reflection_depth && t.reflection_depth > 5)?.date,
      unlocked: completed.some(t => t.reflection_depth && t.reflection_depth > 5), amber: false,
    },
    {
      icon: '⬡', label: '7 days of showing up',
      detail: daysActive >= 7 || streak >= 7 ? `Achieved · Day ${Math.max(daysActive, 7)}` : `You're on Day ${daysActive} · Unlocks at Day 7`,
      unlocked: daysActive >= 7 || streak >= 7, amber: daysActive >= 7 || streak >= 7,
    },
    {
      icon: '◉', label: 'Identity shift detected',
      detail: completed.some(t => t.reflection_sentiment === 'breakthrough')
        ? 'Your coach witnessed a breakthrough'
        : `Unlocks at Day 14 · You're on Day ${daysActive}`,
      date: completed.find(t => t.reflection_sentiment === 'breakthrough')?.date,
      unlocked: daysActive >= 14 || completed.some(t => t.reflection_sentiment === 'breakthrough'),
      amber: daysActive >= 14,
    },
    ...(daysActive >= 30 ? [{
      icon: '★', label: '30 days of consistency',
      detail: 'A month of identity work. You are not the same person.',
      unlocked: true, amber: true, date: undefined,
    }] : []),
    ...(streak >= 30 ? [{
      icon: '◆', label: `${streak}-day streak`,
      detail: 'Consistency is identity in action.',
      unlocked: true, amber: true, date: undefined,
    }] : []),
  ], [completed, daysActive, streak])

  const unlockedCount = milestones.filter(m => m.unlocked).length
  const lockedCount = milestones.filter(m => !m.unlocked).length

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="rounded-2xl border overflow-hidden"
      style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(15,8,3,0.9)' }}
    >
      <div className="px-5 py-4 border-b flex items-center justify-between" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
        <p className="text-[#5C4020] text-[10px] font-mono tracking-[0.18em] uppercase">Moments earned</p>
        <span className="text-[#C8963E] text-[10px] font-mono">{unlockedCount}/{milestones.length}</span>
      </div>
      <div className="p-5 space-y-3">
        {milestones.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: m.unlocked ? 1 : 0.3, x: 0 }}
            transition={{ delay: 0.15 + i * 0.06 }}
            className="flex items-center gap-3 p-3 rounded-xl"
            style={{
              background: m.unlocked ? m.amber ? 'rgba(200,150,62,0.07)' : 'rgba(255,255,255,0.02)' : 'transparent',
              border: `1px solid ${m.unlocked ? m.amber ? 'rgba(200,150,62,0.2)' : 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.04)'}`,
            }}
          >
            <div className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 text-sm" style={{
              background: m.unlocked && m.amber ? 'radial-gradient(circle, rgba(200,150,62,0.25), rgba(200,150,62,0.05))' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${m.unlocked ? m.amber ? 'rgba(200,150,62,0.4)' : 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.04)'}`,
              color: m.unlocked ? m.amber ? '#E8A83E' : '#7A6E65' : 'rgba(255,255,255,0.15)',
            }}>
              {m.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm" style={{ fontFamily: "'Cormorant Garamond', serif", color: m.unlocked ? m.amber ? '#F5ECD7' : '#C4BBB5' : 'rgba(245,236,215,0.25)' }}>
                {m.label}
              </p>
              <p className="text-[10px] font-mono mt-0.5" style={{ color: m.unlocked ? 'rgba(200,150,62,0.5)' : 'rgba(255,255,255,0.15)' }}>
                {m.detail}
              </p>
              {m.date && (
                <p className="text-[9px] font-mono mt-0.5" style={{ color: 'rgba(200,150,62,0.3)' }}>
                  {new Date(m.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                </p>
              )}
            </div>
            {m.unlocked && <div className="shrink-0 text-[#C8963E] text-xs font-mono">✓</div>}
          </motion.div>
        ))}
        {lockedCount > 0 && (
          <p className="text-center text-[#3D2010] text-[10px] font-mono italic pt-2">
            {lockedCount} more moment{lockedCount > 1 ? 's' : ''} ahead. Keep showing up.
          </p>
        )}
      </div>
    </motion.div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

type Tab = 'journey' | 'traits' | 'milestones'

export default function EvolutionPage() {
  const [tab, setTab] = useState<Tab>('journey')

  const { data: dashboard, isLoading: dashLoading } = useSWR(
    '/progress/dashboard', () => api.progress.getDashboard()
  )
  const { data: historyData, isLoading: histLoading } = useSWR(
    '/tasks/history/90', () => api.tasks.getHistory(90)
  )

  const isLoading = dashLoading || histLoading
  const tasks: Task[] = historyData?.tasks || []
  const traits: Trait[] = dashboard?.top_traits || []
  const score = dashboard?.scores?.transformation ?? 0
  const streak = dashboard?.scores?.streak ?? 0
  const daysActive = dashboard?.scores?.days_active ?? 0

  const chapter = getChapter(daysActive)
  const completed = tasks.filter(t => t.status === 'completed')
  const firstTask = completed.length > 0 ? completed[completed.length - 1] : null
  const latestTask = completed.length > 0 ? completed[0] : null

  const TABS: { id: Tab; label: string }[] = [
    { id: 'journey', label: 'Journey' },
    { id: 'traits', label: 'Traits' },
    { id: 'milestones', label: 'Milestones' },
  ]

  return (
    <div
      className="min-h-screen pb-24 md:pb-8 relative overflow-hidden"
      style={{ background: '#0A0704' }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&display=swap');
        @keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:1} }
      `}</style>

      {/* Ambient orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(200,150,62,0.12) 0%, transparent 70%)' }} />
        <div className="absolute top-1/2 right-0 w-80 h-80 rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(139,96,32,0.15) 0%, transparent 70%)' }} />
        <div className="absolute inset-0 opacity-25"
          style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E")` }} />
      </div>

      <div className="relative z-10 max-w-lg mx-auto px-5 pt-6">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
          <p className="text-[#5C4020] text-[10px] font-mono tracking-[0.2em] uppercase mb-1">Your Evolution</p>
          <h1 className="text-4xl font-bold text-[#F5ECD7] leading-tight"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            Who you're becoming
          </h1>
          {daysActive > 0 && (
            <p className="text-[#3D2010] text-sm mt-1 font-mono">
              {completed.length} tasks completed · {daysActive} days active
            </p>
          )}
        </motion.div>

        {isLoading ? (
          <EvolutionSkeleton />
        ) : completed.length === 0 ? (
          <EmptyEvolution />
        ) : (
          <>
            {/* Score ring */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.05 }}
              className="mb-5 pt-2 pb-5 flex flex-col items-center gap-3"
            >
              <ScoreRing value={score} />
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="text-[#8B6040] text-sm italic text-center"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
              >
                {score < 20 ? 'The foundation is being laid.' :
                 score < 40 ? 'The shift has begun. Keep going.' :
                 score < 60 ? 'You\'re becoming who you said you would.' :
                 score < 80 ? 'The identity is taking hold.' :
                 'This is who you are now.'}
              </motion.p>
            </motion.div>

            {/* Tabs */}
            <div className="flex gap-2 mb-5">
              {TABS.map(t => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className="flex-1 py-2.5 rounded-xl text-[10px] font-mono tracking-[0.12em] uppercase transition-all duration-300"
                  style={{
                    background: tab === t.id ? 'rgba(200,150,62,0.15)' : 'transparent',
                    border: `1px solid ${tab === t.id ? 'rgba(200,150,62,0.35)' : 'rgba(255,255,255,0.06)'}`,
                    color: tab === t.id ? '#E8A83E' : 'rgba(245,236,215,0.35)',
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <AnimatePresence mode="wait">
              <motion.div
                key={tab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
              >
                {tab === 'journey' && (
                  <>
                    <ChapterCard chapter={chapter} daysActive={daysActive} />
                    <IdentityArc first={firstTask} latest={latestTask} />
                    <CoachWitness tasks={tasks} />
                  </>
                )}
                {tab === 'traits' && (
                  <>
                    <motion.div
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                      className="rounded-xl px-4 py-3 text-sm italic leading-relaxed"
                      style={{
                        fontFamily: "'Cormorant Garamond', serif",
                        background: 'rgba(200,150,62,0.05)',
                        border: '1px solid rgba(200,150,62,0.1)',
                        color: 'rgba(200,150,62,0.7)',
                      }}
                    >
                      These are not scores. They are the character being written into you through every choice you make.
                    </motion.div>
                    <TraitMastery traits={traits} />
                    <DepthArc tasks={tasks} />
                  </>
                )}
                {tab === 'milestones' && (
                  <>
                    <motion.div
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                      className="rounded-xl px-4 py-3 text-sm italic leading-relaxed"
                      style={{
                        fontFamily: "'Cormorant Garamond', serif",
                        background: 'rgba(200,150,62,0.05)',
                        border: '1px solid rgba(200,150,62,0.1)',
                        color: 'rgba(200,150,62,0.7)',
                      }}
                    >
                      Every milestone is a moment your future self will point back to.
                    </motion.div>
                    <Milestones tasks={tasks} streak={streak} daysActive={daysActive} />
                  </>
                )}
              </motion.div>
            </AnimatePresence>
          </>
        )}
      </div>
    </div>
  )
}

function EvolutionSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-52 rounded-2xl" style={{ background: 'rgba(255,255,255,0.03)' }} />
      <div className="flex gap-2">
        {[1,2,3].map(i => <div key={i} className="flex-1 h-10 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)' }} />)}
      </div>
      <div className="h-36 rounded-2xl" style={{ background: 'rgba(255,255,255,0.03)' }} />
      <div className="h-48 rounded-2xl" style={{ background: 'rgba(255,255,255,0.03)' }} />
    </div>
  )
}

function EmptyEvolution() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="rounded-2xl p-12 text-center border"
      style={{ border: '1px dashed rgba(200,150,62,0.15)', background: 'rgba(15,8,3,0.8)' }}
    >
      <div className="text-3xl mb-4" style={{ color: 'rgba(200,150,62,0.4)' }}>✦</div>
      <p className="text-lg text-[#5C4020] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
        Your evolution starts here.
      </p>
      <p className="text-[#3D2010] text-sm">
        Complete your first task and come back to watch who you're becoming.
      </p>
    </motion.div>
  )
}