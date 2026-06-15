import { BackendStatus } from "@/components/backend-status";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-start justify-center gap-8 bg-[#FAFAF8] px-8 py-24 text-[#1A1A1A] sm:px-16">
      <BackendStatus />
      <h1 className="max-w-4xl text-6xl font-bold leading-[0.95] tracking-tight sm:text-8xl">
        Thread It<span className="text-lime-400">.</span>
      </h1>
      <p className="max-w-md text-lg leading-7 text-zinc-600">
        A single-shop apparel storefront. This is the v1 pipeline slice — frontend on
        Vercel, API on Render, talking across CORS. The storefront comes next.
      </p>
    </main>
  );
}
