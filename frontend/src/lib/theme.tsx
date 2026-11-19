"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

export type ThemeChoice = "light" | "dark" | "system";
const KEY = "theme";

interface ThemeValue {
  choice: ThemeChoice;
  resolved: "light" | "dark";
  setChoice: (c: ThemeChoice) => void;
  /** Telegram mavzusi (foydalanuvchi qo‘lda tanlamagan bo‘lsa ishlatiladi) */
  setExternalScheme: (s: "light" | "dark" | null) => void;
}

const ThemeContext = createContext<ThemeValue | null>(null);

function systemDark() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [choice, setChoiceState] = useState<ThemeChoice>("system");
  const [external, setExternal] = useState<"light" | "dark" | null>(null);
  const [sysDark, setSysDark] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(KEY) as ThemeChoice | null;
      if (saved === "light" || saved === "dark" || saved === "system") setChoiceState(saved);
    } catch {
      /* e’tiborsiz */
    }
    setSysDark(systemDark());
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e: MediaQueryListEvent) => setSysDark(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const resolved: "light" | "dark" =
    choice === "system" ? (external ?? (sysDark ? "dark" : "light")) : choice;

  const mounted = useRef(false);
  useEffect(() => {
    const root = document.documentElement;
    // Birinchi yuklanishda emas, faqat almashtirilganda silliq o‘tish
    const animate = mounted.current && root.classList.contains("dark") !== (resolved === "dark");
    mounted.current = true;
    if (animate && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      root.classList.add("theme-transition");
      window.setTimeout(() => root.classList.remove("theme-transition"), 400);
    }
    root.classList.toggle("dark", resolved === "dark");
    root.style.colorScheme = resolved;
  }, [resolved]);

  const setChoice = useCallback((c: ThemeChoice) => {
    setChoiceState(c);
    try {
      localStorage.setItem(KEY, c);
    } catch {
      /* e’tiborsiz */
    }
  }, []);

  return (
    <ThemeContext.Provider value={{ choice, resolved, setChoice, setExternalScheme: setExternal }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used inside ThemeProvider");
  return ctx;
}
