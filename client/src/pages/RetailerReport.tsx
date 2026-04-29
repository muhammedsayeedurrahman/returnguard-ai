import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Speedometer from "../components/Speedometer";
import SignalChips from "../components/SignalChips";
import { getClaim, adminReview } from "../lib/api";

interface Evidence {
  signal_name: string;
  verdict: string;
  detail: string;
  weight: number;
  raw_json?: string;
}

interface Turn {
  turn_number: number;
  agent_message: string;
  customer_response: string;
  tool_called: string | null;
  tool_result: string | null;
}

interface ClaimData {
  claim: any;
  evidence: Evidence[];
  session: any | null;
  turns: Turn[];
}

const DECISION_PILL: Record<string, { bg: string; fg: string; label: string }> = {
  APPROVE:    { bg: "bg-emerald-100", fg: "text-emerald-800", label: "✓ Approve" },
  BORDERLINE: { bg: "bg-amber-100",   fg: "text-amber-800",   label: "⚠ Manual Review" },
  REJECT:     { bg: "bg-red-100",     fg: "text-red-800",     label: "✗ Reject" },
};

export default function RetailerReport() {
  const { claimId } = useParams<{ claimId: string }>();
  const [data, setData] = useState<ClaimData | null>(null);
  const [overriding, setOverriding] = useState(false);

  async function load() {
    if (!claimId) return;
    const r = await getClaim(claimId);
    if (r.ok) setData(r.data);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claimId]);

  async function override(outcome: "CONFIRMED_LEGIT" | "CONFIRMED_FRAUD" | "ESCALATED") {
    if (!claimId) return;
    setOverriding(true);
    await adminReview(claimId, outcome);
    setOverriding(false);
    load();
  }

  if (!data) {
    return <div className="text-center text-slate-500 py-12">Loading report…</div>;
  }

  const score = data.claim.score ?? 0;
  const decision = data.claim.decision ?? "BORDERLINE";
  const pill = DECISION_PILL[decision] || DECISION_PILL.BORDERLINE;
  const videoPath = data.claim.video_path as string | undefined;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/admin" className="text-sm text-slate-500 hover:text-slate-700">
            ← Back to queue
          </Link>
          <h2 className="text-2xl font-semibold text-slate-900 mt-1">
            Claim Report
          </h2>
          <div className="text-xs font-mono text-slate-400 mt-1">{data.claim.id}</div>
        </div>
        <div className={`${pill.bg} ${pill.fg} px-4 py-2 rounded-lg text-sm font-semibold`}>
          {pill.label}
        </div>
      </div>

      {/* Hero: speedometer + summary */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex flex-col lg:flex-row items-center gap-6">
          <Speedometer score={score} showNumeric={true} width={300} />
          <div className="flex-1 space-y-3">
            <div>
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Customer
              </div>
              <div className="text-sm font-mono">{data.claim.customer_id}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Reason
              </div>
              <div className="text-sm">{data.claim.reason_code}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Customer's claim
              </div>
              <div className="text-sm text-slate-700 italic">
                "{data.claim.claim_text || "(no text provided)"}"
              </div>
            </div>
            {data.claim.ring_cluster_id && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-800">
                <span className="font-mono">{data.claim.ring_cluster_id}</span>
                {" — auto-frozen as ring member"}
              </div>
            )}

            {/* Override buttons */}
            <div className="pt-3 flex gap-2">
              <button
                onClick={() => override("CONFIRMED_LEGIT")}
                disabled={overriding}
                className="px-3 py-1.5 rounded-md text-sm font-medium bg-emerald-100 text-emerald-700 hover:bg-emerald-200 disabled:opacity-50"
              >
                ✓ Confirm Legit
              </button>
              <button
                onClick={() => override("CONFIRMED_FRAUD")}
                disabled={overriding}
                className="px-3 py-1.5 rounded-md text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50"
              >
                ✗ Confirm Fraud
              </button>
              <button
                onClick={() => override("ESCALATED")}
                disabled={overriding}
                className="px-3 py-1.5 rounded-md text-sm font-medium bg-amber-100 text-amber-800 hover:bg-amber-200 disabled:opacity-50"
              >
                Escalate
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Signal chips */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="text-xs uppercase tracking-wide text-slate-500 mb-3">
          Signals fired
        </div>
        <SignalChips evidence={data.evidence} />
      </div>

      {/* Customer proof video — WhatsApp-style bubble */}
      {videoPath && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-3">
            Customer proof video
          </div>
          <div className="bg-emerald-50 rounded-2xl rounded-bl-sm p-3 max-w-md inline-block">
            <video
              controls
              src={`/api/v1/claims/${data.claim.id}/video`}
              className="rounded-lg w-full"
              style={{ maxHeight: 320 }}
            />
            <div className="text-xs text-emerald-900 mt-2 flex justify-between">
              <span>📹 Customer proof</span>
              <span className="text-emerald-700">
                {new Date(data.claim.filed_at).toLocaleString("en-IN")}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* AI conversation transcript */}
      {data.turns.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-3">
            AI conversation transcript
          </div>
          <div className="space-y-3">
            {data.turns.map((t) => (
              <div key={t.turn_number} className="space-y-2">
                {t.agent_message && (
                  <div className="flex">
                    <div className="bg-slate-100 rounded-2xl rounded-bl-sm px-4 py-2 max-w-[85%] text-sm">
                      <span className="text-xs text-slate-500 mr-2">AI</span>
                      {t.agent_message}
                    </div>
                  </div>
                )}
                {t.customer_response && (
                  <div className="flex justify-end">
                    <div className="bg-indigo-600 text-white rounded-2xl rounded-br-sm px-4 py-2 max-w-[85%] text-sm">
                      {t.customer_response}
                    </div>
                  </div>
                )}
                {t.tool_called && (
                  <div className="text-xs text-slate-500 font-mono px-2">
                    → tool: {t.tool_called}
                    {t.tool_result && t.tool_called === "issue_decision" && (() => {
                      try {
                        const tr = JSON.parse(t.tool_result);
                        return (
                          <span>
                            {" → "}
                            <span className="text-slate-700">{tr.decision}</span>
                            {tr.rationale && <span> · {tr.rationale}</span>}
                          </span>
                        );
                      } catch {
                        return null;
                      }
                    })()}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
