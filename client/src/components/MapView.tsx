import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import { adminMap } from "../lib/api";

interface MapPoint {
  claim_id: string;
  customer_id: string;
  decision: string;
  score: number;
  ring_cluster_id: string | null;
  product_name: string;
  value_inr: number;
  address: string;
  pincode: string;
  lat: number;
  lng: number;
}

const ringIcon = L.divIcon({
  className: "",
  html: '<div class="map-ring-pin"></div>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});
const legitIcon = L.divIcon({
  className: "",
  html: '<div class="map-legit-pin"></div>',
  iconSize: [11, 11],
  iconAnchor: [5.5, 5.5],
});
const rejectIcon = L.divIcon({
  className: "",
  html: '<div class="map-reject-pin"></div>',
  iconSize: [13, 13],
  iconAnchor: [6.5, 6.5],
});
const borderlineIcon = L.divIcon({
  className: "",
  html: '<div class="map-borderline-pin"></div>',
  iconSize: [12, 12],
  iconAnchor: [6, 6],
});

function pickIcon(p: MapPoint) {
  if (p.ring_cluster_id) return ringIcon;
  if (p.decision === "REJECT") return rejectIcon;
  if (p.decision === "BORDERLINE") return borderlineIcon;
  return legitIcon;
}

/**
 * Spread overlapping ring pins by tiny offset so each is individually clickable.
 * Same ring → 4 pins overlap at one address; we fan them on a small circle.
 */
function jitterRingPins(points: MapPoint[]): MapPoint[] {
  const ringGroups = new Map<string, MapPoint[]>();
  for (const p of points) {
    if (p.ring_cluster_id) {
      const arr = ringGroups.get(p.ring_cluster_id) || [];
      arr.push(p);
      ringGroups.set(p.ring_cluster_id, arr);
    }
  }
  return points.map((p) => {
    if (!p.ring_cluster_id) return p;
    const group = ringGroups.get(p.ring_cluster_id) || [p];
    const idx = group.findIndex((q) => q.claim_id === p.claim_id);
    const angle = (idx / Math.max(group.length, 1)) * 2 * Math.PI;
    const r = 0.0008; // ~80m offset
    return {
      ...p,
      lat: p.lat + Math.cos(angle) * r,
      lng: p.lng + Math.sin(angle) * r,
    };
  });
}

export default function MapView() {
  const [points, setPoints] = useState<MapPoint[]>([]);

  useEffect(() => {
    let live = true;
    async function load() {
      const r = await adminMap();
      if (live && r.ok) setPoints(r.data);
    }
    load();
    const t = setInterval(load, 3000);
    return () => {
      live = false;
      clearInterval(t);
    };
  }, []);

  const jittered = useMemo(() => jitterRingPins(points), [points]);

  const ringCount = points.filter((p) => p.ring_cluster_id).length;
  const legitCount = points.filter(
    (p) => !p.ring_cluster_id && p.decision === "APPROVE",
  ).length;
  const flaggedCount = points.length - ringCount - legitCount;

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
        <div>
          <div className="font-medium text-slate-900">Geographic distribution</div>
          <div className="text-xs text-slate-500">
            Ring members cluster geographically — legit customers spread across India
          </div>
        </div>
        <div className="flex gap-3 text-xs">
          <Legend dot="bg-emerald-500" label={`legit (${legitCount})`} />
          <Legend dot="bg-indigo-500" label={`borderline+rejected (${flaggedCount})`} />
          <Legend dot="bg-red-600" pulse label={`ring (${ringCount})`} />
        </div>
      </div>
      <div style={{ height: 420 }}>
        <MapContainer
          center={[22.0, 79.0]}
          zoom={4}
          scrollWheelZoom={true}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {jittered.map((p) => (
            <Marker key={p.claim_id} position={[p.lat, p.lng]} icon={pickIcon(p)}>
              <Popup>
                <div className="text-sm" style={{ minWidth: 200 }}>
                  <div className="font-mono text-xs text-slate-500">{p.customer_id}</div>
                  <div className="font-medium text-slate-800">{p.product_name}</div>
                  <div className="text-xs text-slate-600 mt-1">{p.address}</div>
                  <div className="mt-2 flex items-center gap-2 text-xs">
                    <span className="font-mono">score: {p.score}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded ${
                        p.decision === "APPROVE"
                          ? "bg-emerald-100 text-emerald-700"
                          : p.decision === "REJECT"
                          ? "bg-red-100 text-red-700"
                          : "bg-indigo-100 text-indigo-700"
                      }`}
                    >
                      {p.decision}
                    </span>
                  </div>
                  {p.ring_cluster_id && (
                    <div className="mt-2 text-xs font-mono text-red-700">
                      {p.ring_cluster_id}
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

interface LegendProps {
  dot: string;
  label: string;
  pulse?: boolean;
}

function Legend({ dot, label, pulse }: LegendProps) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className={`w-2.5 h-2.5 rounded-full ${dot} ${
          pulse ? "animate-pulse" : ""
        }`}
      />
      <span className="text-slate-600">{label}</span>
    </div>
  );
}
