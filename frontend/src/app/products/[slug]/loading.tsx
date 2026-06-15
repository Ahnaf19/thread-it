import { Skeleton } from "@/components/ui/skeleton";

// Detail-shaped loading state (two columns), so navigating to a product doesn't
// flash the root grid skeleton (which is the list shape, not the detail shape).
export default function Loading() {
  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 sm:px-10">
      <Skeleton className="h-4 w-16" />
      <div className="mt-6 grid gap-10 md:grid-cols-2">
        <Skeleton className="aspect-[4/5] w-full" />
        <div className="flex flex-col gap-4 md:pt-2">
          <Skeleton className="h-9 w-2/3" />
          <Skeleton className="h-6 w-24" />
          <Skeleton className="mt-4 h-20 w-full" />
          <Skeleton className="mt-4 h-11 w-full max-w-xs" />
        </div>
      </div>
    </main>
  );
}
