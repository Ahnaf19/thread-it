import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#FAFAF8] px-6 text-center text-[#1A1A1A]">
      <h2 className="text-2xl font-semibold">Not found</h2>
      <p className="text-zinc-500">That product doesn’t exist or is no longer available.</p>
      <Link href="/" className="text-sm underline underline-offset-4">
        Back to the collection
      </Link>
    </main>
  );
}
