'use client'

import { useState, useEffect } from 'react'

interface ScrollProgress {
  progress: number
  velocity: number
  direction: 'up' | 'down' | 'none'
}

export function useScrollProgress(): ScrollProgress {
  const [scrollData, setScrollData] = useState<ScrollProgress>({
    progress: 0,
    velocity: 0,
    direction: 'none',
  })

  useEffect(() => {
    let lastScrollY = window.scrollY
    let lastTime = Date.now()
    let rafId: number

    const updateScroll = () => {
      const currentScrollY = window.scrollY
      const currentTime = Date.now()
      const deltaTime = currentTime - lastTime
      
      const docHeight = document.documentElement.scrollHeight - window.innerHeight
      const progress = docHeight > 0 ? currentScrollY / docHeight : 0
      
      const deltaY = currentScrollY - lastScrollY
      const velocity = deltaTime > 0 ? (deltaY / deltaTime) * 16 : 0
      
      const direction = deltaY > 0.5 ? 'down' : deltaY < -0.5 ? 'up' : 'none'
      
      setScrollData({
        progress: Math.max(0, Math.min(1, progress)),
        velocity,
        direction,
      })
      
      lastScrollY = currentScrollY
      lastTime = currentTime
      rafId = requestAnimationFrame(updateScroll)
    }

    rafId = requestAnimationFrame(updateScroll)
    
    return () => cancelAnimationFrame(rafId)
  }, [])

  return scrollData
}

export function usePhaseProgress(phaseStart: number, phaseEnd: number): number {
  const { progress } = useScrollProgress()
  
  if (progress < phaseStart) return 0
  if (progress > phaseEnd) return 1
  
  return (progress - phaseStart) / (phaseEnd - phaseStart)
}