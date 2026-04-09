'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import TextareaAutosize from 'react-textarea-autosize'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { trackEvent } from '@/lib/posthog'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ReinterviewPage() {
  const router = useRouter()
  const { refreshUser } = useAuthStore()

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [phase, setPhase] = useState('tension')
  const [starting, setStarting] = useState(true)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  // On mount: reset interview state on backend, then send the opening message
  useEffect(() => {
    async function init() {
      try {
        await api.onboarding.startReinterview()
        const res = await api.onboarding.sendInterviewMessage("I'm ready to begin my next interview.")
        setMessages([{ role: 'assistant', content: res.message }])
        setPhase(res.phase)
      } catch (err: any) {
        const code = err?.detail?.code
        if (code === 'identity_tier_required') {
          setError('Re-interview is available on The Identity plan.')
        } else if (code === 'goal_not_approaching_completion') {
          setError('Re-interview becomes available when your current goal is approaching completion.')
        } else {
          setError('Something went wrong starting your re-interview. Try again from the dashboard.')
        }
      } finally {
        setStarting(false)
      }
    }
    init()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage() {
    if (!input.trim() || loading) return
    const text = input.trim()
    setInput('')
    setLoading(true)
    const newMessages: Message[] = [...messages, { role: 'user', content: text }]
    setMessages(newMessages)

    try {
      const res = await api.onboarding.sendInterviewMessage(text)

      // Quality gate — keep conversation open if data is too shallow
      if ((res as any).needs_more_depth) {
        setMessages([...newMessages, { role: 'assistant', content: res.message }])
        setPhase(res.phase)
        setLoading(false)
        return
      }

      setMessages([...newMessages, { role: 'assistant', content: res.message }])
      setPhase(res.phase)

      if (res.is_complete) {
        trackEvent('reinterview_completed')
        await refreshUser()
        // Route to goal-setup to define the next goal
        setTimeout(() => router.push('/goal-setup'), 1200)
      }
    } catch (err: any) {
      const isTimeout = err?.name === 'AbortError'
      setMessages([...newMessages, {
        role: 'assistant',
        content: isTimeout
          ? "That took a little longer than usual. Try sending again."
          : "Something went wrong. Try sending that again.",
      }])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // ── Loading state while backend resets interview ───────────

  if (starting) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 rounded-2xl bg-[#F59E0B]/10 border border-[#F59E0B]/20 flex items-center justify-center mx-auto mb-4">
            <motion.span
              className="text-[#F59E0B] text-xl"
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.6, repeat: Infinity }}
            >
              &#10022;
            </motion.span>
          </div>
          <p className="text-[#5C524A] text-sm">Preparing your next interview...</p>
        </div>
      </div>
    )
  }

  // ── Error state ────────────────────────────────────────────

  if (error) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center max-w-md px-6">
          <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto mb-4">
            <span className="text-[#5C524A] text-xl">&#10022;</span>
          </div>
          <p className="text-[#A09690] text-sm leading-relaxed mb-6">{error}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="text-[#F59E0B] text-sm hover:underline"
          >
            Back to dashboard
          </button>
        </div>
      </div>
    )
  }

  // ── Interview UI ───────────────────────────────────────────

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] max-w-2xl mx-auto w-full">

      {/* Header context strip */}
      <div className="mb-4 px-1 flex items-center justify-between">
        <div>
          <p className="text-[#5C524A] text-xs uppercase tracking-widest font-mono">
            &#10022; Next Discovery Interview
          </p>
          <p className="text-[#3D3630] text-xs mt-0.5">
            You've grown. Let's find out who you're becoming next.
          </p>
        </div>
        <button
          onClick={() => router.push('/dashboard')}
          className="text-[#3D3630] hover:text-[#5C524A] text-xs transition-colors"
        >
          Exit
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-6 pb-6 pr-2">
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-[#F59E0B]/15 border border-[#F59E0B]/20 flex items-center justify-center mr-3 mt-0.5 shrink-0">
                  <span className="text-[#F59E0B] text-xs">&#10022;</span>
                </div>
              )}
              <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-[0.9375rem] leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#F59E0B]/10 border border-[#F59E0B]/15 text-[#E8E2DC] rounded-tr-sm'
                  : 'bg-[#1E1B18] border border-white/5 text-[#C4BBB5] rounded-tl-sm'
              }`}>
                {msg.content}
              </div>
            </motion.div>
          ))}

          {loading && (
            <motion.div
              key="loading"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="w-8 h-8 rounded-full bg-[#F59E0B]/15 border border-[#F59E0B]/20 flex items-center justify-center mr-3 shrink-0">
                <span className="text-[#F59E0B] text-xs">&#10022;</span>
              </div>
              <div className="bg-[#1E1B18] border border-white/5 px-4 py-3 rounded-2xl rounded-tl-sm">
                <TypingDots />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/5 pt-4">
        <div className="flex items-end gap-3 bg-[#141210] border border-white/7 rounded-2xl px-4 py-3 focus-within:border-[#F59E0B]/30 focus-within:shadow-[0_0_0_3px_rgba(245,158,11,0.08)] transition-all">
          <TextareaAutosize
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your response..."
            minRows={1}
            maxRows={5}
            disabled={loading}
            className="flex-1 bg-transparent text-[#E8E2DC] placeholder:text-[#3D3630] text-[0.9375rem] leading-relaxed resize-none focus:outline-none disabled:opacity-50 font-sans"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="shrink-0 w-9 h-9 rounded-xl bg-[#F59E0B] disabled:bg-[#2A2520] disabled:text-[#5C524A] text-[#0A0908] flex items-center justify-center transition-all hover:bg-[#FCD34D] disabled:cursor-not-allowed"
          >
            <SendIcon />
          </button>
        </div>
        <p className="text-[#3D3630] text-xs text-center mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}

function TypingDots() {
  return (
    <div className="flex gap-1 items-center h-5">
      {[0, 1, 2].map(i => (
        <motion.div
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-[#5C524A]"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </div>
  )
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}