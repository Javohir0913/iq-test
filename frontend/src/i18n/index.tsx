"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { translate, translateList, LANG_COOKIE, type Lang, type Vars } from "./core";

export { LANGS, LANG_COOKIE, LOCALES, localized, translate, translateList, type Lang } from "./core";

interface I18nValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string, vars?: Vars) => string;
  list: <T = string>(key: string) => T[];
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ initialLang, children }: { initialLang: Lang; children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang);
  const router = useRouter();

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try {
      document.cookie = `${LANG_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
      localStorage.setItem(LANG_COOKIE, next);
    } catch {
      /* saqlab bo‘lmasa ham til almashadi */
    }
    // Server komponentlar (bosh sahifa) yangi til bilan qayta chiziladi
    router.refresh();
  }, [router]);

  // Bot havolasidagi ?lang=uz|ru tanlovni belgilaydi
  useEffect(() => {
    try {
      const param = new URLSearchParams(window.location.search).get("lang");
      if ((param === "uz" || param === "ru" || param === "en") && param !== initialLang) setLang(param);
    } catch {
      /* e’tiborsiz */
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.title = translate(lang, "meta.title");
  }, [lang]);

  const value = useMemo<I18nValue>(
    () => ({
      lang,
      setLang,
      t: (key, vars) => translate(lang, key, vars),
      list: (key) => translateList(lang, key),
    }),
    [lang, setLang],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside I18nProvider");
  return ctx;
}
