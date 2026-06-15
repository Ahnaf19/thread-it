"use client";

import { useCallback, useEffect, useState } from "react";

// The one async-state machine behind every client-fetched view (ADR-0009).
// A Resource is in exactly one status: idle (nothing to fetch yet), loading,
// ready (data in hand), or error. `null` is never overloaded to mean both
// "loading" and "failed" — that overload was the bug #31 fixes.
export type Resource<T> =
  | { status: "idle"; data: null; error: null }
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: T; error: null }
  | { status: "error"; data: null; error: Error };

type Options = {
  // When false, the resource stays idle and `load` is never called. Use for a
  // fetch that has no input yet (e.g. the cart view with an empty bag).
  enabled?: boolean;
  // Re-fetch whenever any of these change (like an effect dependency list).
  deps?: unknown[];
};

const IDLE = { status: "idle", data: null, error: null } as const;
const LOADING = { status: "loading", data: null, error: null } as const;

function sameDeps(a: unknown[], b: unknown[]): boolean {
  return a.length === b.length && a.every((v, i) => Object.is(v, b[i]));
}

export function useResource<T>(
  load: (signal: AbortSignal) => Promise<T>,
  options: Options = {},
): Resource<T> & { reload: () => void } {
  const { enabled = true, deps = [] } = options;

  const [nonce, setNonce] = useState(0);
  const reload = useCallback(() => setNonce((n) => n + 1), []);

  const [state, setState] = useState<Resource<T>>(enabled ? LOADING : IDLE);

  // Reset to loading/idle synchronously when the run identity changes (deps,
  // enabled, or a reload). React's documented "adjust state on input change"
  // pattern: setState during render, guarded by the previous run held in state.
  // (setState-in-effect cascades a render; refs can't be touched during render.)
  const run = { enabled, nonce, deps };
  const [prev, setPrev] = useState(run);
  if (prev.enabled !== enabled || prev.nonce !== nonce || !sameDeps(prev.deps, deps)) {
    setPrev(run);
    setState(enabled ? LOADING : IDLE);
  }

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    // `load` is captured from the render that scheduled this effect; by contract
    // it changes only when `deps` change, so the captured closure is current.
    load(controller.signal)
      .then((data) => {
        // Drop stale resolves: a superseded run's controller is already aborted.
        if (!controller.signal.aborted) setState({ status: "ready", data, error: null });
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        if (err instanceof Error && err.name === "AbortError") return;
        setState({
          status: "error",
          data: null,
          error: err instanceof Error ? err : new Error(String(err)),
        });
      });
    return () => controller.abort();
    // deps is intentionally spread; load is captured, not a dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, nonce, ...deps]);

  return { ...state, reload } as Resource<T> & { reload: () => void };
}
