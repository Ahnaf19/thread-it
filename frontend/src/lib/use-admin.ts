"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { clearToken, useAdminToken } from "@/components/admin-auth";
import { UnauthorizedError } from "@/lib/api";

// Token guard: returns the admin token, redirecting to /admin/login if absent.
export function useRequireAdmin(): string | null {
  const router = useRouter();
  const token = useAdminToken();
  useEffect(() => {
    if (token === null) router.replace("/admin/login");
  }, [token, router]);
  return token;
}

// Guard + cancellable fetch + 401→clear→login, in one place. Pass a STABLE
// fetcher (a module-level function, not an inline arrow) so the effect re-runs
// only on token change.
export function useAdminResource<T>(
  fetcher: (token: string) => Promise<T>,
): { token: string | null; data: T | null } {
  const router = useRouter();
  const token = useRequireAdmin();
  const [data, setData] = useState<T | null>(null);

  useEffect(() => {
    if (!token) return;
    let active = true;
    fetcher(token)
      .then((d) => {
        if (active) setData(d);
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) {
          clearToken();
          router.replace("/admin/login");
        }
      });
    return () => {
      active = false;
    };
  }, [token, router, fetcher]);

  return { token, data };
}
