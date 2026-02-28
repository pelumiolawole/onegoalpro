// OneGoalLogo.tsx
// Reusable logo component — icon + optional wordmark
// Usage: <OneGoalLogo size={28} /> or <OneGoalLogo size={28} showText />

interface Props {
  size?: number
  showText?: boolean
  textSize?: string   // tailwind text-* class
  className?: string
}

export default function OneGoalLogo({
  size = 28,
  showText = true,
  textSize = 'text-xl',
  className = '',
}: Props) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <OneGoalIcon size={size} />
      {showText && (
        <span className={`font-display ${textSize} text-[#F5F1ED] leading-none`}>
          One Goal
        </span>
      )}
    </div>
  )
}

export function OneGoalIcon({ size = 28 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ flexShrink: 0 }}
    >
      {/* ── Target rings (perspective/3D angled) ── */}
      {/* Outer dark ring */}
      <ellipse cx="42" cy="52" rx="38" ry="44" fill="#2D3A3A" />
      {/* Mid ring */}
      <ellipse cx="42" cy="52" rx="28" ry="33" fill="#1A2626" />
      {/* Inner ring */}
      <ellipse cx="42" cy="52" rx="18" ry="22" fill="#2D3A3A" />
      {/* Bullseye — teal */}
      <ellipse cx="42" cy="52" rx="9" ry="11" fill="#4A9E96" />

      {/* ── Scattered miss arrows (dark/charcoal) ── */}
      {/* Top-left arrow */}
      <g transform="translate(28, 18) rotate(130)">
        <line x1="0" y1="0" x2="14" y2="0" stroke="#374545" strokeWidth="2.5" strokeLinecap="round"/>
        <polygon points="14,0 10,-3 10,3" fill="#374545"/>
      </g>
      {/* Top-right arrow */}
      <g transform="translate(55, 14) rotate(150)">
        <line x1="0" y1="0" x2="14" y2="0" stroke="#374545" strokeWidth="2.5" strokeLinecap="round"/>
        <polygon points="14,0 10,-3 10,3" fill="#374545"/>
      </g>
      {/* Right-top arrow */}
      <g transform="translate(70, 32) rotate(175)">
        <line x1="0" y1="0" x2="14" y2="0" stroke="#374545" strokeWidth="2.5" strokeLinecap="round"/>
        <polygon points="14,0 10,-3 10,3" fill="#374545"/>
      </g>
      {/* Bottom-right arrow */}
      <g transform="translate(68, 62) rotate(-155)">
        <line x1="0" y1="0" x2="14" y2="0" stroke="#374545" strokeWidth="2.5" strokeLinecap="round"/>
        <polygon points="14,0 10,-3 10,3" fill="#374545"/>
      </g>
      {/* Bottom arrow */}
      <g transform="translate(52, 80) rotate(-120)">
        <line x1="0" y1="0" x2="14" y2="0" stroke="#374545" strokeWidth="2.5" strokeLinecap="round"/>
        <polygon points="14,0 10,-3 10,3" fill="#374545"/>
      </g>
      {/* Left-bottom arrow */}
      <g transform="translate(18, 72) rotate(-60)">
        <line x1="0" y1="0" x2="14" y2="0" stroke="#374545" strokeWidth="2.5" strokeLinecap="round"/>
        <polygon points="14,0 10,-3 10,3" fill="#374545"/>
      </g>

      {/* ── The ONE red arrow — hits bullseye dead center ── */}
      <g>
        {/* Shaft */}
        <line x1="92" y1="52" x2="48" y2="52" stroke="#C0392B" strokeWidth="5" strokeLinecap="round"/>
        {/* Arrowhead */}
        <polygon points="48,52 58,46 58,58" fill="#C0392B"/>
        {/* Tail fletching */}
        <line x1="92" y1="52" x2="86" y2="45" stroke="#C0392B" strokeWidth="2.5" strokeLinecap="round"/>
        <line x1="92" y1="52" x2="86" y2="59" stroke="#C0392B" strokeWidth="2.5" strokeLinecap="round"/>
      </g>
    </svg>
  )
}
