'use client'

/**
 * "Report" link plus bottom sheet for AI-generated content (coach replies,
 * interview messages, daily tasks). Required by Google Play's AI-generated
 * content policy. Sends the reported text to POST /reports/ai-content.
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '@/lib/api'

type Source = 'coach' | 'interview' | 'task'
type Reason = 'offensive' | 'inaccurate' | 'inappropriate_advice' | 'other'

const REASONS: { value: Reason; label: string }[] = [
  { value: 'offensive', label: 'Offensive or harmful' },
  { value: 'inaccurate', label: 'Inaccurate' },
  { value: 'inappropriate_advice', label: 'Inappropriate advice' },
  { value: 'other', label: 'Other' },
]

interface Props {
  source: Source
  content: string
  referenceId?: string | null
  label?: string
  className?: string
}

export default function ReportContent({ source, content, referenceId, label = 'Report', className = '' }: Props) {
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState<Reason | null>(null)
  const [details, setDetails] = useState('')
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function close() {
    setOpen(false)
    setReason(null)
    setDetails('')
    setError(null)
  }

  async function submit() {
    if (!reason || sending) return
    setSending(true)
    setError(null)
    try {
      await api.reports.aiContent({
        source,
        reason,
        content,
        reference_id: referenceId || undefined,
        details: reason === 'other' && details.trim() ? details.trim().slice(0, 1000) : undefined,
      })
      setSent(true)
      close()
    } catch {
      setError("That didn't send. Please try again.")
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      {sent ? (
        <span className={`text-[11px] text-[#5C524A] ${className}`}>Thanks, we'll review this.</span>
      ) : (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className={`text-[11px] text-[#3D3630] hover:text-[#7A6E65] transition-colors ${className}`}
        >
          {label}
        </button>
      )}

      <AnimatePresence>
        {open && (
          <motion.div
            className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={close}
          >
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label="Report this content"
              className="w-full sm:max-w-md bg-[#141210] border border-white/10 rounded-t-2xl sm:rounded-2xl p-5 pb-8 sm:pb-5"
              initial={{ y: 40 }}
              animate={{ y: 0 }}
              exit={{ y: 40 }}
              onClick={e => e.stopPropagation()}
            >
              <h2 className="text-[#F5F1ED] text-base mb-1">Report this content</h2>
              <p className="text-[#7A6E65] text-sm mb-4">What's wrong with it?</p>

              <div className="space-y-2 mb-4">
                {REASONS.map(r => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setReason(r.value)}
                    className={`w-full text-left px-4 py-3 rounded-xl border text-sm transition-colors ${
                      reason === r.value
                        ? 'border-[#F59E0B]/40 bg-[#F59E0B]/10 text-[#F5F1ED]'
                        : 'border-white/5 bg-[#1E1B18] text-[#C4BBB5] hover:border-white/15'
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>

              {reason === 'other' && (
                <textarea
                  value={details}
                  onChange={e => setDetails(e.target.value)}
                  maxLength={1000}
                  rows={3}
                  placeholder="Tell us more (optional)"
                  className="input-base text-sm w-full mb-4 resize-none"
                />
              )}

              {error && <p className="text-[#F87171] text-sm mb-3">{error}</p>}

              <div className="flex gap-3">
                <button type="button" onClick={submit} disabled={!reason || sending} className="btn btn-primary flex-1 h-11">
                  {sending ? 'Sending…' : 'Send report'}
                </button>
                <button type="button" onClick={close} className="btn btn-ghost h-11 px-4">
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
