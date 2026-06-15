import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

// Shared loading / error shells for client-fetched views (ADR-0009). Empty
// states stay inline per page — the copy is too view-specific to share.

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4 py-20 text-center">
      <p className="text-lg font-medium">{title}</p>
      <p className="max-w-sm text-sm text-zinc-500">{message}</p>
      {onRetry && (
        <Button onClick={onRetry} className="bg-lime-400 text-[#1A1A1A] hover:bg-lime-500">
          Try again
        </Button>
      )}
    </div>
  );
}

// Shape-matched skeleton for the admin tables.
export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-hidden>
      <Skeleton className="h-6 w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

// Shape-matched skeleton for the cart line-item list.
export function CartSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="divide-y divide-black/10" aria-hidden>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 py-5">
          <Skeleton className="h-24 w-20 shrink-0" />
          <div className="flex flex-1 flex-col gap-3">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-4 w-1/5" />
            <Skeleton className="mt-auto h-8 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}
