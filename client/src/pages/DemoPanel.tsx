import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitClaim } from "../lib/api";

type Scenario = {
  key: string;
  label: string;
  description: string;
  orderId: string;
  reasonCode: string;
  claimText: string;
  photoFilename: string | null;
  expectedDecision: "APPROVE" | "BORDERLINE" | "REJECT";
  color: string;
};

const SCENARIOS: Scenario[] = [
  {
    key: "maya",
    label: "Run Maya (legit)",
    description: "Honest customer, damaged earbuds. Expect: instant approve.",
    orderId: "ord_legit_000",
    reasonCode: "damaged",
    claimText:
      "The earbuds case has a small crack near the hinge, came like that out of the package",
    photoFilename: null,
    expectedDecision: "APPROVE",
    color: "bg-emerald-600 hover:bg-emerald-700",
  },
  {
    key: "priya",
    label: "Run Priya (borderline)",
    description:
      "Damage claim with EXIF-fail photo. Engine escalates to AI specialist.",
    orderId: "ord_priya_001",
    reasonCode: "damaged",
    claimText:
      "Earbuds arrived with major water damage on the speaker, completely unusable",
    photoFilename: "priya_exif_fail.jpg",
    expectedDecision: "BORDERLINE",
    color: "bg-indigo-600 hover:bg-indigo-700",
  },
  {
    key: "ring4",
    label: "Run Ring (4th member)",
    description:
      "Final ring-claim submission triggers cluster detection across 4 accounts.",
    orderId: "ord_ring_04",
    reasonCode: "damaged",
    claimText:
      "Item arrived but it's not as described in the listing. Quality is poor and packaging was tampered. Please refund or replace urgently.",
    photoFilename: null,
    expectedDecision: "REJECT",
    color: "bg-red-600 hover:bg-red-700",
  },
  {
    key: "wardrobing",
    label: "Run Wardrobing (₹45K lehenga, returned 1 day later)",
    description:
      "High-value apparel returned 1 day after delivery during wedding season — classic wardrobing.",
    orderId: "ord_wardrobing_001",
    reasonCode: "damaged",
    claimText: "The lehenga doesn't fit as expected, returning it.",
    photoFilename: null,
    expectedDecision: "BORDERLINE",
    color: "bg-amber-600 hover:bg-amber-700",
  },
  {
    key: "friendly_fraud",
    label: "Run Friendly Fraud (3 prior chargebacks)",
    description:
      "Customer with 3 prior chargebacks files an INR claim on a ₹1.3 lakh iPhone.",
    orderId: "ord_friendly_001",
    reasonCode: "not_received",
    claimText: "I never received this order.",
    photoFilename: null,
    expectedDecision: "REJECT",
    color: "bg-purple-600 hover:bg-purple-700",
  },
  {
    key: "inr_abuse",
    label: "Run INR Abuse (claim 1h after delivery)",
    description:
      "Customer with 2 prior INR claims files another, 1 hour after carrier GPS-confirmed delivery.",
    orderId: "ord_inr_001",
    reasonCode: "not_received",
    claimText: "Package shows delivered but I was home all day, nothing arrived.",
    photoFilename: null,
    expectedDecision: "REJECT",
    color: "bg-pink-600 hover:bg-pink-700",
  },
];

export default function DemoPanel() {
  const navigate = useNavigate();
  const [running, setRunning] = useState<string | null>(null);

  async function runScenario(s: Scenario) {
    setRunning(s.key);
    const fd = new FormData();
    fd.append("order_id", s.orderId);
    fd.append("reason_code", s.reasonCode);
    fd.append("claim_text", s.claimText);
    if (s.photoFilename) {
      // Synthesize a tiny fake JPEG with the right filename so mock vision picks it up
      const blob = new Blob(["fake-photo-bytes"], { type: "image/jpeg" });
      fd.append("photo", new File([blob], s.photoFilename, { type: "image/jpeg" }));
    }
    try {
      const r = await submitClaim(fd);
      if (r.ok) {
        navigate(`/status/${r.data.claim_id}`);
      } else {
        alert("Failed: " + JSON.stringify(r));
      }
    } finally {
      setRunning(null);
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Demo Control Panel</h2>
        <p className="text-slate-600 text-sm mt-1">
          One-click scenarios for the live pitch. Each runs in under 5 seconds.
        </p>
      </div>

      <div className="space-y-3">
        {SCENARIOS.map((s) => (
          <div
            key={s.key}
            className="bg-white border border-slate-200 rounded-xl p-5 flex items-center gap-4"
          >
            <div className="flex-1">
              <div className="font-medium text-slate-900">{s.label}</div>
              <div className="text-sm text-slate-600 mt-1">{s.description}</div>
              <div className="text-xs text-slate-400 mt-2 font-mono">
                Order: {s.orderId} · Reason: {s.reasonCode} · Expect:{" "}
                {s.expectedDecision}
              </div>
            </div>
            <button
              onClick={() => runScenario(s)}
              disabled={running !== null}
              className={`text-white px-4 py-2 rounded-md font-medium text-sm transition ${s.color} disabled:opacity-50`}
            >
              {running === s.key ? "Running…" : "Run"}
            </button>
          </div>
        ))}
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
        <div className="font-medium mb-1">Pitch tip</div>
        Run Maya first (legit, ~3s). Then Priya (chat opens, AI engine resolves).
        Then Ring (open admin tab in second window — graph lights up). Total: 90 seconds.
      </div>

      <div className="text-center text-sm text-slate-500">
        Open <a href="/admin" className="text-indigo-600 underline">/admin</a> in a
        second tab to watch the queue + ring graph fill in real-time.
      </div>
    </div>
  );
}
