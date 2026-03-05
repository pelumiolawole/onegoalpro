'use client'

import { useRef, useEffect, useState, Suspense, lazy } from 'react'
import { useScrollProgress } from '@/hooks/useScrollProgress'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { PARTICLES } from '@/lib/landing/constants'

// Lazy load the Three.js component to avoid SSR issues
const ParticleCanvas = lazy(() => import('./ParticleCanvas'))

export function Singularity() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [isMounted, setIsMounted] = useState(false)
  const { progress } = useScrollProgress()
  const reducedMotion = useReducedMotion()

  const [isMobile, setIsMobile] = useState(false)

  // Only render canvas after client-side mount
  useEffect(() => {
    setIsMounted(true)
    setIsMobile(window.innerWidth < 768)
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      setMousePosition({
        x: e.clientX - rect.left - rect.width / 2,
        y: -(e.clientY - rect.top - rect.height / 2),
      })
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  // Show fallback for mobile, reduced motion, or SSR
  if (!isMounted || isMobile || reducedMotion) {
    return (
      <div
        ref={containerRef}
        className="fixed inset-0 z-0"
        style={{ 
          pointerEvents: 'none',
          background: 'radial-gradient(ellipse at center, #1a150f 0%, #0d0b08 40%, #0a0908 100%)'
        }}
      >
        {/* Static stars for fallback */}
        <div className="absolute inset-0 opacity-30">
          {Array.from({ length: 50 }).map((_, i) => (
            <div
              key={i}
              className="absolute rounded-full bg-amber-400"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                width: `${Math.random() * 2 + 1}px`,
                height: `${Math.random() * 2 + 1}px`,
              }}
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-0"
      style={{ pointerEvents: 'none' }}
    >
      <Suspense fallback={
        <div style={{
          background: 'radial-gradient(ellipse at center, #1a150f 0%, #0a0908 100%)',
          width: '100%',
          height: '100%'
        }} />
      }>
        <ParticleCanvas
          scrollProgress={progress}
          mousePosition={mousePosition}
        />
      </Suspense>
    </div>
  )
}