import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        muted: "hsl(var(--muted))",
        border: "hsl(var(--border))",
        panel: "hsl(var(--panel))",
        cyan: "hsl(var(--cyan))",
        amber: "hsl(var(--amber))",
        coral: "hsl(var(--coral))",
        success: "hsl(var(--success))"
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "ui-sans-serif", "system-ui"]
      },
      boxShadow: {
        glow: "0 0 48px rgba(95, 220, 255, 0.16)",
        panel: "0 24px 80px rgba(0, 0, 0, 0.36)"
      }
    }
  },
  plugins: []
};

export default config;

