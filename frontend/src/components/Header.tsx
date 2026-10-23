"use client";

import NextLink from "next/link";
import { LANGS, useI18n } from "@/i18n";
import { useAuth } from "@/lib/auth";
import { useTheme, type ThemeChoice } from "@/lib/theme";
import { Monitor, Moon, Sun } from "./icons";

export function Logo({ compact = false }: { compact?: boolean }) {
  const { t } = useI18n();
  return (
    <NextLink href="/" className="focus-ring group flex items-center gap-2.5 rounded-btn" aria-label={compact ? t("common.home") : undefined}>
      <span aria-hidden className="relative grid h-9 w-9 place-items-center overflow-hidden rounded-[10px] bg-ink text-page shadow-soft transition-transform duration-300 group-hover:rotate-[-6deg]">
        <svg viewBox="0 0 36 36" width="36" height="36" aria-hidden>
          <path d="M12 7l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" fill="currentColor" />
          <rect x="19" y="19" width="11" height="11" rx="3" fill="rgb(var(--accent))" />
        </svg>
      </span>
      {!compact && <span className="hidden whitespace-nowrap text-[15px] font-bold tracking-tight min-[420px]:inline">{t("common.brand")}</span>}
    </NextLink>
  );
}

export function LangSwitch() {
  const { lang, setLang, t } = useI18n();
  const idx = LANGS.indexOf(lang);
  return (
    <div role="group" aria-label={t("common.language")} className="relative flex rounded-full border border-line bg-surface p-0.5 text-xs font-semibold">
      <span
        aria-hidden
        className="absolute bottom-0.5 left-0.5 top-0.5 w-10 rounded-full bg-ink transition-transform duration-300 ease-[cubic-bezier(0.34,1.4,0.64,1)]"
        style={{ transform: `translateX(${idx * 100}%)` }}
      />
      {LANGS.map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          className={`focus-ring relative z-10 h-8 w-10 rounded-full uppercase transition-colors duration-300 ${lang === l ? "text-page" : "text-muted hover:text-ink"}`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

const ORDER: ThemeChoice[] = ["light", "dark", "system"];

export function ThemeToggle() {
  const { choice, setChoice } = useTheme();
  const { t } = useI18n();
  const next = ORDER[(ORDER.indexOf(choice) + 1) % ORDER.length];
  const Icon = choice === "light" ? Sun : choice === "dark" ? Moon : Monitor;
  return (
    <button
      onClick={() => setChoice(next)}
      className="focus-ring grid h-9 w-9 place-items-center rounded-full border border-line bg-surface text-ink transition-colors hover:bg-surface-2"
      aria-label={`${t("common.theme.label")}: ${t(`common.theme.${choice}`)}`}
      title={t(`common.theme.${choice}`)}
    >
      <span key={choice} className="anim-pop" style={{ ["--delay" as string]: "0s" }}>
        <Icon size={17} />
      </span>
    </button>
  );
}

export function UserButton() {
  const { status, user } = useAuth();
  const { t } = useI18n();
  if (status === "loading") return <span className="h-9 w-9 rounded-full bg-ink/[0.06]" aria-hidden />;
  if (status !== "authed" || !user)
    return (
      <NextLink
        href="/start"
        className="focus-ring inline-flex h-9 items-center rounded-full border border-line bg-surface px-3.5 text-sm font-semibold transition-colors hover:bg-surface-2"
      >
        {t("auth.login")}
      </NextLink>
    );
  const initials = (user.first_name || user.username || "?").slice(0, 1).toUpperCase();
  return (
    <NextLink
      href="/me"
      className="focus-ring grid h-9 w-9 place-items-center overflow-hidden rounded-full bg-teal text-sm font-bold text-white ring-2 ring-surface"
      aria-label={t("auth.my_results")}
      title={t("auth.signed_in_as", { name: user.full_name || user.username })}
    >
      {user.photo_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={user.photo_url} alt="" className="h-full w-full object-cover" referrerPolicy="no-referrer" />
      ) : (
        initials
      )}
    </NextLink>
  );
}

export function Header({ children }: { children?: React.ReactNode }) {
  const { t } = useI18n();
  return (
    <header className="sticky top-0 z-40 border-b border-transparent bg-page/75 backdrop-blur-xl supports-[backdrop-filter]:bg-page/65">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:rounded-btn focus:bg-surface focus:px-3 focus:py-2">
        {t("common.skip")}
      </a>
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
        <Logo />
        <div className="flex items-center gap-2">
          {children}
          <LangSwitch />
          <ThemeToggle />
          <UserButton />
        </div>
      </div>
    </header>
  );
}
