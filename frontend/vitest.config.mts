import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

// Frontend unit tests (Vitest + React Testing Library), per the bundled Next 16
// testing guide. We test client logic only — the async-state hook (ADR-0009);
// async Server Components are not unit-testable and stay light-touch.
export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
