import { describe, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";

import { useResource } from "./use-resource";

// A promise we resolve/reject by hand, to drive race scenarios deterministically.
function deferred<T>() {
  let resolve!: (v: T) => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe("useResource", () => {
  it("stays idle and does not fetch when disabled", () => {
    const load = vi.fn(async () => "x");
    const { result } = renderHook(() => useResource(load, { enabled: false }));

    expect(result.current.status).toBe("idle");
    expect(load).not.toHaveBeenCalled();
  });

  it("starts loading, then resolves to ready with data", async () => {
    const load = vi.fn(async () => "shirt");
    const { result } = renderHook(() => useResource(load));

    expect(result.current.status).toBe("loading");
    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.data).toBe("shirt");
    expect(load).toHaveBeenCalledTimes(1);
  });

  it("transitions to error (not a silent hang) when the fetch rejects", async () => {
    const boom = new Error("cold start timeout");
    const load = vi.fn(async () => {
      throw boom;
    });
    const { result } = renderHook(() => useResource(load));

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error).toBe(boom);
    expect(result.current.data).toBeNull();
  });

  it("reload() re-runs the fetch", async () => {
    const load = vi.fn(async () => "ok");
    const { result } = renderHook(() => useResource(load));

    await waitFor(() => expect(result.current.status).toBe("ready"));
    act(() => result.current.reload());
    await waitFor(() => expect(load).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(result.current.status).toBe("ready"));
  });

  it("ignores a stale resolve from a superseded run", async () => {
    const first = deferred<string>();
    const second = deferred<string>();
    const runs = [first, second];
    let i = 0;
    const load = vi.fn(() => runs[i++].promise);

    const { result } = renderHook(() => useResource(load));
    act(() => result.current.reload());

    // Resolve the latest run first, then the stale one — stale must not win.
    await act(async () => {
      second.resolve("new");
    });
    await act(async () => {
      first.resolve("old");
    });

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.data).toBe("new");
  });

  it("aborts the in-flight fetch on unmount", () => {
    let captured: AbortSignal | undefined;
    const load = vi.fn((signal: AbortSignal) => {
      captured = signal;
      return new Promise<string>(() => {});
    });
    const { unmount } = renderHook(() => useResource(load));

    expect(captured?.aborted).toBe(false);
    unmount();
    expect(captured?.aborted).toBe(true);
  });

  it("re-fetches when deps change", async () => {
    const load = vi.fn(async () => "v");
    let dep = 1;
    const { result, rerender } = renderHook(() => useResource(load, { deps: [dep] }));

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(load).toHaveBeenCalledTimes(1);

    dep = 2;
    rerender();
    await waitFor(() => expect(load).toHaveBeenCalledTimes(2));
  });
});
