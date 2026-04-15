'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { api } from '@/lib/api'

export default function PreviewPage() {
  const router = useRouter()
  const [strategy, setStrategy] = useState<any>(null)
  const [loading, setLoading]   = useState(true)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    api.onboarding.previewStrategy()
      .then(setStrategy)
      .catch(() => router.push('/goal-setup'))
      .finally(() => setLoading(false))
  }, [])

  async function handleConfirm() {
    setConfirming(true)
    try {
      await api.onboarding.confirmGoal()
      router.push('/activate')
    } catch {
      setConfirming(false)
    }
  }

  if (loading) return <LoadingSkeleton />

  const { goal, objectives, identity_traits } = strategy || {}

  return (
    <div className="max-w-2xl mx-auto w-full">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>

        <h1 className="font-display text-4xl text-[#1A1A1A] mb-2">
          Your strategy
        </h1>
        <p className="text-[#9E9D9B] mb-8">
          This is what the AI built from your interview. Read it carefully — you can
          go back and change your goal if it doesn't land right.
        </p>

        {/* Goal statement */}
        <div className="bg-[#F8F8F7] border border-[#009e97]/20 rounded-2xl p-6 mb-5">
          <p className="text-[#009e97] text-xs uppercase tracking-widest mb-3 font-mono">
            Your One Goal
          </p>
          <p className="font-display text-xl text-[#1A1A1A] leading-snug mb-4">
            {goal?.statement}
          </p>
          {goal?.why && (
            <p className="text-[#9E9D9B] text-sm italic border-t border-black/5 pt-4">
              "{goal.why}"
            </p>
          )}
        </div>

        {/* Required identity */}
        {goal?.required_identity && (
          <div className="bg-[#F0EFED] border border-black/5 rounded-2xl p-5 mb-5">
            <p className="text-[#C8C7C5] text-xs uppercase tracking-widest mb-2 font-mono">
              Who you must become
            </p>
            <p className="text-[#5C5B57] leading-relaxed">
              {goal.required_identity}
            </p>
          </div>
        )}

        {/* Identity traits */}
        {identity_traits?.length > 0 && (
          <div className="mb-5">
            <p className="text-[#C8C7C5] text-xs uppercase tracking-widest mb-3 font-mono">
              Identity traits to develop
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {identity_traits.map((trait: any, i: number) => (
                <motion.div
                  key={trait.name}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                  className="bg-[#F8F8F7] border border-black/5 rounded-xl p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[#28271F] font-medium capitalize">{trait.name}</span>
                    <span className="text-[#C8C7C5] text-xs font-mono">
                      {trait.current_score.toFixed(0)} → {trait.target_score.toFixed(0)}
                    </span>
                  </div>
                  <div className="h-1.5 bg-[#E5E4E2] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#009e97] rounded-full transition-all"
                      style={{ width: `${(trait.current_score / 10) * 100}%` }}
                    />
                  </div>
                  <p className="text-[#C8C7C5] text-xs mt-2">{trait.category}</p>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Objectives */}
        {objectives?.length > 0 && (
          <div className="mb-8">
            <p className="text-[#C8C7C5] text-xs uppercase tracking-widest mb-3 font-mono">
              Objectives — in sequence
            </p>
            <div className="space-y-3">
              {objectives.map((obj: any, i: number) => (
                <motion.div
                  key={obj.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + i * 0.08 }}
                  className="flex gap-4 bg-[#F8F8F7] border border-black/5 rounded-xl p-4"
                >
                  <div className="w-7 h-7 rounded-full bg-[#E5E4E2] border border-black/10 flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-[#C8C7C5] text-xs font-mono">{i + 1}</span>
                  </div>
                  <div>
                    <p className="text-[#28271F] font-medium mb-1">{obj.title}</p>
                    <p className="text-[#9E9D9B] text-sm">{obj.description}</p>
                    {obj.estimated_weeks && (
                      <p className="text-[#C8C7C5] text-xs mt-2 font-mono">~{obj.estimated_weeks} weeks</p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 border-t border-black/5 pt-6">
          <button
            onClick={handleConfirm}
            disabled={confirming}
            className="btn btn-primary flex-1 h-12 text-base"
          >
            {confirming ? 'Confirming…' : 'This is my strategy — activate'}
          </button>
          <button
            onClick={() => router.push('/goal-setup')}
            className="btn btn-ghost h-12"
          >
            Change my goal
          </button>
        </div>

      </motion.div>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="max-w-2xl mx-auto w-full space-y-4 animate-pulse">
      <div className="h-10 bg-[#F0EFED] rounded-xl w-1/2" />
      <div className="h-32 bg-[#F0EFED] rounded-2xl" />
      <div className="h-20 bg-[#F0EFED] rounded-2xl" />
      <div className="grid grid-cols-2 gap-3">
        {[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-[#F0EFED] rounded-xl" />)}
      </div>
    </div>
  )
}
