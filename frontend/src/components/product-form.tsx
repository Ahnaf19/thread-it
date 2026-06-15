"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { ProductInput } from "@/lib/api";

const CATEGORIES = ["Tops", "Bottoms", "Outerwear", "Dresses", "Accessories"];
const SIZES = ["XS", "S", "M", "L", "XL", "XXL", "One Size"];

const EMPTY: ProductInput = {
  name: "",
  description: "",
  price: 0,
  category: "Tops",
  is_active: true,
  variants: [{ size: "M", stock: 0 }],
  images: [{ url: "", alt: "", position: 0 }],
};

export function ProductForm({
  initial,
  submitLabel,
  onSubmit,
}: {
  initial?: ProductInput;
  submitLabel: string;
  onSubmit: (input: ProductInput) => Promise<void>;
}) {
  const [form, setForm] = useState<ProductInput>(initial ?? EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof ProductInput>(key: K, value: ProductInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const images = form.images
        .filter((i) => i.url.trim())
        .map((i, position) => ({ ...i, position }));
      await onSubmit({ ...form, images });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
      setBusy(false);
    }
  }

  const field = "w-full border border-zinc-300 px-3 py-2 text-sm";

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      <div>
        <label className="mb-1 block text-sm font-medium">Name</label>
        <input
          className={field}
          value={form.name}
          onChange={(e) => set("name", e.target.value)}
          required
        />
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <label className="mb-1 block text-sm font-medium">Price (৳)</label>
          <input
            type="number"
            min={0}
            className={field}
            value={form.price}
            onChange={(e) => set("price", Number(e.target.value))}
            required
          />
        </div>
        <div className="flex-1">
          <label className="mb-1 block text-sm font-medium">Category</label>
          <select
            className={field}
            value={form.category}
            onChange={(e) => set("category", e.target.value)}
          >
            {CATEGORIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">Description</label>
        <textarea
          className={field}
          rows={3}
          value={form.description}
          onChange={(e) => set("description", e.target.value)}
        />
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-medium">Sizes &amp; stock</legend>
        {form.variants.map((v, i) => (
          <div key={i} className="mb-2 flex items-center gap-2">
            <select
              className={field + " max-w-32"}
              value={v.size}
              onChange={(e) =>
                set("variants", form.variants.map((x, j) => (j === i ? { ...x, size: e.target.value } : x)))
              }
            >
              {SIZES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
            <input
              type="number"
              min={0}
              className={field + " max-w-28"}
              value={v.stock}
              onChange={(e) =>
                set("variants", form.variants.map((x, j) => (j === i ? { ...x, stock: Number(e.target.value) } : x)))
              }
            />
            <button
              type="button"
              className="text-sm text-zinc-400 hover:text-[#1A1A1A]"
              onClick={() => set("variants", form.variants.filter((_, j) => j !== i))}
            >
              remove
            </button>
          </div>
        ))}
        <button
          type="button"
          className="text-sm underline underline-offset-4"
          onClick={() => set("variants", [...form.variants, { size: "S", stock: 0 }])}
        >
          + add size
        </button>
      </fieldset>

      <fieldset>
        <legend className="mb-2 text-sm font-medium">Image URLs</legend>
        {form.images.map((img, i) => (
          <div key={i} className="mb-2 flex items-center gap-2">
            <input
              className={field}
              placeholder="https://…"
              value={img.url}
              onChange={(e) =>
                set("images", form.images.map((x, j) => (j === i ? { ...x, url: e.target.value } : x)))
              }
            />
            <input
              className={field + " max-w-48"}
              placeholder="alt text"
              value={img.alt}
              onChange={(e) =>
                set("images", form.images.map((x, j) => (j === i ? { ...x, alt: e.target.value } : x)))
              }
            />
            <button
              type="button"
              className="text-sm text-zinc-400 hover:text-[#1A1A1A]"
              onClick={() => set("images", form.images.filter((_, j) => j !== i))}
            >
              remove
            </button>
          </div>
        ))}
        <button
          type="button"
          className="text-sm underline underline-offset-4"
          onClick={() => set("images", [...form.images, { url: "", alt: "", position: form.images.length }])}
        >
          + add image
        </button>
      </fieldset>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={form.is_active}
          onChange={(e) => set("is_active", e.target.checked)}
        />
        Active (visible in the storefront)
      </label>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <Button type="submit" disabled={busy} className="bg-lime-400 text-[#1A1A1A] hover:bg-lime-500">
        {busy ? "Saving…" : submitLabel}
      </Button>
    </form>
  );
}
