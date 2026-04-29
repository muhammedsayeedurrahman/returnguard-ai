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
    stored_amount?: number;
  };
}

const SAMPLE_ORDERS = [
  { id: "ord_legit_000", label: "Boat Earbuds (Bengaluru)", amount: 1499 },
  { id: "ord_priya_001", label: "Boat Earbuds (Priya)",      amount: 1499 },
  { id: "ord_wardrobing_001", label: "Sabyasachi Lehenga (Mumbai)", amount: 45000 },
  { id: "ord_friendly_001", label: "iPhone 15 Pro (Bengaluru)", amount: 134900 },
];


export default function BillingVerification() {
  const [orderId, setOrderId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState<string>("");
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

  function selectSample(id: string) {
    setOrderId(id);
    setFile(null);
    setFileName("");
    setResult(null);
  }

  async function autoLoadFile(url: string, suggestedName: string) {
    try {
      const r = await fetch(url);
      const blob = await r.blob();
      const f = new File([blob], suggestedName, { type: "application/pdf" });
      setFile(f);
      setFileName(suggestedName);
    } catch (err) {
      setError(`Could not auto-load: ${String(err)}`);
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Receipt Verification</h2>
        <p className="text-slate-600 mt-1 text-sm">
          Upload your receipt PDF — we'll match it against the copy we issued at order time.
        </p>
      </div>

      {/* Sample receipts panel — judges can grab a clean or tampered version to demo */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 text-sm">
        <div className="font-medium text-indigo-900 mb-2">
          Demo helper — try a clean or tampered receipt
        </div>
        <div className="space-y-2">
          {SAMPLE_ORDERS.map((o) => (
            <div key={o.id} className="flex items-center gap-2 flex-wrap">
              <button
                onClick={() => selectSample(o.id)}
                className="font-mono text-xs px-2 py-0.5 rounded bg-white border border-indigo-300 hover:bg-indigo-100 text-indigo-800"
              >
                {o.id}
              </button>
              <span className="text-slate-700 flex-1 text-xs">
                {o.label} · ₹{o.amount.toLocaleString("en-IN")}
              </span>
              <button
                onClick={() => {
                  setOrderId(o.id);
                  autoLoadFile(`/api/v1/receipts/${o.id}/download`, `${o.id}.pdf`);
                }}
                className="text-xs px-2 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-700"
              >
                ✓ Use clean
              </button>
              <button
                onClick={() => {
                  setOrderId(o.id);
                  autoLoadFile(`/api/v1/demo/receipts/${o.id}/tampered`, `${o.id}_tampered.pdf`);
                }}
                className="text-xs px-2 py-1 rounded bg-red-600 text-white hover:bg-red-700"
              >
                ⚠ Use tampered
              </button>
            </div>
          ))}
        </div>
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
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono text-sm"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Receipt PDF</label>
          {file ? (
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-md px-3 py-2">
              <span className="text-sm text-slate-700 flex-1">{fileName || file.name}</span>
              <button
                type="button"
                onClick={() => { setFile(null); setFileName(""); }}
                className="text-xs text-slate-500 hover:text-slate-800"
              >
                Remove
              </button>
            </div>
          ) : (
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) { setFile(f); setFileName(f.name); }
              }}
              className="w-full text-sm text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
              required
            />
          )}
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

      {result && <ResultCard result={result} orderId={orderId} />}
    </div>
  );
}


interface ResultCardProps {
  result: ReceiptResult;
  orderId: string;
}

