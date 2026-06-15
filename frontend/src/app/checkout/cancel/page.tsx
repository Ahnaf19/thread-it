import Link from "next/link";

export default function CheckoutCancelPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#FAFAF8] px-6 text-center text-[#1A1A1A]">
      <h1 className="text-3xl font-bold tracking-tight">Checkout cancelled</h1>
      <p className="max-w-sm text-zinc-600">No payment was made. Your bag is still here when you’re ready.</p>
      <Link href="/cart" className="mt-2 text-sm underline underline-offset-4">
        Back to your bag
      </Link>
    </main>
  );
}
