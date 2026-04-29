import { useEffect, useRef, useState } from "react";

interface SpeedometerProps {
  score: number; // 0–100
  /** When false, hides the numeric score (used for customer-facing view). */
  showNumeric?: boolean;
  /** Optional label override; defaults to tier-derived label. */
  label?: string;
  width?: number;
}

interface Band {
  start: number;
  end: number;
  color: string;
  tone: string;
  label: string;
}

const BANDS: Band[] = [
  { start: 0,  end: 35,  color: "#10b981", tone: "emerald", label: "Trusted" },
  { start: 35, end: 65,  color: "#f59e0b", tone: "amber",   label: "Review" },
  { start: 65, end: 100, color: "#dc2626", tone: "red",     label: "Flagged" },
];

function bandFor(score: number): Band {
  for (const b of BANDS) {
    if (score >= b.start && score < b.end) return b;
  }
  return BANDS[BANDS.length - 1];
}

/** Map a 0–100 score to needle rotation in degrees (-90 = 0, +90 = 100). */
function scoreToAngle(score: number): number {
  const clamped = Math.max(0, Math.min(100, score));
  return -90 + (clamped / 100) * 180;
}

/** SVG arc path between two angles around (cx,cy) with given radius. */
function describeArc(cx: number, cy: number, r: number, start: number, end: number): string {
  const a1 = ((start - 90) * Math.PI) / 180;
  const a2 = ((end - 90) * Math.PI) / 180;
  const x1 = cx + r * Math.cos(a1);
  const y1 = cy + r * Math.sin(a1);
  const x2 = cx + r * Math.cos(a2);
  const y2 = cy + r * Math.sin(a2);
  const large = end - start <= 180 ? 0 : 1;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
}

export function Speedometer({
  score,
  showNumeric = true,
  label,
  width = 280,
}: SpeedometerProps) {
  const [animatedAngle, setAnimatedAngle] = useState(-90);
  const targetAngle = scoreToAngle(score);
  const band = bandFor(score);
  const displayLabel = label ?? band.label;

  // Animate needle on mount/score change
  const startedAt = useRef<number | null>(null);
  useEffect(() => {
    let raf = 0;
    const startAngle = animatedAngle;
    const delta = targetAngle - startAngle;
    const duration = 800;
    startedAt.current = performance.now();

    const tick = (now: number) => {
      const elapsed = now - (startedAt.current ?? now);
      const t = Math.min(1, elapsed / duration);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setAnimatedAngle(startAngle + delta * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetAngle]);

  const cx = width / 2;
  const cy = width / 2;
  const r = width * 0.4;

  return (
    <div className="flex flex-col items-center select-none" style={{ width }}>
      <svg viewBox={`0 0 ${width} ${cy + 30}`} width={width} height={cy + 30}>
        {/* Color bands */}
        {BANDS.map((b) => {
          const startA = -90 + (b.start / 100) * 180;
          const endA = -90 + (b.end / 100) * 180;
          return (
            <path
              key={b.start}
              d={describeArc(cx, cy, r, startA, endA)}
              fill="none"
              stroke={b.color}
              strokeWidth={width * 0.08}
              strokeLinecap="butt"
              opacity={0.85}
            />
          );
        })}

        {/* Tick labels */}
        {[0, 35, 65, 100].map((t) => {
          const a = ((scoreToAngle(t) - 90) * Math.PI) / 180;
          const tr = r + width * 0.075;
          const x = cx + tr * Math.cos(a);
          const y = cy + tr * Math.sin(a);
          return (
            <text
              key={t}
              x={x}
              y={y + 4}
              textAnchor="middle"
              fontSize={width * 0.04}
              fill="#64748b"
              fontFamily="ui-monospace, monospace"
            >
              {t}
            </text>
          );
        })}

        {/* Needle */}
        <g transform={`rotate(${animatedAngle} ${cx} ${cy})`}>
          <line
            x1={cx}
            y1={cy}
            x2={cx}
            y2={cy - r * 0.95}
            stroke="#0f172a"
            strokeWidth={width * 0.012}
            strokeLinecap="round"
          />
          <circle cx={cx} cy={cy} r={width * 0.04} fill="#0f172a" />
          <circle cx={cx} cy={cy} r={width * 0.018} fill="#fff" />
        </g>

        {/* Center label / numeric */}
        {showNumeric ? (
          <>
            <text
              x={cx}
              y={cy + r * 0.6}
              textAnchor="middle"
              fontSize={width * 0.18}
              fontWeight={700}
              fill={band.color}
              fontFamily="ui-monospace, monospace"
            >
              {Math.round(score)}
            </text>
            <text
              x={cx}
              y={cy + r * 0.6 + width * 0.07}
              textAnchor="middle"
              fontSize={width * 0.05}
              fill="#64748b"
            >
              of 100
            </text>
          </>
        ) : (
          <text
            x={cx}
            y={cy + r * 0.5}
            textAnchor="middle"
            fontSize={width * 0.08}
            fontWeight={600}
            fill={band.color}
          >
            {displayLabel}
          </text>
        )}
      </svg>

      {showNumeric && (
        <div className="mt-1 text-sm font-medium" style={{ color: band.color }}>
          {displayLabel}
        </div>
      )}
    </div>
  );
}

export default Speedometer;
