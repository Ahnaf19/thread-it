// Backend API base URL. Set NEXT_PUBLIC_API_URL in Vercel env settings to the
// Render backend URL (e.g. https://thread-it-api.onrender.com). Falls back to
// the local FastAPI dev server.
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Health = {
  status: string;
  service: string;
  environment: string;
};

// Cold-start warm-up: Render's free tier spins down after ~15 min idle, so the
// next request waits ~30-50s while it boots. We ping /health on page load to
// warm it while the user reads the page. A mitigation, not a fix.
export async function fetchHealth(signal?: AbortSignal): Promise<Health> {
  const res = await fetch(`${API_URL}/health`, { signal });
  if (!res.ok) {
    throw new Error(`Backend returned ${res.status}`);
  }
  return res.json();
}