function ResultCard({ result, orderId }: ResultCardProps) {
  const verdict = result.verdict;
  const isVerified = verdict === "OK" && result.score === 0;
  const isMismatch = verdict === "FAIL";
  const isPartial = verdict === "WARN" || (verdict === "OK" && result.score > 0);

  return (
    <div className="space-y-4 animate-banner-in">
      {/* Hero verdict card */}
      <div
        className={
          isVerified
            ? "rounded-xl border-2 border-emerald-200 bg-gradient-to-br from-emerald-50 to-emerald-100 p-6"
            : isMismatch
            ? "rounded-xl border-2 border-red-200 bg-gradient-to-br from-red-50 to-red-100 p-6"
            : "rounded-xl border-2 border-amber-200 bg-gradient-to-br from-amber-50 to-amber-100 p-6"
        }
      >
        <div className="flex items-start gap-4">
          <div className="text-5xl">
            {isVerified ? "✓" : isMismatch ? "✗" : "!"}
          </div>
          <div className="flex-1">
            <div className="text-2xl font-semibold text-slate-900">
              {isVerified
                ? "Receipt verified"
                : isMismatch
                ? "Mismatch detected"
                : "Partial verification"}
            </div>
            <div className="text-sm text-slate-700 mt-1">{result.detail}</div>
            <div className="text-xs font-mono text-slate-500 mt-3">
              Order {orderId} · score {result.score} · verdict {verdict}
            </div>
          </div>
        </div>

        {/* Next-step CTA */}
        {isVerified && (
          <div className="mt-4 pt-4 border-t border-emerald-200 text-sm text-emerald-900">
            Your refund will be processed within 24 hours. No further action needed.
          </div>
        )}
        {isMismatch && (
          <div className="mt-4 pt-4 border-t border-red-200 text-sm text-red-900">
            This receipt doesn't match the copy we issued. Your claim has been routed
            for manual review. A teammate will follow up within 24 hours.
          </div>
        )}
        {isPartial && (
          <div className="mt-4 pt-4 border-t border-amber-200 text-sm text-amber-900">
            We need to take a closer look — please upload the original receipt PDF
            from your order confirmation email.
          </div>
        )}
      </div>

      {/* Side-by-side comparison */}
      {result.raw.metadata && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <MetaPanel
            title="What you uploaded"
            tone={isMismatch ? "danger" : "neutral"}
            items={[
              ["Producer", result.raw.metadata.producer || "—"],
              ["Created", result.raw.metadata.creation_date || "—"],
              ["Modified", result.raw.metadata.mod_date || "—"],
              ["Hash (SHA-256)", result.raw.sha256?.slice(0, 16) + "…" || "—"],
            ]}
          />
          <MetaPanel
            title="What we issued"
            tone="success"
            items={[
              ["Source", "ReturnGuard AI billing system"],
              ["Issued at", "Order time"],
              ["Verification", "Cryptographic SHA-256 hash"],
              ["Status", isVerified ? "✓ Hashes match" : "✗ Hashes differ"],
            ]}
          />
        </div>
      )}

      {/* Tamper signals */}
      {result.raw.tamper_signals && result.raw.tamper_signals.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="font-medium text-red-900 mb-2">Tamper signals detected</div>
          <ul className="space-y-1 text-sm text-red-800">
            {result.raw.tamper_signals.map((s, i) => (
              <li key={i}>
                <span className="font-mono text-xs bg-red-100 px-1.5 py-0.5 rounded">
                  {s.type}
                </span>{" "}
                {s.detail}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}


interface MetaPanelProps {
  title: string;
  tone: "success" | "danger" | "neutral";
  items: [string, string][];
}

function MetaPanel({ title, tone, items }: MetaPanelProps) {
  const toneClass =
    tone === "success"
      ? "border-emerald-200 bg-emerald-50/50"
      : tone === "danger"
      ? "border-red-200 bg-red-50/50"
      : "border-slate-200 bg-white";
  return (
    <div className={`rounded-xl border ${toneClass} p-4`}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500 mb-3">
        {title}
      </div>
      <dl className="space-y-1.5 text-sm">
        {items.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-3">
            <dt className="text-slate-500 shrink-0">{k}</dt>
            <dd className="text-slate-800 font-mono text-xs text-right break-all">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
