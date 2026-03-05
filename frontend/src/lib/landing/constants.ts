export const COLORS = {
  gold: {
    primary: '#c99a2e',
    bright: '#e8c97a',
    dark: '#8a6420',
    glow: 'rgba(201, 154, 46, 0.5)',
  },
  void: {
    bg: '#0a0908',
    light: '#0d0b08',
    dark: '#050403',
    center: '#1a150f',
  }
} as const

export const PHASES = {
  SINGULARITY: { start: 0, end: 0.15 },
  EXPLOSION: { start: 0.15, end: 0.35 },
  CONSTELLATION: { start: 0.35, end: 0.55 },
  SOLAR_SYSTEM: { start: 0.55, end: 0.80 },
  GALAXY: { start: 0.80, end: 1.0 },
} as const

export const PARTICLES = {
  COUNT: 10000,
  COUNT_MOBILE: 3000,
  BREATH_SPEED: 0.0005,
  BREATH_AMPLITUDE: 0.05,
  MOUSE_INFLUENCE: 0.02,
  MOUSE_RADIUS: 200,
} as const

export const CAMERA = {
  FOV: 75,
  NEAR: 0.1,
  FAR: 1000,
  INITIAL_Z: 5,
} as const

export const TIMING = {
  TEXT_FADE_IN_DELAY: 2,
  TEXT_FADE_IN_DURATION: 1.5,
  SCROLL_HINT_DELAY: 5,
  SCROLL_HINT_DURATION: 1,
  BREATH_CYCLE: 4,
} as const

export const COPY = {
  headline: {
    line1: 'One Goal.',
    line2: 'One Identity.',
  },
  subheadline: 'Most apps track what you do. OneGoal works on who you are. It starts with a real interview, builds a goal around your actual life, and gives you one task every day that moves you toward the person you\'re trying to become.',
  scrollHint: 'Scroll to begin',
} as const