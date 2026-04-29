import { useEffect, useRef, useState } from "react";

interface VideoRecorderProps {
  /** Called once the customer accepts the recording. */
  onRecorded: (blob: Blob, durationSeconds: number) => void;
  /** Hard cap in seconds (default 30). */
  maxSeconds?: number;
}

type RecorderState = "idle" | "ready" | "recording" | "preview" | "denied" | "unsupported";

const PREFERRED_MIME = "video/webm;codecs=vp8,opus";

/**
 * Customer-side proof-of-receipt video recorder.
 *
 * - Uses navigator.mediaDevices.getUserMedia (camera + mic).
 * - MediaRecorder produces WebM; hard-stops at maxSeconds.
 * - Re-record allowed before submission.
 * - Graceful failure: if camera blocked or unsupported, reports state to parent
 *   so the form can still submit photo-only.
 */
export function VideoRecorder({ onRecorded, maxSeconds = 30 }: VideoRecorderProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const startedAtRef = useRef<number>(0);
  const stopTimerRef = useRef<number | null>(null);

  const [state, setState] = useState<RecorderState>("idle");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedDuration, setRecordedDuration] = useState(0);

  // Cleanup tracks + URLs on unmount
  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (stopTimerRef.current) window.clearTimeout(stopTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Tick the recording timer
  useEffect(() => {
    if (state !== "recording") return;
    const t = window.setInterval(() => {
      setElapsed((Date.now() - startedAtRef.current) / 1000);
    }, 100);
    return () => window.clearInterval(t);
  }, [state]);

  async function requestCamera() {
    if (typeof navigator === "undefined" || !navigator.mediaDevices) {
      setState("unsupported");
      return;
    }
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: true,
      });
      streamRef.current = s;
      if (videoRef.current) {
        videoRef.current.srcObject = s;
        videoRef.current.play().catch(() => {/* autoplay sometimes throws on Safari */});
      }
      setState("ready");
    } catch {
      setState("denied");
    }
  }

  function startRecording() {
    if (!streamRef.current) return;
    chunksRef.current = [];
    const mime = MediaRecorder.isTypeSupported(PREFERRED_MIME) ? PREFERRED_MIME : "";
    let recorder: MediaRecorder;
    try {
      recorder = mime
        ? new MediaRecorder(streamRef.current, { mimeType: mime })
        : new MediaRecorder(streamRef.current);
    } catch {
      setState("unsupported");
      return;
    }
    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mime || "video/webm" });
      const duration = (Date.now() - startedAtRef.current) / 1000;
      setRecordedBlob(blob);
      setRecordedDuration(duration);
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      setState("preview");
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };

    startedAtRef.current = Date.now();
    recorder.start(500);
    recorderRef.current = recorder;
    setElapsed(0);
    setState("recording");

    // Hard-stop at max duration
    stopTimerRef.current = window.setTimeout(stopRecording, maxSeconds * 1000);
  }

  function stopRecording() {
    if (stopTimerRef.current) {
      window.clearTimeout(stopTimerRef.current);
      stopTimerRef.current = null;
    }
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
  }

  function reRecord() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setRecordedBlob(null);
    setRecordedDuration(0);
    setState("idle");
  }

  function submit() {
    if (recordedBlob) onRecorded(recordedBlob, recordedDuration);
  }

  if (state === "unsupported") {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm text-slate-600">
        Video recording isn't supported on this browser. You can still submit a photo.
      </div>
    );
  }
  if (state === "denied") {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
        Camera access blocked. You can submit a photo only.{" "}
        <button onClick={requestCamera} className="underline font-medium">
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="bg-slate-900 rounded-lg overflow-hidden relative" style={{ aspectRatio: "4/3" }}>
        {state === "preview" && previewUrl ? (
          <video
            src={previewUrl}
            controls
            className="w-full h-full object-cover"
          />
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
        )}

        {state === "recording" && (
          <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/70 text-white rounded-full px-3 py-1 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            REC {elapsed.toFixed(1)}s / {maxSeconds}s
          </div>
        )}
        {state === "preview" && (
          <div className="absolute top-3 left-3 bg-emerald-600 text-white rounded-full px-3 py-1 text-xs font-mono">
            ✓ Recorded {recordedDuration.toFixed(1)}s
          </div>
        )}
      </div>

      <div className="flex gap-2">
        {state === "idle" && (
          <button
            type="button"
            onClick={requestCamera}
            className="flex-1 px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700"
          >
            🎥 Open camera to record proof
          </button>
        )}
        {state === "ready" && (
          <button
            type="button"
            onClick={startRecording}
            className="flex-1 px-4 py-2 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-700"
          >
            ● Start recording
          </button>
        )}
        {state === "recording" && (
          <button
            type="button"
            onClick={stopRecording}
            className="flex-1 px-4 py-2 rounded-md bg-slate-900 text-white text-sm font-medium hover:bg-slate-800"
          >
            ■ Stop
          </button>
        )}
        {state === "preview" && (
          <>
            <button
              type="button"
              onClick={reRecord}
              className="flex-1 px-4 py-2 rounded-md border border-slate-300 text-sm font-medium hover:bg-slate-50"
            >
              ↻ Re-record
            </button>
            <button
              type="button"
              onClick={submit}
              className="flex-1 px-4 py-2 rounded-md bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700"
            >
              ✓ Use this video
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default VideoRecorder;
