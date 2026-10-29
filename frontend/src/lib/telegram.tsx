"use client";

import Script from "next/script";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { LANG_COOKIE, useI18n } from "@/i18n";
import { useTheme } from "./theme";

interface TelegramWebApp {
  initData: string;
  initDataUnsafe: { user?: { id: number; first_name?: string; last_name?: string; language_code?: string } };
  colorScheme: "light" | "dark";
  themeParams: Record<string, string>;
  ready: () => void;
  expand: () => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  onEvent: (event: string, cb: () => void) => void;
  offEvent: (event: string, cb: () => void) => void;
  openTelegramLink?: (url: string) => void;
  disableVerticalSwipes?: () => void;
  enableClosingConfirmation?: () => void;
  disableClosingConfirmation?: () => void;
  isVersionAtLeast?: (v: string) => boolean;
  downloadFile?: (params: { url: string; file_name: string }, cb?: (accepted: boolean) => void) => void;
  openLink?: (url: string) => void;
  BackButton: { show: () => void; hide: () => void; onClick: (cb: () => void) => void; offClick: (cb: () => void) => void };
  HapticFeedback?: { selectionChanged: () => void; notificationOccurred: (t: "success" | "error" | "warning") => void };
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

interface TelegramValue {
  webApp: TelegramWebApp | null;
  initData: string;
  haptic: (kind?: "select" | "success") => void;
  /** Test davomida Mini App tasodifan yopilmasligi uchun tasdiq so‘rash */
  setClosingConfirmation: (on: boolean) => void;
}

const TelegramContext = createContext<TelegramValue>({
  webApp: null,
  initData: "",
  haptic: () => {},
  setClosingConfirmation: () => {},
});

export function TelegramProvider({ children }: { children: React.ReactNode }) {
  const [webApp, setWebApp] = useState<TelegramWebApp | null>(null);
  const { setExternalScheme, resolved } = useTheme();
  const { setLang } = useI18n();
  const router = useRouter();
  const pathname = usePathname();
  const backRef = useRef<() => void>(() => {});
  const [inTelegram, setInTelegram] = useState(false);

  // Skript faqat Telegram ichida yuklanadi (oddiy brauzerda ortiqcha so‘rov bo‘lmasin)
  useEffect(() => {
    try {
      const w = window as unknown as { TelegramWebviewProxy?: unknown };
      const flagged =
        window.location.hash.includes("tgWebApp") ||
        window.location.search.includes("tgWebApp") ||
        Boolean(w.TelegramWebviewProxy) ||
        sessionStorage.getItem("iq.tg") === "1";
      if (flagged) {
        sessionStorage.setItem("iq.tg", "1");
        setInTelegram(true);
      }
    } catch {
      /* e’tiborsiz */
    }
  }, []);

  const init = useCallback(() => {
    const wa = window.Telegram?.WebApp;
    if (!wa || !wa.initData) return; // oddiy brauzer
    wa.ready();
    wa.expand();
    try {
      // Test ichida pastga surganda Mini App yopilib ketmasin (Bot API 7.7+)
      if (wa.isVersionAtLeast?.("7.7")) wa.disableVerticalSwipes?.();
    } catch {
      /* eski versiya */
    }
    // Til hali tanlanmagan bo‘lsa – Telegram tiliga moslash
    const hasLangCookie = document.cookie.split("; ").some((c) => c.startsWith(`${LANG_COOKIE}=`));
    const hasLangParam = new URLSearchParams(window.location.search).has("lang");
    const code = (wa.initDataUnsafe.user?.language_code || "").slice(0, 2);
    if (!hasLangCookie && !hasLangParam) {
      if (["ru", "be", "uk", "kk"].includes(code)) setLang("ru");
      else if (code && code !== "uz") setLang("en");
    }
    setWebApp(wa);
    const applyTheme = () => setExternalScheme(wa.colorScheme === "dark" ? "dark" : "light");
    applyTheme();
    wa.onEvent("themeChanged", applyTheme);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setExternalScheme]);

  useEffect(() => {
    if (window.Telegram?.WebApp) init();
  }, [init]);

  // Telegram sarlavha/fon ranglarini sayt mavzusiga moslash
  useEffect(() => {
    if (!webApp) return;
    const color = resolved === "dark" ? "#0C121D" : "#FBFAF7";
    try {
      webApp.setHeaderColor?.(color);
      webApp.setBackgroundColor?.(color);
    } catch {
      /* eski Telegram versiyalari */
    }
  }, [webApp, resolved]);

  // BackButton: bosh sahifadan boshqa joyda ko‘rsatiladi
  useEffect(() => {
    if (!webApp) return;
    const handler = () => {
      if (pathname.startsWith("/test/") || pathname.startsWith("/result/")) router.push("/");
      else router.back();
    };
    webApp.BackButton.offClick(backRef.current);
    backRef.current = handler;
    if (pathname === "/") webApp.BackButton.hide();
    else {
      webApp.BackButton.show();
      webApp.BackButton.onClick(handler);
    }
  }, [webApp, pathname, router]);

  const haptic = useCallback(
    (kind: "select" | "success" = "select") => {
      try {
        if (kind === "select") webApp?.HapticFeedback?.selectionChanged();
        else webApp?.HapticFeedback?.notificationOccurred("success");
      } catch {
        /* e’tiborsiz */
      }
    },
    [webApp],
  );

  const setClosingConfirmation = useCallback(
    (on: boolean) => {
      try {
        if (on) webApp?.enableClosingConfirmation?.();
        else webApp?.disableClosingConfirmation?.();
      } catch {
        /* e’tiborsiz */
      }
    },
    [webApp],
  );

  return (
    <TelegramContext.Provider value={{ webApp, initData: webApp?.initData ?? "", haptic, setClosingConfirmation }}>
      {inTelegram && <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" onLoad={init} />}
      {children}
    </TelegramContext.Provider>
  );
}

export function useTelegram() {
  return useContext(TelegramContext);
}
