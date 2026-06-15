"use client";

import { useEffect } from "react";

import { API_URL } from "@/lib/api";

// Cold-start mitigation: fire a cheap /health request on load to wake Render's
// free tier while the user browses. Renders nothing (silent); failures ignored.
export function WarmUpPing() {
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}/health`, { signal: controller.signal }).catch(() => {});
    return () => controller.abort();
  }, []);
  return null;
}
