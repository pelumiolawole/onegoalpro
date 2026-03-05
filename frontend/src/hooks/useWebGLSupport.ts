'use client'

import { useState, useEffect } from 'react'

interface WebGLSupport {
  supported: boolean
  version: 'webgl2' | 'webgl' | 'none'
}

export function useWebGLSupport(): WebGLSupport {
  const [support, setSupport] = useState<WebGLSupport>({
    supported: false,
    version: 'none',
  })

  useEffect(() => {
    try {
      const canvas = document.createElement('canvas')
      
      const gl2 = canvas.getContext('webgl2')
      if (gl2) {
        setSupport({ supported: true, version: 'webgl2' })
        return
      }
      
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
      if (gl) {
        setSupport({ supported: true, version: 'webgl' })
        return
      }
      
      setSupport({ supported: false, version: 'none' })
    } catch {
      setSupport({ supported: false, version: 'none' })
    }
  }, [])

  return support
}