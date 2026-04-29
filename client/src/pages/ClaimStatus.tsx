import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { getClaim, takeTurn } from "../lib/api";

type Evidence = {
  signal_name: string;
  verdict: string;
  detail: string;
  weight: number;
};

type Turn = {
  turn_number: number;
  agent_message: string;
  customer_response: string;
  tool_called: string | null;
  tool_result: string | null;
};

type ClaimData = {
  claim: any;
  evidence: Evidence[];
  session: any | null;
  turns: Turn[];
};

const VERDICT_COLORS: Record<string, string> = {
  OK: "bg-emerald-50 text-emerald-700 border-emerald-200",
  SKIP: "bg-slate-50 text-slate-500 border-slate-200",
  WARN: "bg-amber-50 text-amber-800 border-amber-200",
  FAIL: "bg-red-50 text-red-700 border-red-200",
  MISSING: "bg-amber-50 text-amber-800 border-amber-200",
};

const DECISION_BANNER: Record<string, { color: string; title: string; sub: string }> = {
  APPROVE: {
    color: "bg-emerald-600",
    title: "✓ Approved",
    sub: "Refund will be processed within 24 hours.",
  },
  REJECT: {
    color: "bg-red-600",
    title: "Under review",
    sub: "We've identified a concern. A teammate will follow up within 24 hours.",
  },
  BORDERLINE: {
    color: "bg-indigo-600",
    title: "Quick verification",
    sub: "Our specialist will help finish this in under a minute.",
  },
};

export default function ClaimStatus() {
  const { claimId } = useParams<{ claimId: string }>();
  const [data, setData] = useState<ClaimData | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatPhoto, setChatPhoto] = useState<File | null>(null);
  const [sending, setSending] = useState(false);
  const pollRef = useRef<number | null>(null);

  async function refresh() {
    if (!claimId) return;
    const r = await getClaim(claimId);
    if (r.ok) setData(r.data);
  }

  useEffect(() => {
    refresh();
    pollRef.current = window.setInterval(refresh, 1500) as unknown as number;
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [claimId]);

  if (!data) return <div className="text-slate-500">Loading…</div>;

  const decision = data.claim.decision || "BORDERLINE";
  const banner = DECISION_BANNER[decision] || DECISION_BANNER.BORDERLINE;

  async function sendTurn() {
    if (!data?.session?.id) return;
    if (!chatInput.trim() && !chatPhoto) return;
    setSending(true);
    await takeTurn(data.session.id, chatInput, chatPhoto || undefined);
    setChatInput("");
    setChatPhoto(null);
    setSending(false);
    refresh();
  }

  const sessionClosed = !!data.session?.outcome;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div
        key={decision}
        className={`${banner.color} text-white rounded-xl p-6 flex items-center gap-5 animate-banner-in`}
      >
        <ScoreRing score={data.claim.score ?? 0} />
        <div className="flex-1">
          <div className="text-2xl font-semibold">{banner.title}</div>
          <div className="text-white/90 mt-1">{banner.sub}</div>
          <div className="text-xs text-white/70 mt-3 font-mono">
            Claim {data.claim.id} · {decision}
          </div>
        </div>
      </div>

      {/* AI Evaluation Engine chat — only renders when borderline */}
      {data.session && (
        <div className="bg-white rounded-xl border border-slate-200">
          <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
            <div>
              <div className="font-medium text-slate-900">AI Evaluation Specialist</div>
              <div className="text-xs text-slate-500">
                Resolves this claim in seconds — no waiting on a human queue.
              </div>
            </div>
            <div className="text-xs text-slate-500">
              Turn {data.session.turn_count}/4
            </div>
          </div>

          <div className="p-5 space-y-3 max-h-96 overflow-y-auto">
            {data.turns.length === 0 && !sending && (
              <div className="text-center text-sm text-slate-500 py-4">
                Send a message to begin verification.
              </div>
            )}
            {data.turns.map((t) => (
              <div key={t.turn_number} className="space-y-2 message-in">
                {t.agent_message && (
                  <div className="flex">
                    <div className="bg-slate-100 rounded-2xl rounded-bl-sm px-4 py-2 max-w-[85%]">
                      <div className="text-sm text-slate-800">{t.agent_message}</div>
                    </div>
                  </div>
                )}
                {t.customer_response && (
                  <div className="flex justify-end">
                    <div className="bg-indigo-600 text-white rounded-2xl rounded-br-sm px-4 py-2 max-w-[85%]">
                      <div className="text-sm">{t.customer_response}</div>
                    </div>
                  </div>
                )}
                {t.tool_result && t.tool_called === "issue_decision" && (
                  <div className="text-xs text-slate-500 italic px-1">
                    Decision: {JSON.parse(t.tool_result).decision} —{" "}
                    {JSON.parse(t.tool_result).rationale}
                  </div>
                )}
              </div>
            ))}
            {sending && (
              <div className="flex">
                <div className="bg-slate-100 rounded-2xl rounded-bl-sm px-4 py-3 inline-flex items-center">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </div>
            )}
          </div>

          {!sessionClosed && (
            <div className="p-4 border-t border-slate-200">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendTurn()}
                  placeholder="Type your response…"
                  className="flex-1 px-3 py-2 border border-slate-300 rounded-md text-sm"
                />
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setChatPhoto(e.target.files?.[0] || null)}
                  className="text-xs"
                />
                <button
                  onClick={sendTurn}
                  disabled={sending}
                  className="bg-slate-900 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
                >
                  Send
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Evidence trail */}
      <div className="bg-white rounded-xl border border-slate-200" key="evidence">
        <div className="px-5 py-3 border-b border-slate-200">
          <div className="font-medium text-slate-900">Evidence trail</div>
          <div className="text-xs text-slate-500">
            Six independent signals — none can block alone.
          </div>
        </div>
        <div className="divide-y divide-slate-100">
          {data.evidence.map((e, i) => (
            <div key={i} className="px-5 py-3 flex items-start gap-3">
              <span
                className={`text-xs font-mono px-2 py-0.5 rounded border ${
                  VERDICT_COLORS[e.verdict] || "bg-slate-50 text-slate-500 border-slate-200"
                }`}
              >
                {e.verdict}
              </span>
              <div className="flex-1">
                <div className="text-sm font-medium text-slate-800">
                  {e.signal_name}
                </div>
                <div className="text-sm text-slate-600 mt-0.5">{e.detail}</div>
              </div>
              <div className="text-xs text-slate-400 font-mono">
                w={e.weight}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface ScoreRingProps {
  score: number;
}

function ScoreRing({ score }: ScoreRingProps) {
  const r = 36;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = c * (1 - clamped / 100);
  return (
    <div className="relative w-20 h-20 shrink-0">
      <svg viewBox="0 0 88 88" className="score-progress w-full h-full">
        <circle
          cx="44" cy="44" r={r}
          stroke="rgba(255,255,255,0.25)"
          strokeWidth="6" fill="none"
        />
        <circle
          cx="44" cy="44" r={r}
          stroke="white" strokeWidth="6" fill="none"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className="score-progress-fill"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center text-2xl font-semibold">
        {clamped}
      </div>
    </div>
  );
}
