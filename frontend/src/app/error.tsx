"use client";

import { Button } from "@/components/ui/button";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#FAFAF8] px-6 text-center text-[#1A1A1A]">
      <h2 className="text-2xl font-semibold">Something went wrong</h2>
      <p className="max-w-sm text-zinc-500">
        We couldn’t load the collection. The store may be waking up — try again in a moment.
      </p>
      <Button onClick={reset} className="bg-lime-400 text-[#1A1A1A] hover:bg-lime-500">
        Try again
      </Button>
    </main>
  );
}
