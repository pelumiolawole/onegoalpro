export const COLORS = {
  teal: {
    primary: '#009e97',
    bright: '#33c4be',
    dark: '#006b66',
    glow: 'rgba(0, 158, 151, 0.5)',
  },
  surface: {
    bg: '#FFFFFF',
    light: '#F8F8F7',
    dark: '#F0EFED',
    center: '#e6f8f7',
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