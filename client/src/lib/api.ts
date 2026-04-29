const BASE = "/api/v1";

export async function getOrder(orderId: string) {
  const r = await fetch(`${BASE}/orders/${orderId}`);
  return r.json();
}

export async function submitClaim(form: FormData) {
  const r = await fetch(`${BASE}/claims`, {
    method: "POST",
    body: form,
  });
  return r.json();
}

export async function getClaim(claimId: string) {
  const r = await fetch(`${BASE}/claims/${claimId}`);
  return r.json();
}

export async function takeTurn(sessionId: string, message: string, photo?: File) {
  const fd = new FormData();
  fd.append("message", message);
  if (photo) fd.append("photo", photo);
  const r = await fetch(`${BASE}/evaluation/${sessionId}/turn`, {
    method: "POST",
    body: fd,
  });
  return r.json();
}

export async function adminQueue() {
  const r = await fetch(`${BASE}/admin/queue`);
  return r.json();
}

export async function adminRings() {
  const r = await fetch(`${BASE}/admin/rings`);
  return r.json();
}

export async function adminStats() {
  const r = await fetch(`${BASE}/admin/stats`);
  return r.json();
}

export async function adminMap() {
  const r = await fetch(`${BASE}/admin/map`);
  return r.json();
}

export async function adminReview(claimId: string, outcome: "CONFIRMED_LEGIT" | "CONFIRMED_FRAUD" | "ESCALATED", notes = "") {
  const fd = new FormData();
  fd.append("claim_id", claimId);
  fd.append("outcome", outcome);
  fd.append("notes", notes);
  const r = await fetch(`${BASE}/admin/review`, { method: "POST", body: fd });
  return r.json();
}

export async function verifyReceipt(orderId: string, file: File) {
  const fd = new FormData();
  fd.append("order_id", orderId);
  fd.append("receipt", file);
  const r = await fetch(`${BASE}/receipts/verify`, { method: "POST", body: fd });
  return r.json();
}
