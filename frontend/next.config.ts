import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Seed images come from picsum.photos; production shots from Supabase Storage.
    remotePatterns: [
      { protocol: "https", hostname: "picsum.photos" },
      { protocol: "https", hostname: "fastly.picsum.photos" },
      { protocol: "https", hostname: "*.supabase.co" },
    ],
  },
};

export default nextConfig;
