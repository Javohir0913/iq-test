"use client";

import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/i18n";
import { useAuth } from "@/lib/auth";
import { useMeta } from "@/lib/useMeta";
import { Send, Spinner } from "./icons";
import { Star } from "./shapes";

declare global {
  interface Window {
    onTelegramAuth?: (user: Record<string, unknown>) => void;
  }
}

// Rasmiy Telegram Login Widget (bot domeni @BotFather → /setdomain da sozlanishi kerak)
function Widget({ bot, onAuth }: { bot: string; onAuth: (user: Record<string, unknown>) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const handler = useRef(onAuth);
  handler.current = onAuth;
  const { lang } = useI18n();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    window.onTelegramAuth = (user) => handler.current(user);
    el.innerHTML = "";
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", bot);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-radius", "12");
    script.setAttribute("data-userpic", "false");
    script.setAttribute("data-lang", lang);
    script.setAttribute("data-request-access", "write");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    el.appendChild(script);
    return () => {
      delete window.onTelegramAuth;
    };
  }, [bot, lang]);

  return <div ref={ref} className="flex min-h-[48px] justify-center" />;
}

export function LoginCard() {
  const { t } = useI18n();
  const { loginWithWidget } = useAuth();
  const meta = useMeta();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const bot = meta.telegram_bot;

  const onAuth = async (user: Record<string, unknown>) => {
    setBusy(true);
    setError("");
    try {
      await loginWithWidget(user);
    } catch {
      setError(t("auth.error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative overflow-hidden rounded-panel border border-line bg-surface p-6 text-center shadow-soft sm:p-10">
      <div aria-hidden className="absolute -right-6 -top-6 text-ink/[0.06]">
        <Star points={4} inner={0.4} size={120} />
      </div>
      <div className="relative">
        <span className="mx-auto grid h-16 w-16 place-items-center rounded-panel bg-[#229ED9] text-white shadow-soft">
          <Send size={30} />
        </span>
        <h1 className="mt-5 text-2xl font-bold tracking-tight sm:text-3xl">{t("auth.title")}</h1>
        <p className="mx-auto mt-2 max-w-md text-muted">{t("auth.text")}</p>
        <div className="mt-7">
          {busy ? (
            <p className="inline-flex items-center gap-2 text-sm font-medium text-muted">
              <Spinner /> {t("auth.loading")}
            </p>
          ) : bot ? (
            <>
              <Widget bot={bot} onAuth={onAuth} />
              <p className="mt-3 text-xs text-muted">{t("auth.widget_hint")}</p>
            </>
          ) : (
            <p className="text-sm text-muted">{t("auth.unavailable")}</p>
          )}
          {error && (
            <p role="alert" className="mt-3 text-sm font-medium text-accent">
              {error}
            </p>
          )}
        </div>
        {bot && (
          <p className="mt-6 text-sm text-muted">
            {t("auth.or_bot")}:{" "}
            <a className="font-semibold text-teal underline-offset-4 hover:underline" href={`https://t.me/${bot}`} target="_blank" rel="noopener noreferrer">
              @{bot}
            </a>
          </p>
        )}
      </div>
    </div>
  );
}
