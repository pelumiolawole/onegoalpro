'use client'

import { useEffect, useState } from 'react'
import { useScrollProgress } from '@/hooks/useScrollProgress'
import { COPY, TIMING } from '@/lib/landing/constants'
import { cn } from '@/lib/utils'

export function ContentOverlay() {
  const { progress } = useScrollProgress()
  const [showText, setShowText] = useState(false)
  const [showScrollHint, setShowScrollHint] = useState(false)
  
  useEffect(() => {
    const timer = setTimeout(() => setShowText(true), TIMING.TEXT_FADE_IN_DELAY * 1000)
    return () => clearTimeout(timer)
  }, [])
  
  useEffect(() => {
    const timer = setTimeout(() => setShowScrollHint(true), TIMING.SCROLL_HINT_DELAY * 1000)
    return () => clearTimeout(timer)
  }, [])
  
  const textOpacity = Math.max(0, 1 - progress * 3)
  const textBlur = progress * 10
  
  return (
    <div className="fixed inset-0 z-10 pointer-events-none flex flex-col items-center justify-center">
      <div 
        className="text-center px-4"
        style={{
          opacity: showText ? textOpacity : 0,
          filter: `blur(${textBlur}px)`,
          transform: `translateY(${progress * 50}px)`,
          transition: 'opacity 1.5s ease-out',
        }}
      >
        <h1 className="headline-display text-5xl md:text-7xl lg:text-8xl text-white mb-4">
          {COPY.headline.line1}
        </h1>
        <h2 className="headline-accent text-4xl md:text-6xl lg:text-7xl">
          {COPY.headline.line2}
        </h2>
      </div>
      
      <p 
        className={cn(
          "mt-8 text-lg md:text-xl text-gray-400 max-w-xl text-center px-6",
          "transition-all duration-1000 delay-500"
        )}
        style={{
          opacity: showText ? textOpacity * 0.8 : 0,
          transform: `translateY(${20 + progress * 30}px)`,
        }}
      >
        {COPY.subheadline}
      </p>
      
      <div 
        className="mt-12"
        style={{
          opacity: showText && progress < 0.3 ? 1 : 0,
          transform: `translateY(${progress * 20}px)`,
          transition: 'opacity 0.5s ease',
        }}
      >
        <a 
          href="/signup"
          className="pointer-events-auto inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-gold-600 to-gold-500 text-void-dark font-medium rounded-full hover:from-gold-500 hover:to-gold-400 transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-gold-500/25"
        >
          Start the Interview
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </a>
      </div>
      
      <div 
        className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3"
        style={{
          opacity: showScrollHint && progress < 0.1 ? 1 : 0,
          transition: 'opacity 1s ease',
        }}
      >
        <span className="text-xs uppercase tracking-widest text-gold-400/60">
          {COPY.scrollHint}
        </span>
        <div className="w-px h-16 bg-gradient-to-b from-transparent via-gold-400/40 to-transparent animate-breathe" />
      </div>
      
      <div className="absolute right-8 top-1/2 -translate-y-1/2 flex flex-col gap-2">
        {[0, 0.25, 0.5, 0.75, 1].map((phase, i) => (
          <div 
            key={i}
            className={cn(
              "w-1 h-8 rounded-full transition-all duration-300",
              Math.abs(progress - phase) < 0.15 
                ? "bg-gold-400" 
                : "bg-white/10"
            )}
          />
        ))}
      </div>
    </div>
  )
}