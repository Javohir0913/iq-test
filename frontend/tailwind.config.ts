import type { Config } from "tailwindcss";

const token = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: ["class"],
  theme: {
    extend: {
      colors: {
        ink: token("ink"),
        accent: token("accent"),
        "accent-strong": token("accent-strong"),
        teal: token("teal"),
        soft: token("soft"),
        panel: token("panel"),
        page: token("page"),
        line: token("line"),
        muted: token("muted"),
        surface: token("surface"),
        "surface-2": token("surface-2"),
        // Savol rasmlari uchun doim och yuza (qorong‘i rejimda ham)
        paper: token("paper"),
        "paper-panel": token("paper-panel"),
        "paper-ink": token("paper-ink"),
        "paper-line": token("paper-line"),
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "14px",
        panel: "18px",
        btn: "12px",
      },
      boxShadow: {
        soft: "0 1px 2px rgb(var(--shadow) / 0.06), 0 8px 24px -12px rgb(var(--shadow) / 0.18)",
        lift: "0 2px 4px rgb(var(--shadow) / 0.06), 0 18px 40px -16px rgb(var(--shadow) / 0.28)",
        glow: "0 0 0 4px rgb(var(--accent) / 0.18), 0 16px 32px -12px rgb(var(--accent) / 0.45)",
      },
      keyframes: {
        shimmer: { "100%": { transform: "translateX(100%)" } },
      },
      animation: {
        shimmer: "shimmer 1.6s infinite",
      },
    },
  },
  plugins: [],
};

export default config;
