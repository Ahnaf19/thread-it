import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";

import { clearToken, getToken, setToken } from "@/components/admin-auth";
import { UnauthorizedError } from "@/lib/api";
import { useAdminResource } from "@/lib/use-admin";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
}));

beforeEach(() => {
  replace.mockClear();
  clearToken();
  localStorage.clear();
});

afterEach(() => {
  clearToken();
});

describe("useAdminResource", () => {
  it("redirects to login and does not fetch when there is no token", async () => {
    const fetcher = vi.fn(async () => ["product"]);
    const { result } = renderHook(() => useAdminResource(fetcher));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/admin/login"));
    expect(fetcher).not.toHaveBeenCalled();
    expect(result.current.token).toBeNull();
  });

  it("fetches with the token and reaches ready", async () => {
    setToken("tok");
    const fetcher = vi.fn(async (token: string) => `data-for-${token}`);
    const { result } = renderHook(() => useAdminResource(fetcher));

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.data).toBe("data-for-tok");
    expect(fetcher).toHaveBeenCalledWith("tok");
  });

  it("surfaces a non-401 failure as an error state (no silent hang)", async () => {
    setToken("tok");
    const fetcher = vi.fn(async () => {
      throw new Error("500");
    });
    const { result } = renderHook(() => useAdminResource(fetcher));

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(replace).not.toHaveBeenCalled();
    expect(getToken()).toBe("tok"); // session not cleared on a plain error
  });

  it("clears the session and redirects on a 401, without showing an error", async () => {
    setToken("tok");
    const fetcher = vi.fn(async () => {
      throw new UnauthorizedError("Session expired");
    });
    const { result } = renderHook(() => useAdminResource(fetcher));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/admin/login"));
    expect(getToken()).toBeNull();
    expect(result.current.status).not.toBe("error");
  });
});
