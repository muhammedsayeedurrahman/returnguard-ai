import { useState } from "react";
import { verifyReceipt } from "../lib/api";

interface ReceiptResult {
  signal: string;
  verdict: "OK" | "WARN" | "FAIL" | "SKIP";
  score: number;
  detail: string;
  raw: {
    sha256?: string;
    metadata?: {
      title?: string;
      author?: string;
      creator?: string;
      producer?: string;
      creation_date?: string;
      mod_date?: string;
    };
    tamper_signals?: { type: string; detail: string }[];
    amount_check?: { found_in_text?: boolean; expected?: number };
  };
}

const VERDICT_STYLE: Record<string, { color: string; label: string }> = {
  OK:   { color: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Verified" },
  WARN: { color: "bg-amber-50 text-amber-800 border-amber-200", label: "Partial Check" },
  FAIL: { color: "bg-red-50 text-red-700 border-red-200", label: "Mismatch Detected" },
  SKIP: { color: "bg-slate-50 text-slate-600 border-slate-200", label: "No Receipt" },
};

export default function BillingVerification() {
  const [orderId, setOrderId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ReceiptResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!orderId || !file) return;
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const r = await verifyReceipt(orderId, file);
      if (!r.ok) {
        setError(r.detail || "Verification failed");
      } else {
        setResult(r.data);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Receipt Verification</h2>
        <p className="text-slate-600 mt-1 text-sm">
          Upload your receipt PDF — we'll verify it against our records and check for
          tampering.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="bg-white rounded-xl border border-slate-200 p-6 space-y-4"
      >
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Order ID</label>
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="ord_legit_000"
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Receipt PDF</label>
          <input
            type="file"
            accept="application/pdf,image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full text-sm text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
            required
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md px-3 py-2">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || !orderId || !file}
          className="w-full bg-slate-900 text-white py-2.5 rounded-md font-medium hover:bg-slate-800 disabled:opacity-50 transition"
        >
          {submitting ? "Verifying…" : "Verify receipt"}
        </button>
      </form>

      {result && (
        <div className={`rounded-xl border ${VERDICT_STYLE[result.verdict].color} p-5`}>
          <div className="flex items-center gap-3 mb-3">
            <div className="text-2xl font-semibold">
              {VERDICT_STYLE[result.verdict].label}
            </div>
            <span className="font-mono text-xs px-2 py-0.5 rounded border border-current/30">
              score {result.score}
            </span>
          </div>
          <div className="text-sm">{result.detail}</div>

          {result.raw.metadata && (
            <div className="mt-4 bg-white/40 rounded p-3 text-xs space-y-1 font-mono">
              {result.raw.metadata.creator && (
                <div>Creator: <span className="text-slate-700">{result.raw.metadata.creator}</span></div>
              )}
              {result.raw.metadata.producer && (
                <div>Producer: <span className="text-slate-700">{result.raw.metadata.producer}</span></div>
              )}
              {result.raw.metadata.creation_date && (
                <div>Created: <span className="text-slate-700">{result.raw.metadata.creation_date}</span></div>
              )}
              {result.raw.metadata.mod_date && (
                <div>Modified: <span className="text-slate-700">{result.raw.metadata.mod_date}</span></div>
              )}
            </div>
          )}

          {result.raw.tamper_signals && result.raw.tamper_signals.length > 0 && (
            <div className="mt-3 text-xs">
              <div className="font-medium mb-1">Tamper signals:</div>
              <ul className="list-disc pl-5 space-y-0.5">
                {result.raw.tamper_signals.map((s, i) => (
                  <li key={i}>{s.type}: {s.detail}</li>
                ))}
              </ul>
            </div>
          )}

          {result.raw.sha256 && (
            <div className="mt-3 text-xs text-slate-500 font-mono break-all">
              sha256: {result.raw.sha256}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
