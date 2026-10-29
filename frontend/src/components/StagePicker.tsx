"use client";

// Bosqich tanlash: bosqich kartochkalari, majburiy kanallar va do‘st taklif qilish
import { useState } from "react";
import { useI18n } from "@/i18n";
import type { Progress, StageProgress } from "@/lib/api";
import { useTelegram } from "@/lib/telegram";
import { Check, Link, Lock, Refresh, Send, Spinner } from "./icons";
import { Button } from "./ui";

export function StageCards({
  stages,
  selected,
  onSelect,
}: {
  stages: StageProgress[];
  selected: number | null;
  onSelect: (n: number) => void;
}) {
  const { t } = useI18n();
  return (
    <div role="radiogroup" aria-label={t("stages.title")} className="grid gap-3 sm:grid-cols-3">
      {stages.map((s) => {
        const active = s.number === selected;
        return (
          <button
            key={s.number}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onSelect(s.number)}
            className={`focus-ring relative flex flex-col items-start rounded-card border p-4 text-left transition-[border,box-shadow,background] duration-200 ${
              active
                ? "border-accent bg-accent/[0.06] shadow-[0_0_0_3px_rgb(var(--accent)/0.15)]"
                : "border-line bg-surface hover:border-ink/30"
            }`}
          >
            <span className="flex w-full items-center justify-between gap-2">
              <span className="text-sm font-bold tracking-tight">{t("stages.stage", { n: s.number })}</span>
              {s.unlocked ? (
                active ? (
                  <span className="grid h-5 w-5 place-items-center rounded-full bg-accent text-white">
                    <Check size={12} strokeWidth={3} />
                  </span>
                ) : null
              ) : (
                <Lock size={15} className="text-muted" aria-label={t("stages.locked")} />
              )}
            </span>
            <span className="tabular mt-2 text-2xl font-extrabold tracking-tight">{s.question_count}</span>
            <span className="text-xs text-muted">
              {t("stages.questions", { count: s.question_count })} · {t("stages.minutes", { minutes: s.duration_minutes })}
            </span>
            <span
              className={`mt-3 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                s.certificate ? "bg-teal/15 text-teal" : "bg-ink/[0.06] text-muted"
              }`}
            >
              {s.certificate ? t("stages.certificate") : t("stages.no_certificate")}
            </span>
            {s.best_percent !== null && s.finished_count > 0 && (
              <span className="mt-2 text-xs text-muted">{t("stages.best", { percent: Math.round(s.best_percent) })}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export function ChannelsCard({ progress, onCheck }: { progress: Progress; onCheck: () => Promise<void> }) {
  const { t } = useI18n();
  const { webApp } = useTelegram();
  const [checking, setChecking] = useState(false);
  const [failed, setFailed] = useState(false);

  const check = async () => {
    setChecking(true);
    setFailed(false);
    try {
      await onCheck();
    } finally {
      setChecking(false);
      setFailed(true);
    }
  };

  return (
    <div className="rounded-card border border-accent/30 bg-accent/[0.06] p-4 sm:p-5">
      <p className="font-semibold">{t("stages.channels_title")}</p>
      <p className="mt-1 text-sm text-muted">{t("stages.channels_text")}</p>
      <ul className="mt-4 space-y-2">
        {progress.channels.map((ch) => (
          <li key={ch.title + ch.url} className="flex items-center justify-between gap-3 rounded-btn border border-line bg-surface px-3 py-2.5">
            <span className="min-w-0 truncate text-sm font-semibold">{ch.title}</span>
            {ch.subscribed ? (
              <span className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-teal">
                <Check size={14} strokeWidth={3} /> {t("stages.subscribed")}
              </span>
            ) : ch.url ? (
              <a
                href={ch.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => {
                  if (webApp?.openTelegramLink && ch.url.startsWith("https://t.me/")) {
                    e.preventDefault();
                    webApp.openTelegramLink(ch.url);
                  }
                }}
                className="focus-ring inline-flex h-9 shrink-0 items-center gap-1.5 rounded-btn bg-[#229ED9] px-3.5 text-sm font-semibold text-white hover:brightness-105"
              >
                <Send size={14} /> {t("stages.subscribe")}
              </a>
            ) : null}
          </li>
        ))}
      </ul>
      {failed && !checking && !progress.subscribed && (
        <p role="alert" className="mt-3 text-sm font-medium text-accent">
          {t("stages.not_subscribed")}
        </p>
      )}
      <Button type="button" variant="dark" size="sm" className="mt-4 w-full" onClick={check} disabled={checking}>
        {checking ? <Spinner size={15} /> : <Refresh size={15} />} {checking ? t("stages.checking") : t("stages.check")}
      </Button>
    </div>
  );
}

export function FriendsCard({ progress, missing }: { progress: Progress; missing: number }) {
  const { t } = useI18n();
  const { webApp } = useTelegram();
  const [copied, setCopied] = useState(false);
  const link = progress.referral_link;
  const text = t("stages.invite_text");
  const share = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* e’tiborsiz */
    }
  };

  return (
    <div className="rounded-card border border-teal/30 bg-teal/[0.07] p-4 sm:p-5">
      <p className="font-semibold">{t("stages.friends_title")}</p>
      <p className="mt-1 text-sm text-muted">{t("stages.friends_text")}</p>
      <p className="mt-3 text-sm font-semibold text-teal">{t("stages.need_friends", { n: missing })}</p>
      <p className="tabular mt-1 text-sm text-muted">
        {t("stages.friends_count", { n: progress.friends })}
        {progress.pending_friends > 0 && ` · ${t("stages.friends_pending", { n: progress.pending_friends })}`}
      </p>
      {link && (
        <>
          <div className="mt-4 truncate rounded-btn border border-line bg-surface px-3 py-2.5 font-mono text-xs">{link}</div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <a
              href={share}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => {
                if (webApp?.openTelegramLink) {
                  e.preventDefault();
                  webApp.openTelegramLink(share);
                }
              }}
              className="focus-ring inline-flex h-9 items-center justify-center gap-1.5 rounded-btn bg-[#229ED9] px-3 text-sm font-semibold text-white hover:brightness-105"
            >
              <Send size={14} /> {t("stages.invite_share")}
            </a>
            <Button type="button" variant="secondary" size="sm" onClick={copy}>
              {copied ? <Check size={14} /> : <Link size={14} />} {copied ? t("stages.copied") : t("stages.invite_copy")}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
