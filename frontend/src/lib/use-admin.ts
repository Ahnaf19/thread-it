"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { clearToken, useAdminToken } from "@/components/admin-auth";
import { UnauthorizedError } from "@/lib/api";
import { type Resource, useResource } from "@/lib/use-resource";

// Token guard: returns the admin token, redirecting to /admin/login if absent.
export function useRequireAdmin(): string | null {
  const router = useRouter();
  const token = useAdminToken();
  useEffect(() => {
    if (token === null) router.replace("/admin/login");
  }, [token, router]);
  return token;
}

// Guard + the async-state machine (ADR-0009) + 401→clear→login, in one place.
// Returns the full Resource (status/data/error/reload) so callers render
// loading / empty / error consistently. A 401 is NOT surfaced as an error: we
// clear the session and bounce to login, masking it as `loading` while we go.
export function useAdminResource<T>(
  fetcher: (token: string) => Promise<T>,
): Resource<T> & { token: string | null; reload: () => void } {
  const router = useRouter();
  const token = useRequireAdmin();

  const resource = useResource<T>(() => fetcher(token as string), {
    enabled: token !== null,
    deps: [token],
  });

  const isAuthError =
    resource.status === "error" && resource.error instanceof UnauthorizedError;

  useEffect(() => {
    if (isAuthError) {
      clearToken();
      router.replace("/admin/login");
    }
  }, [isAuthError, router]);

  if (isAuthError) {
    return { token, status: "loading", data: null, error: null, reload: resource.reload };
  }
  return { token, ...resource };
}
