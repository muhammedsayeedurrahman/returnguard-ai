import { useState } from "react";

interface Evidence {
  signal_name: string;
  verdict: string;
  detail: string;
  weight: number;
  raw_json?: string;
}

interface SignalChipsProps {
  evidence: Evidence[];
}

const VERDICT_STYLES: Record<string, { bg: string; fg: string; border: string }> = {
  OK:      { bg: "bg-emerald-50", fg: "text-emerald-700", border: "border-emerald-200" },
  SKIP:    { bg: "bg-slate-50",   fg: "text-slate-500",   border: "border-slate-200" },
  WARN:    { bg: "bg-amber-50",   fg: "text-amber-800",   border: "border-amber-200" },
  FAIL:    { bg: "bg-red-50",     fg: "text-red-700",     border: "border-red-200" },
  MISSING: { bg: "bg-amber-50",   fg: "text-amber-800",   border: "border-amber-200" },
  GENUINE: { bg: "bg-emerald-50", fg: "text-emerald-700", border: "border-emerald-200" },
  AI_GENERATED: { bg: "bg-red-50",fg: "text-red-700",     border: "border-red-200" },
  EDITED:  { bg: "bg-red-50",     fg: "text-red-700",     border: "border-red-200" },
  SUSPICIOUS: { bg: "bg-amber-50",fg: "text-amber-800",   border: "border-amber-200" },
  UNKNOWN: { bg: "bg-slate-50",   fg: "text-slate-500",   border: "border-slate-200" },
};

const SIGNAL_ICONS: Record<string, string> = {
  exif: "📷",
  image_text: "🖼️",
  ela: "🔍",
  linguistic: "📝",
  address: "📍",
  behavioural: "👤",
  ring_cluster: "🕸️",
  ring_velocity: "⚡",
  receipt: "🧾",
  friendly_fraud: "💳",
  wardrobing: "👗",
  inr: "📦",
  image_trust: "🛡️",
};

const SIGNAL_LABELS: Record<string, string> = {
  exif: "EXIF",
  image_text: "Image-Text",
  ela: "ELA",
  linguistic: "Linguistic",
  address: "Address",
  behavioural: "Behaviour",
  ring_cluster: "Ring",
  ring_velocity: "Velocity",
  receipt: "Receipt",
  friendly_fraud: "Chargeback",
  wardrobing: "Wardrobing",
  inr: "INR",
  image_trust: "Image Trust",
};

export function SignalChips({ evidence }: SignalChipsProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  // Sort: FAIL first, then WARN, then OK/SKIP last; image_trust always first if present
  const sorted = [...evidence].sort((a, b) => {
    if (a.signal_name === "image_trust") return -1;
    if (b.signal_name === "image_trust") return 1;
    const order: Record<string, number> = { FAIL: 0, AI_GENERATED: 0, EDITED: 0, MISSING: 1, WARN: 1, SUSPICIOUS: 1, OK: 2, GENUINE: 2, SKIP: 3, UNKNOWN: 3 };
    return (order[a.verdict] ?? 4) - (order[b.verdict] ?? 4);
  });

  return (
    <div>
      <div className="flex flex-wrap gap-2">
        {sorted.map((ev) => {
          const style = VERDICT_STYLES[ev.verdict] || VERDICT_STYLES.SKIP;
          const icon = SIGNAL_ICONS[ev.signal_name] || "•";
          const label = SIGNAL_LABELS[ev.signal_name] || ev.signal_name;
          const isExpanded = expanded === ev.signal_name;
          const isImageTrust = ev.signal_name === "image_trust";
          return (
            <button
              key={ev.signal_name}
              onClick={() => setExpanded(isExpanded ? null : ev.signal_name)}
              className={`text-left rounded-lg border ${style.border} ${style.bg} ${style.fg} px-3 py-1.5 text-xs font-medium transition hover:shadow-sm ${
                isImageTrust ? "ring-2 ring-offset-1 ring-indigo-300" : ""
              }`}
            >
              <span className="mr-1">{icon}</span>
              {label}
              <span className="ml-1.5 font-mono opacity-75">·{ev.verdict}</span>
              {ev.weight > 0 && (
                <span className="ml-1.5 font-mono text-[10px] opacity-60">
                  w{ev.weight.toFixed(2)}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {expanded && (
        <div className="mt-3 bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm">
          {(() => {
            const ev = evidence.find((e) => e.signal_name === expanded);
            if (!ev) return null;
            return (
              <>
                <div className="font-medium text-slate-900 mb-1">
                  {SIGNAL_LABELS[ev.signal_name] || ev.signal_name} — {ev.verdict}
                </div>
                <div className="text-slate-700">{ev.detail}</div>
                {ev.raw_json && ev.raw_json !== "{}" && (
                  <pre className="mt-2 text-xs text-slate-500 font-mono overflow-x-auto">
                    {ev.raw_json}
                  </pre>
                )}
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
}

export default SignalChips;
