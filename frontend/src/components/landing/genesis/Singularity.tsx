'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import * as THREE from 'three'
import { useScrollProgress } from '@/hooks/useScrollProgress'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { PARTICLES, COLORS, CAMERA } from '@/lib/landing/constants'

const vertexShader = `
  uniform float uTime;
  uniform float uBreathPhase;
  uniform vec2 uMouse;
  uniform float uMouseInfluence;
  uniform float uScrollProgress;

  attribute float size;
  attribute float phase;
  attribute vec3 offset;

  varying float vAlpha;
  varying float vSize;

  const float PI = 3.14159265359;
  const float BREATH_SPEED = 1.5;
  const float BREATH_AMP = 0.08;

  void main() {
    float breath = sin(uTime * BREATH_SPEED + phase * PI * 2.0) * BREATH_AMP;
    breath *= (1.0 + uBreathPhase * 0.5);

    vec3 pos = offset * (1.0 + breath);

    float dist = distance(pos.xy, uMouse * 2.0);
    float mouseEffect = smoothstep(2.0, 0.0, dist) * uMouseInfluence;
    pos.xy += uMouse * mouseEffect;

    float flatten = uScrollProgress * 0.3;
    pos.y *= (1.0 - flatten * abs(pos.y));

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);

    float attenuation = 300.0 / -mvPosition.z;
    gl_PointSize = size * attenuation * (1.0 + breath * 2.0);

    gl_Position = projectionMatrix * mvPosition;

    vAlpha = 0.6 + breath * 2.0;
    vAlpha *= (1.0 - uScrollProgress * 0.3);
    vSize = size;
  }
`

const fragmentShader = `
  uniform vec3 uColor;
  uniform float uTime;

  varying float vAlpha;
  varying float vSize;

  void main() {
    vec2 center = gl_PointCoord - vec2(0.5);
    float dist = length(center);

    float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
    alpha *= vAlpha;

    float core = 1.0 - smoothstep(0.0, 0.2, dist);
    vec3 color = mix(uColor, vec3(1.0, 0.9, 0.7), core * 0.5);

    float shimmer = sin(uTime * 3.0 + vSize * 10.0) * 0.1 + 0.9;
    color *= shimmer;

    gl_FragColor = vec4(color, alpha);

    if (alpha < 0.01) discard;
  }
`

interface ParticleSystemProps {
  count: number
  scrollProgress: number
  mousePosition: { x: number; y: number }
  reducedMotion: boolean
}

function createParticleSystem(count: number) {
  const geometry = new THREE.BufferGeometry()
  
  const offsets = new Float32Array(count * 3)
  const sizes = new Float32Array(count)
  const phases = new Float32Array(count)

  const goldenRatio = (1 + Math.sqrt(5)) / 2

  for (let i = 0; i < count; i++) {
    const y = 1 - (i / (count - 1)) * 2
    const radius = Math.sqrt(1 - y * y)
    const theta = goldenRatio * i * Math.PI * 2

    const x = Math.cos(theta) * radius
    const z = Math.sin(theta) * radius

    const randomOffset = 0.1
    offsets[i * 3] = x * (1 + (Math.random() - 0.5) * randomOffset)
    offsets[i * 3 + 1] = y * (1 + (Math.random() - 0.5) * randomOffset)
    offsets[i * 3 + 2] = z * (1 + (Math.random() - 0.5) * randomOffset)

    sizes[i] = Math.random() * 3 + 1
    phases[i] = Math.random()
  }

  geometry.setAttribute('offset', new THREE.BufferAttribute(offsets, 3))
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
  geometry.setAttribute('phase', new THREE.BufferAttribute(phases, 1))

  const material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      uTime: { value: 0 },
      uColor: { value: new THREE.Color(COLORS.gold.primary) },
      uBreathPhase: { value: 0 },
      uMouse: { value: new THREE.Vector2(0, 0) },
      uMouseInfluence: { value: PARTICLES.MOUSE_INFLUENCE },
      uScrollProgress: { value: 0 },
    },
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })

  return new THREE.Points(geometry, material)
}

function ParticleScene({ 
  count, 
  scrollProgress, 
  mousePosition, 
  reducedMotion 
}: ParticleSystemProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<{
    scene: THREE.Scene
    camera: THREE.PerspectiveCamera
    renderer: THREE.WebGLRenderer
    points: THREE.Points
    rafId: number
  } | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Setup
    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(CAMERA.FOV, width / height, 0.1, 1000)
    camera.position.z = CAMERA.INITIAL_Z

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // Create particles
    const points = createParticleSystem(count)
    scene.add(points)

    sceneRef.current = { scene, camera, renderer, points, rafId: 0 }

    // Animation loop
    let lastTime = 0
    const animate = (time: number) => {
      if (!sceneRef.current) return
      
      const { points, camera, renderer, scene } = sceneRef.current
      const material = points.material as THREE.ShaderMaterial
      
      const delta = (time - lastTime) / 1000
      lastTime = time
      
      const timeScale = reducedMotion ? 0.3 : 1.0
      
      // Update uniforms
      material.uniforms.uTime.value += delta * timeScale
      material.uniforms.uScrollProgress.value = scrollProgress
      material.uniforms.uBreathPhase.value = 
        Math.sin(material.uniforms.uTime.value * 0.5) * 0.5 + 0.5

      // Update camera
      const targetZ = CAMERA.INITIAL_Z - scrollProgress * 2
      camera.position.z += (targetZ - camera.position.z) * 0.05
      camera.rotation.z = scrollProgress * 0.1

      // Rotate points
      points.rotation.y += 0.001 * timeScale
      points.rotation.x = scrollProgress * 0.3

      renderer.render(scene, camera)
      sceneRef.current.rafId = requestAnimationFrame(animate)
    }

    sceneRef.current.rafId = requestAnimationFrame(animate)

    // Resize handler
    const handleResize = () => {
      if (!sceneRef.current || !containerRef.current) return
      const { camera, renderer } = sceneRef.current
      const w = containerRef.current.clientWidth
      const h = containerRef.current.clientHeight
      
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (sceneRef.current) {
        cancelAnimationFrame(sceneRef.current.rafId)
        container.removeChild(renderer.domElement)
        geometry.dispose()
        material.dispose()
        renderer.dispose()
      }
    }
  }, [count, reducedMotion])

  // Update mouse position
  useEffect(() => {
    if (!sceneRef.current) return
    const { points } = sceneRef.current
    const material = points.material as THREE.ShaderMaterial
    
    const targetX = (mousePosition.x / window.innerWidth) * 4
    const targetY = (mousePosition.y / window.innerHeight) * 4
    
    material.uniforms.uMouse.value.x += (targetX - material.uniforms.uMouse.value.x) * 0.05
    material.uniforms.uMouse.value.y += (targetY - material.uniforms.uMouse.value.y) * 0.05
  }, [mousePosition])

  return <div ref={containerRef} className="absolute inset-0" />
}

export function Singularity() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const { progress } = useScrollProgress()
  const reducedMotion = useReducedMotion()

  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
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

  const particleCount = isMobile || reducedMotion
    ? PARTICLES.COUNT_MOBILE
    : PARTICLES.COUNT

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-0"
      style={{ background: 'radial-gradient(circle at center, #0D0B09 0%, #0A0908 100%)' }}
    >
      <ParticleScene
        count={particleCount}
        scrollProgress={progress}
        mousePosition={mousePosition}
        reducedMotion={reducedMotion}
      />
    </div>
  )
}