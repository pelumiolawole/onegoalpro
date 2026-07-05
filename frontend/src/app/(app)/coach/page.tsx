'use client'

import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import TextareaAutosize from 'react-textarea-autosize'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { Zap } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  created_at?: string
  isGreeting?: boolean
}

// The coach should send plain conversational text. If markdown slips through,
// strip the artifacts rather than rendering raw asterisks to the user.
function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*/g, '')          // bold markers
    .replace(/^#{1,6}\s+/gm, '')   // headers
    .replace(/^\s*-\s+/gm, '')     // leading bullets
}

function formatDateLabel(dateStr: string): string {
  const date = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(today.getDate() - 1)
  if (date.toDateString() === today.toDateString()) return 'Today'
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday'
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}

function DateSeparator({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 my-4">
      <div className="flex-1 h-px bg-white/5" />
      <span className="text-[10px] uppercase tracking-widest text-[#3D3630] font-medium px-2">
        {label}
      </span>
      <div className="flex-1 h-px bg-white/5" />
    </div>
  )
}

export default function CoachPage() {
  const { user } = useAuthStore()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [loading, setLoading] = useState(true)
  const [quotaRemaining, setQuotaRemaining] = useState<number | null>(null)
  const [quotaExhausted, setQuotaExhausted] = useState(false)
  const [taskStarter, setTaskStarter] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const msgId = useRef(0)

  useEffect(() => {
    let cancelled = false

    async function init() {
      try {
        const res = await api.coach.getActiveSession()
        if (cancelled) return

        setSessionId(res.session_id)

        const existingMessages: Message[] = (res.messages || []).map((m: any) => ({
          id: String(msgId.current++),
          role: m.role,
          content: m.content,
          created_at: m.created_at,
        }))

        // Check if today's greeting already exists in restored history
        const today = new Date().toDateString()
        const alreadyGreetedToday = existingMessages.some(
          m => m.role === 'assistant' &&
               m.created_at &&
               new Date(m.created_at).toDateString() === today
        )

        // Fetch greeting — needed for greeting text and task starter button
        let greetingText: string | null = null
        let greetingTaskTitle: string | null = null
        try {
          const greetingRes = await api.coach.getGreeting()
          if (!cancelled && greetingRes?.greeting) {
            greetingText = greetingRes.greeting
            greetingTaskTitle = greetingRes.task_title
          }
        } catch {
          // Non-fatal — coach still works without greeting
        }

        if (cancelled) return

        const finalMessages = [...existingMessages]

        // Inject greeting as display-only UI message if not already greeted today
        if (greetingText && !alreadyGreetedToday) {
          finalMessages.push({
            id: String(msgId.current++),
            role: 'assistant',
            content: greetingText,
            created_at: new Date().toISOString(),
            isGreeting: true,
          })
        }

        setMessages(finalMessages)

        // Task-specific starter — appears highlighted at top of starter list
        if (greetingTaskTitle) {
          setTaskStarter(`How do I approach "${greetingTaskTitle}" without talking myself out of it?`)
        }

      } catch {
        // Session fetch failed — empty state renders
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    init()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage(overrideText?: string) {
    const textToSend = overrideText || input.trim()
    if (!textToSend || streaming || !sessionId) return
    if (!overrideText) setInput('')
    setStreaming(true)

    const userId = String(msgId.current++)
    setMessages(prev => [...prev, {
      id: userId, role: 'user', content: textToSend, created_at: new Date().toISOString(),
    }])

    const aiId = String(msgId.current++)
    setMessages(prev => [...prev, {
      id: aiId, role: 'assistant', content: '', streaming: true, created_at: new Date().toISOString(),
    }])

    try {
      const res = await api.coach.streamMessage(sessionId, textToSend)

      if (!res.ok) {
        let errorDetail: any = {}
        try { errorDetail = await res.json() } catch {}
        const detail = errorDetail.detail || {}
        if (res.status === 429 && (typeof detail === 'object' ? detail.code : errorDetail.code) === 'quota_exceeded') {
          setMessages(prev => prev.filter(m => m.id !== aiId))
          setQuotaExhausted(true)
        } else {
          setMessages(prev =>
            prev.map(m => m.id === aiId
              ? { ...m, content: "Something went wrong. Please try again.", streaming: false }
              : m
            )
          )
        }
        return
      }

      if (!res.body) throw new Error('No stream body')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let fullText = ''
      let nextLineIsSystemEvent = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.trim()) {
            nextLineIsSystemEvent = false
            continue
          }

          if (line.startsWith('event: system')) {
            nextLineIsSystemEvent = true
            continue
          }

          if (line.startsWith('data: ')) {
            const data = line.slice(6)

            if (data === '[DONE]' || data.startsWith('[ERROR]')) {
              nextLineIsSystemEvent = false
              break
            }

            if (nextLineIsSystemEvent || data.trimStart().startsWith('{')) {
              try {
                const parsed = JSON.parse(data.trim())
                if (parsed.type === 'quota_banner') {
                  // Quota events now feed only the quiet composer counter —
                  // no banner UI while messages remain.
                  const remaining = parsed?.usage?.remaining
                  if (typeof remaining === 'number') {
                    setQuotaRemaining(remaining)
                    if (remaining <= 0) setQuotaExhausted(true)
                  }
                  nextLineIsSystemEvent = false
                  continue
                }
              } catch {
                // Not JSON — treat as chat text
              }
            }

            nextLineIsSystemEvent = false
            fullText += data.replace(/\\n/g, '\n')
            setMessages(prev =>
              prev.map(m => m.id === aiId ? { ...m, content: fullText } : m)
            )
          }
        }
      }

      setMessages(prev =>
        prev.map(m => m.id === aiId ? { ...m, streaming: false } : m)
      )
    } catch (err: any) {
      if (err?.status === 429 && err?.detail?.code === 'quota_exceeded') {
        setMessages(prev => prev.filter(m => m.id !== aiId))
        setQuotaExhausted(true)
      } else {
        setMessages(prev =>
          prev.map(m => m.id === aiId
            ? { ...m, content: "Something went wrong. Please try again.", streaming: false }
            : m
          )
        )
      }
    } finally {
      setStreaming(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const name = user?.display_name?.split(' ')[0] || 'you'

  // Starters: task-specific first (highlighted), then generic
  const starters = [
    ...(taskStarter ? [{ text: taskStarter, highlight: true }] : []),
    { text: "What's one thing that felt harder than expected this week?", highlight: false },
    { text: "Where am I avoiding the work I know I should be doing?", highlight: false },
    { text: "What would today look like if I showed up as the person I'm becoming?", highlight: false },
  ]

  // Show starters below greeting only — disappear once user has replied
  const lastMessage = messages[messages.length - 1]
  const showStarters = !loading && lastMessage?.isGreeting && !streaming

  return (
    <div className="flex flex-col h-screen max-h-screen pb-16 md:pb-0">

      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5 shrink-0">
        <div className="w-9 h-9 rounded-xl bg-[#F59E0B]/15 border border-[#F59E0B]/20 flex items-center justify-center">
          <span className="text-[#F59E0B] text-sm">✦</span>
        </div>
        <div>
          <p className="text-[#E8E2DC] text-sm font-medium">Your Coach</p>
          <p className="text-[#3D3630] text-xs">Knows your goal, your history, and where you are</p>
          <p className="text-[#2A2520] text-[10px] mt-0.5">AI coach — not a human</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">

        {loading && (
          <div className="flex justify-center py-12">
            <div className="w-6 h-6 border-2 border-[#F59E0B]/20 border-t-[#F59E0B] rounded-full animate-spin" />
          </div>
        )}

        {/* Empty state — only when no messages at all */}
        {!loading && messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16 max-w-sm mx-auto"
          >
            <div className="w-14 h-14 rounded-2xl bg-[#F59E0B]/10 border border-[#F59E0B]/15 flex items-center justify-center mx-auto mb-5">
              <span className="text-[#F59E0B] text-2xl">✦</span>
            </div>
            <h2 className="font-display text-xl text-[#E8E2DC] mb-3">
              Your coach is here
            </h2>
            <p className="text-[#5C524A] text-sm leading-relaxed mb-6">
              Ask about your goal, your week, or what's getting in the way.
              It knows your full history — use that.
            </p>
            <div className="space-y-2">
              {starters.map(s => (
                <button
                  key={s.text}
                  onClick={() => sendMessage(s.text)}
                  className="w-full text-left text-sm px-4 py-2.5 rounded-xl bg-[#141210] border border-white/5 text-[#7A6E65] hover:text-[#A09690] hover:border-white/10 transition-all"
                >
                  {s.text}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Message thread */}
        <AnimatePresence initial={false}>
          {messages.map((msg, index) => {
            const prevMsg = messages[index - 1]
            const msgDate = msg.created_at ? new Date(msg.created_at).toDateString() : null
            const prevDate = prevMsg?.created_at ? new Date(prevMsg.created_at).toDateString() : null
            const showDateSeparator = msgDate && msgDate !== prevDate

            return (
              <React.Fragment key={msg.id}>
                {showDateSeparator && (
                  <DateSeparator label={formatDateLabel(msg.created_at!)} />
                )}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-7 h-7 rounded-full bg-[#F59E0B]/15 border border-[#F59E0B]/20 flex items-center justify-center mr-2.5 mt-0.5 shrink-0">
                      <span className="text-[#F59E0B] text-[10px]">✦</span>
                    </div>
                  )}
                  <div
                    className={`max-w-[82%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-[#F59E0B]/10 border border-[#F59E0B]/15 text-[#E8E2DC] rounded-tr-sm'
                        : 'bg-[#1E1B18] border border-white/5 text-[#C4BBB5] rounded-tl-sm'
                    }`}
                  >
                    {(msg.role === 'assistant' ? stripMarkdown(msg.content) : msg.content) || (msg.streaming ? <TypingDots /> : '')}
                    {msg.streaming && msg.content && (
                      <motion.span
                        animate={{ opacity: [1, 0] }}
                        transition={{ duration: 0.5, repeat: Infinity }}
                        className="inline-block w-0.5 h-3.5 bg-[#F59E0B] ml-0.5 align-middle"
                      />
                    )}
                  </div>
                </motion.div>
              </React.Fragment>
            )
          })}
        </AnimatePresence>

        {/* Starter prompts — shown below greeting, disappear after first user reply */}
        <AnimatePresence>
          {showStarters && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              transition={{ duration: 0.2 }}
              className="space-y-2 pl-9"
            >
              {starters.slice(0, 3).map(s => (
                <button
                  key={s.text}
                  onClick={() => sendMessage(s.text)}
                  className={`w-full text-left text-sm px-4 py-2.5 rounded-xl border transition-all ${
                    s.highlight
                      ? 'bg-[#F59E0B]/8 border-[#F59E0B]/25 text-[#C4BBB5] hover:bg-[#F59E0B]/12 hover:border-[#F59E0B]/35'
                      : 'bg-[#141210] border-white/5 text-[#7A6E65] hover:text-[#A09690] hover:border-white/10'
                  }`}
                >
                  {s.text}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        <div ref={bottomRef} />
      </div>

      {/* Composer — quiet quota line while messages remain; the upgrade prompt
          replaces the input entirely at the moment of exhaustion. This is the
          only place upgrade UI appears in the coach. */}
      <div className="border-t border-white/5 p-4 shrink-0">
        {quotaExhausted ? (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-3xl mx-auto rounded-2xl border border-[#F59E0B]/25 bg-[#F59E0B]/6 px-5 py-5 text-center"
          >
            <div className="w-9 h-9 rounded-xl bg-[#F59E0B]/15 flex items-center justify-center mx-auto mb-3">
              <Zap className="w-4 h-4 text-[#F59E0B]" />
            </div>
            <p className="text-[#F5F1ED] text-sm font-medium mb-4">
              You've used today's 5 messages. Forge is unlimited.
            </p>
            <a
              href="/settings/upgrade?plan=forge"
              className="inline-block px-5 py-2.5 rounded-xl bg-[#F59E0B] text-[#0A0908] text-sm font-medium hover:bg-[#D97706] transition-colors"
            >
              Upgrade to Forge
            </a>
            <p className="text-[#5C524A] text-xs mt-3">Resets at midnight</p>
          </motion.div>
        ) : (
          <div className="max-w-3xl mx-auto">
            {quotaRemaining !== null && quotaRemaining > 0 && (
              <p className="text-[#7A6E65] text-xs mb-2 px-1">
                {quotaRemaining} {quotaRemaining === 1 ? 'message' : 'messages'} left today
              </p>
            )}
            <div className="flex items-end gap-3 bg-[#141210] border border-white/7 rounded-2xl px-4 py-3 focus-within:border-[#F59E0B]/30 focus-within:shadow-[0_0_0_3px_rgba(245,158,11,0.08)] transition-all">
              <TextareaAutosize
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`What's on your mind, ${name}?`}
                minRows={1}
                maxRows={6}
                disabled={streaming || !sessionId}
                className="flex-1 bg-transparent text-[#E8E2DC] placeholder:text-[#3D3630] text-base leading-relaxed resize-none focus:outline-none disabled:opacity-50 font-sans"
              />
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || streaming || !sessionId}
                className="shrink-0 w-8 h-8 rounded-xl bg-[#F59E0B] disabled:bg-[#2A2520] disabled:text-[#5C524A] text-[#0A0908] flex items-center justify-center transition-all hover:bg-[#FCD34D] disabled:cursor-not-allowed"
              >
                {streaming ? (
                  <span className="w-3 h-3 border border-[#0A0908]/30 border-t-[#0A0908] rounded-full animate-spin" />
                ) : (
                  <SendIcon />
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function TypingDots() {
  return (
    <span className="inline-flex gap-1 items-center h-4">
      {[0, 1, 2].map(i => (
        <motion.span
          key={i}
          className="w-1 h-1 rounded-full bg-[#5C524A] inline-block"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </span>
  )
}

function SendIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}
