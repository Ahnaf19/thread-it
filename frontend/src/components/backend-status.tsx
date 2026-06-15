"use client";

import { useEffect, useState } from "react";

import { fetchHealth, type Health } from "@/lib/api";

type Status =
  | { state: "loading" }
  | { state: "ok"; health: Health }
  | { state: "error"; message: string };

// Fires the cold-start warm-up ping on mount and reports backend reachability.
// In v1 this doubles as the visible proof the cross-origin (CORS) wiring works.
export function BackendStatus() {
  const [status, setStatus] = useState<Status>({ state: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetchHealth(controller.signal)
      .then((health) => setStatus({ state: "ok", health }))
      .catch((err) => {
        if (err.name === "AbortError") return;
        setStatus({ state: "error", message: String(err.message ?? err) });
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-black/10 px-4 py-2 text-sm">
      <span
        className={
          "h-2.5 w-2.5 rounded-full " +
          (status.state === "ok"
            ? "bg-lime-400"
            : status.state === "error"
              ? "bg-red-500"
              : "animate-pulse bg-zinc-400")
        }
        aria-hidden
      />
      {status.state === "loading" && <span>Waking the backend…</span>}
      {status.state === "ok" && (
        <span>
          Backend live · <span className="text-zinc-500">{status.health.environment}</span>
        </span>
      )}
      {status.state === "error" && (
        <span className="text-red-600">Backend unreachable: {status.message}</span>
      )}
    </div>
  );
}
