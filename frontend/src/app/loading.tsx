import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 sm:px-10">
      <Skeleton className="mb-10 h-16 w-64" />
      <div className="grid grid-cols-2 gap-x-5 gap-y-10 md:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i}>
            <Skeleton className="aspect-[4/5] w-full" />
            <Skeleton className="mt-3 h-4 w-3/4" />
          </div>
        ))}
      </div>
    </main>
  );
}
