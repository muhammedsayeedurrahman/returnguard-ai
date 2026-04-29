import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { submitClaim } from "../lib/api";
import VideoRecorder from "../components/VideoRecorder";

export default function ReturnForm() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [orderId, setOrderId] = useState(params.get("order") || "");
  const [reason, setReason] = useState(params.get("reason") || "damaged");
  const [text, setText] = useState(params.get("text") || "");
  const [photo, setPhoto] = useState<File | null>(null);
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [showRecorder, setShowRecorder] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("order_id", orderId);
      fd.append("reason_code", reason);
      fd.append("claim_text", text);
      if (photo) fd.append("photo", photo);
      if (videoBlob) {
        fd.append("video", videoBlob, "proof.webm");
        fd.append("capture_method", "live_camera");
      }
      const r = await submitClaim(fd);
      if (!r.ok) {
        setError(r.detail || "Submission failed");
        setSubmitting(false);
        return;
      }
      navigate(`/status/${r.data.claim_id}`);
    } catch (err) {
      setError(String(err));
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-900">File a return</h2>
        <p className="text-slate-600 mt-1 text-sm">
          We'll review and let you know in seconds.
        </p>
      </div>

      <form onSubmit={onSubmit} className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Order ID</label>
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="ord_legit_001"
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Reason</label>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          >
            <option value="damaged">Damaged on arrival</option>
            <option value="wrong_item">Wrong item received</option>
            <option value="not_received">Not received</option>
            <option value="receipt_tampered">Receipt issue</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Tell us what happened
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            placeholder="Briefly describe the issue…"
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Photo (optional)
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setPhoto(e.target.files?.[0] || null)}
            className="w-full text-sm text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Proof video (optional)
          </label>
          {!showRecorder && !videoBlob && (
            <button
              type="button"
              onClick={() => setShowRecorder(true)}
              className="w-full text-left px-3 py-2 border border-dashed border-slate-300 rounded-md text-sm text-slate-600 hover:bg-slate-50"
            >
              🎥 Record a short proof video (≤30s) — speeds up approval for high-value claims
            </button>
          )}
          {showRecorder && !videoBlob && (
            <VideoRecorder
              onRecorded={(blob) => {
                setVideoBlob(blob);
                setShowRecorder(false);
              }}
            />
          )}
          {videoBlob && (
            <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-md px-3 py-2">
              <span className="text-sm text-emerald-800 flex-1">
                ✓ Proof video attached ({(videoBlob.size / 1024).toFixed(0)} KB)
              </span>
              <button
                type="button"
                onClick={() => setVideoBlob(null)}
                className="text-xs text-emerald-700 hover:text-emerald-900"
              >
                Remove
              </button>
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md px-3 py-2">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-slate-900 text-white py-2.5 rounded-md font-medium hover:bg-slate-800 disabled:opacity-50 transition"
        >
          {submitting ? "Reviewing…" : "Submit return request"}
        </button>
      </form>
    </div>
  );
}
