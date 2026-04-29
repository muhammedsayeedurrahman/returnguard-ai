import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminQueue, adminRings, adminStats, adminReview } from "../lib/api";
import MapView from "../components/MapView";

export default function AdminDashboard() {
  const [queue, setQueue] = useState<any[]>([]);
  const [rings, setRings] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);

  async function refresh() {
    const [q, r, s] = await Promise.all([adminQueue(), adminRings(), adminStats()]);
    if (q.ok) setQueue(q.data);
    if (r.ok) setRings(r.data);
    if (s.ok) setStats(s.data);
  }

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Fraud Operations</h2>
        <p className="text-slate-600 mt-1 text-sm">
          Live queue · ring clusters · evidence trails
        </p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatCard label="Total claims" value={stats.total_claims} />
          <StatCard label="Approved" value={stats.approved} color="text-emerald-600" />
          <StatCard label="Borderline" value={stats.borderline} color="text-indigo-600" />
          <StatCard label="Rejected" value={stats.rejected} color="text-red-600" />
          <StatCard
            label="Ring exposure"
            value={`₹${Math.round(stats.exposure_inr).toLocaleString("en-IN")}`}
            color="text-amber-600"
          />
        </div>
      )}

      {/* Map view — geographic distribution */}
      <MapView />

      {/* Ring clusters */}
      <div className="bg-white rounded-xl border border-slate-200">
        <div className="px-5 py-3 border-b border-slate-200">
          <div className="font-medium text-slate-900">Ring clusters detected</div>
          <div className="text-xs text-slate-500">
            Auto-frozen via linguistic + address fingerprint
          </div>
        </div>
        {rings.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-slate-500">
            No active ring clusters.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {rings.map((r) => (
              <div key={r.id} className="px-5 py-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className="text-xs font-mono bg-red-100 text-red-700 px-2 py-1 rounded">
                      {r.id}
                    </span>
                    <span className="ml-2 text-sm font-medium text-slate-800">
                      {r.customer_ids.length} accounts ·{" "}
                      <span className="text-amber-700">
                        ₹{Math.round(r.exposure_inr).toLocaleString("en-IN")}
                      </span>{" "}
                      exposure
                    </span>
                  </div>
                  <span className="text-xs text-slate-500">{r.shared_signal}</span>
                </div>
                <RingGraph customerIds={r.customer_ids} />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Queue */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-200">
          <div className="font-medium text-slate-900">Claim queue</div>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs font-medium text-slate-600">
            <tr>
              <th className="px-5 py-2">Claim</th>
              <th className="px-5 py-2">Customer</th>
              <th className="px-5 py-2">Product</th>
              <th className="px-5 py-2">Score</th>
              <th className="px-5 py-2">Decision</th>
              <th className="px-5 py-2">Ring</th>
              <th className="px-5 py-2 text-right">Review</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {queue.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50">
                <td className="px-5 py-2 font-mono text-xs text-slate-600">
                  <Link to={`/admin/claim/${c.id}`} className="text-indigo-600 hover:underline">
                    {c.id}
                  </Link>
                </td>
                <td className="px-5 py-2 text-slate-700">{c.customer_id}</td>
                <td className="px-5 py-2 text-slate-700">{c.product_name}</td>
                <td className="px-5 py-2">
                  <span
                    className={`font-mono ${
                      c.score >= 65
                        ? "text-red-600"
                        : c.score >= 35
                        ? "text-indigo-600"
                        : "text-emerald-600"
                    }`}
                  >
                    {c.score}
                  </span>
                </td>
                <td className="px-5 py-2">
                  <DecisionBadge decision={c.decision} />
                </td>
                <td className="px-5 py-2 text-xs text-amber-700">
                  {c.ring_cluster_id || "—"}
                </td>
                <td className="px-5 py-2 text-right">
                  <div className="inline-flex gap-1">
                    <button
                      onClick={async () => {
                        await adminReview(c.id, "CONFIRMED_LEGIT");
                        refresh();
                      }}
                      className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded hover:bg-emerald-200 transition"
                      title="Mark legit"
                    >✓ Legit</button>
                    <button
                      onClick={async () => {
                        await adminReview(c.id, "CONFIRMED_FRAUD");
                        refresh();
                      }}
                      className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded hover:bg-red-200 transition"
                      title="Mark fraud"
                    >✗ Fraud</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatCard({ label, value, color = "text-slate-900" }: any) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl px-4 py-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`text-2xl font-semibold mt-1 ${color}`}>{value}</div>
    </div>
  );
}

function DecisionBadge({ decision }: { decision: string }) {
  const map: Record<string, string> = {
    APPROVE: "bg-emerald-100 text-emerald-700",
    BORDERLINE: "bg-indigo-100 text-indigo-700",
    REJECT: "bg-red-100 text-red-700",
    ESCALATE: "bg-amber-100 text-amber-800",
  };
  return (
    <span
      className={`text-xs px-2 py-0.5 rounded-md font-medium ${
        map[decision] || "bg-slate-100 text-slate-600"
      }`}
    >
      {decision || "—"}
    </span>
  );
}

/** Tiny inline SVG ring visualisation — nodes around a circle, all connected. */
function RingGraph({ customerIds }: { customerIds: string[] }) {
  const n = customerIds.length;
  const cx = 200;
  const cy = 80;
  const r = 60;
  const positions = customerIds.map((_, i) => {
    const a = (i / n) * 2 * Math.PI - Math.PI / 2;
    return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
  });
  return (
    <svg viewBox="0 0 400 160" className="w-full max-w-md">
      {positions.map((p, i) =>
        positions.map((q, j) =>
          j > i ? (
            <line
              key={`${i}-${j}`}
              x1={p.x}
              y1={p.y}
              x2={q.x}
              y2={q.y}
              stroke="#dc2626"
              strokeWidth={1.5}
              strokeOpacity={0.6}
              className="ring-link"
            />
          ) : null,
        ),
      )}
      {positions.map((p, i) => (
        <g key={i}>
          <circle
            cx={p.x}
            cy={p.y}
            r={14}
            fill="#dc2626"
            className="ring-node"
          />
          <text
            x={p.x}
            y={p.y + 4}
            fontSize={10}
            fill="white"
            textAnchor="middle"
            fontFamily="monospace"
          >
            {customerIds[i].slice(-2)}
          </text>
          <text
            x={p.x}
            y={p.y + 28}
            fontSize={9}
            fill="#475569"
            textAnchor="middle"
            fontFamily="monospace"
          >
            {customerIds[i]}
          </text>
        </g>
      ))}
    </svg>
  );
}
