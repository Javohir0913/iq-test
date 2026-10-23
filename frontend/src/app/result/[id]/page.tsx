"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { Check, Clock, CloudOff, Download, Link, Refresh, Send, Share, Spinner } from "@/components/icons";
import { CategoryBar, CountUp, ScoreRing } from "@/components/result";
import { Grid3, Star, Triangle } from "@/components/shapes";
import { Button, ButtonLink, Card, Modal, Skeleton, StateView } from "@/components/ui";
import { useI18n } from "@/i18n";
import { ApiError, api, type AttemptResult } from "@/lib/api";
import { renderShareCard } from "@/lib/shareCard";
import { resolveAttemptToken } from "@/lib/attemptToken";
import { useAuth } from "@/lib/auth";
import { useTelegram } from "@/lib/telegram";
import { useMeta } from "@/lib/useMeta";

type LoadState = "loading" | "ready" | "not_found" | "error";

const TONES: Record<string, string> = {
  numeric: "bg-accent",
  pattern: "bg-ink",
  spatial: "bg-teal",
};

export default function ResultPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { t, lang } = useI18n();
  const { status: authStatus } = useAuth();
  const [load, setLoad] = useState<LoadState>("loading");
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [shareOpen, setShareOpen] = useState(false);
  const { webApp } = useTelegram();

  const fetchResult = useCallback(async () => {
    if (authStatus === "loading") return;
    const tk = await resolveAttemptToken(id, authStatus === "authed");
    setToken(tk);
    if (!tk) {
      setLoad("not_found");
      return;
    }
    setLoad("loading");
    try {
      setResult(await api.result(id, tk));
      setLoad("ready");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) router.replace(`/test/${id}`);
      else if (err instanceof ApiError && (err.status === 404 || err.status === 403)) setLoad("not_found");
      else setLoad("error");
    }
  }, [id, router, authStatus]);

  useEffect(() => {
    fetchResult();
  }, [fetchResult]);

  if (load === "loading") return <ResultSkeleton />;
  if (load === "not_found")
    return (
      <>
        <Header />
        <StateView icon={<Grid3 size={48} filled={[0, 4]} accent={8} />} title={t("result.not_found_title")} text={t("result.not_found_text")}>
          <ButtonLink href="/start">{t("common.start")}</ButtonLink>
        </StateView>
      </>
    );
  if (load === "error" || !result || !token)
    return (
      <>
        <Header />
        <StateView icon={<CloudOff size={40} />} title={t("errors.generic_title")} text={t("errors.generic_text")}>
          <Button onClick={fetchResult}>
            <Refresh size={16} /> {t("common.retry")}
          </Button>
        </StateView>
      </>
    );

  const levelName = result.level ? (lang === "ru" ? result.level.name_ru : result.level.name_uz) : "—";
  const levelDesc = result.level ? (lang === "ru" ? result.level.description_ru : result.level.description_uz) : "";
  const minutes = Math.floor(result.duration_seconds / 60);
  const seconds = result.duration_seconds % 60;

  return (
    <>
      <Header />
      <main id="main" className="relative isolate">
        <div className="dot-grid absolute inset-x-0 top-0 -z-10 h-[520px] [mask-image:linear-gradient(to_bottom,black,transparent)]" />
        <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 md:py-12">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted">{t("result.title")}</p>
            <h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-4xl">{t("result.greeting", { name: result.full_name })}</h1>
            {result.status === "expired" && (
              <p className="mx-auto mt-3 inline-flex items-center gap-2 rounded-full bg-accent/10 px-3 py-1.5 text-sm font-medium text-accent">
                <Clock size={15} /> {t("result.expired_note")}
              </p>
            )}
          </motion.div>

          {/* Asosiy ko‘rsatkich */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="relative mt-8 overflow-hidden rounded-[28px] border border-line bg-surface p-6 shadow-lift sm:p-10"
          >
            <Decor />
            <div className="grid items-center gap-8 md:grid-cols-[auto_1fr] md:gap-12">
              <div className="mx-auto">
                <ScoreRing score={result.total_score} max={result.max_score} size={240}>
                  <div>
                    <CountUp to={result.total_score} className="block text-6xl font-extrabold tracking-tight" />
                    <span className="tabular mt-1 block text-sm font-semibold text-muted">
                      / {result.max_score} · {t("result.score").toLowerCase()}
                    </span>
                  </div>
                </ScoreRing>
              </div>
              <div className="text-center md:text-left">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">{t("result.level")}</p>
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.9, type: "spring", stiffness: 300, damping: 18 }}
                  className="mt-2 inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-2xl font-bold text-white shadow-glow sm:text-3xl"
                >
                  <Star points={5} size={22} />
                  {levelName}
                </motion.div>
                {levelDesc && <p className="mx-auto mt-4 max-w-md text-[15px] leading-relaxed text-muted md:mx-0">{levelDesc}</p>}
                <dl className="mt-6 grid grid-cols-3 gap-3">
                  <Stat label={t("result.percent")} value={<><CountUp to={result.percent} />%</>} />
                  <Stat label={t("result.answered")} value={<span className="tabular">{result.answered_count}/{result.total_questions}</span>} />
                  <Stat label={t("result.time_spent")} value={<span className="tabular">{t("result.duration", { m: minutes, s: seconds })}</span>} small />
                </dl>
              </div>
            </div>
          </motion.div>

          {/* Kategoriyalar */}
          <div className="mt-6 grid gap-6 md:grid-cols-[1.4fr_1fr]">
            <Card className="p-6 sm:p-8">
              <h2 className="text-lg font-bold tracking-tight">{t("result.categories_title")}</h2>
              <p className="mt-1 text-sm text-muted">{t("result.categories_hint")}</p>
              <div className="mt-6 space-y-6">
                {result.categories.map((c, i) => (
                  <CategoryBar
                    key={c.key}
                    name={lang === "ru" ? c.name_ru : c.name_uz}
                    percent={c.percent}
                    score={c.score}
                    max={c.max}
                    delay={0.2 + i * 0.15}
                    tone={TONES[c.key] ?? "bg-teal"}
                  />
                ))}
              </div>
            </Card>
            <Card className="grid place-items-center p-6">
              <Radar
                values={result.categories.map((c) => ({ key: c.key, label: lang === "ru" ? c.name_ru : c.name_uz, value: c.percent }))}
              />
            </Card>
          </div>

          {/* Amallar */}
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-center">
            <Button size="lg" onClick={() => setShareOpen(true)}>
              <Share size={18} /> {t("result.share")}
            </Button>
            <a
              href={api.certificateUrl(id, token, lang)}
              onClick={(e) => {
                // Telegram WebView'da oddiy yuklab olish ishlamaydi – Telegram API orqali
                if (!webApp) return;
                e.preventDefault();
                const url = new URL(api.certificateUrl(id, token, lang), window.location.href).toString();
                if (webApp.isVersionAtLeast?.("8.0") && webApp.downloadFile) {
                  webApp.downloadFile({ url, file_name: `sertifikat-${id.slice(0, 8)}.pdf` });
                } else {
                  webApp.openLink?.(url);
                }
              }}
              className="focus-ring inline-flex h-14 items-center justify-center gap-2.5 rounded-btn bg-ink px-7 font-semibold text-page transition hover:bg-ink/90 active:scale-[0.98]" download>
              <Download size={18} /> {t("result.certificate")}
            </a>
            <ButtonLink href="/start" size="lg" variant="secondary">
              <Refresh size={18} /> {t("result.retake")}
            </ButtonLink>
          </div>

          {result.verify_code && (
            <p className="mt-6 text-center text-sm text-muted">
              {t("result.verify_code")}:{" "}
              <a
                href={`/verify/${result.verify_code.replace(/-/g, "")}`}
                className="tabular font-semibold tracking-wider text-ink underline-offset-4 hover:underline"
              >
                {result.verify_code}
              </a>
            </p>
          )}
          <p className="mx-auto mt-10 max-w-2xl text-center text-sm leading-relaxed text-muted">{t("result.disclaimer")}</p>
        </div>
      </main>

      <ShareModal open={shareOpen} onClose={() => setShareOpen(false)} result={result} levelName={levelName} />
    </>
  );
}

function Stat({ label, value, small = false }: { label: string; value: React.ReactNode; small?: boolean }) {
  return (
    <div className="rounded-card border border-line bg-surface-2 px-2 py-3 text-center sm:px-3 md:text-left">
      <dt className="break-words text-[10px] font-semibold uppercase leading-tight tracking-wide text-muted sm:text-[11px] sm:tracking-wider">{label}</dt>
      <dd className={`mt-1 font-bold tracking-tight ${small ? "text-base sm:text-lg" : "text-xl sm:text-2xl"}`}>{value}</dd>
    </div>
  );
}

function Decor() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-0">
      <Star points={4} inner={0.38} size={40} className="absolute right-8 top-8 text-ink/80" />
      <Triangle size={22} className="absolute right-24 top-20 text-teal/70" />
    </div>
  );
}

// Uch yo‘nalish bo‘yicha uchburchak (radar) diagramma
function Radar({ values }: { values: Array<{ key: string; label: string; value: number }> }) {
  const reduce = useReducedMotion();
  const size = 320;
  const c = size / 2;
  const R = 92;
  const n = values.length || 3;
  const point = (i: number, ratio: number) => {
    const a = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [c + R * ratio * Math.cos(a), c + R * ratio * Math.sin(a)] as const;
  };
  const poly = (ratio: (i: number) => number) =>
    values.map((_, i) => point(i, ratio(i)).map((v) => v.toFixed(1)).join(",")).join(" ");
  const colors: Record<string, string> = { numeric: "rgb(var(--accent))", pattern: "rgb(var(--ink))", spatial: "rgb(var(--teal))" };

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="h-auto w-full max-w-[340px] overflow-visible" role="img" aria-label={values.map((v) => `${v.label}: ${Math.round(v.value)}%`).join(", ")}>
      {[0.25, 0.5, 0.75, 1].map((r) => (
        <polygon key={r} points={poly(() => r)} fill="none" stroke="rgb(var(--ink) / 0.1)" strokeWidth={1} />
      ))}
      {values.map((_, i) => {
        const [x, y] = point(i, 1);
        return <line key={i} x1={c} y1={c} x2={x} y2={y} stroke="rgb(var(--ink) / 0.1)" />;
      })}
      <motion.polygon
        points={poly((i) => values[i].value / 100)}
        fill="rgb(var(--accent) / 0.18)"
        stroke="rgb(var(--accent))"
        strokeWidth={2.5}
        strokeLinejoin="round"
        initial={reduce ? false : { scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        style={{ transformOrigin: `${c}px ${c}px` }}
        transition={{ delay: 0.5, duration: 1, ease: [0.16, 1, 0.3, 1] }}
      />
      {values.map((v, i) => {
        const [x, y] = point(i, v.value / 100);
        const [lx, ly] = point(i, 1.32);
        return (
          <g key={v.key}>
            <motion.circle
              cx={x}
              cy={y}
              r={5}
              fill={colors[v.key] ?? "rgb(var(--teal))"}
              stroke="rgb(var(--surface))"
              strokeWidth={2}
              initial={reduce ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.2 }}
            />
            <text x={lx} y={ly - 6} textAnchor="middle" className="fill-ink text-[11px] font-semibold">
              {v.label.length > 18 ? v.label.slice(0, 17) + "…" : v.label}
            </text>
            <text x={lx} y={ly + 9} textAnchor="middle" className="tabular fill-muted text-[11px] font-bold">
              {Math.round(v.value)}%
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function ShareModal({ open, onClose, result, levelName }: { open: boolean; onClose: () => void; result: AttemptResult; levelName: string }) {
  const { t, lang } = useI18n();
  const { webApp } = useTelegram();
  const [blob, setBlob] = useState<Blob | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const meta = useMeta();
  // Bot bo‘lsa – ulashishda bot havolasi (Mini App doim ochiladi), aks holda sayt manzili
  const siteUrl = meta.telegram_bot
    ? `https://t.me/${meta.telegram_bot}`
    : typeof window !== "undefined"
      ? window.location.origin
      : "";
  const shareText = t("result.share_text", { score: result.total_score, max: result.max_score, level: levelName });

  useEffect(() => {
    if (!open || blob) return;
    let cancelled = false;
    renderShareCard(result, {
      brand: t("result.card.brand"),
      headline: t("result.card.headline"),
      score: t("result.card.score"),
      level: levelName,
      cta: t("result.card.cta"),
      url: siteUrl,
      categories: result.categories.map((c) => ({ name: lang === "ru" ? c.name_ru : c.name_uz, percent: c.percent })),
    })
      .then((b) => {
        if (cancelled) return;
        setBlob(b);
        setUrl(URL.createObjectURL(b));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [open, blob, result, levelName, lang, siteUrl, t]);

  // Til almashsa kartochka qayta chiziladi
  useEffect(() => {
    setBlob(null);
    setUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
  }, [lang]);

  const file = blob ? new File([blob], "natija.png", { type: "image/png" }) : null;
  const canNativeShare = typeof navigator !== "undefined" && !!file && !!navigator.canShare?.({ files: [file] });
  const telegramLink = `https://t.me/share/url?url=${encodeURIComponent(siteUrl)}&text=${encodeURIComponent(shareText)}`;

  const nativeShare = async () => {
    if (!file) return;
    try {
      await navigator.share({ files: [file], text: `${shareText} ${siteUrl}` });
    } catch {
      /* foydalanuvchi bekor qildi */
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(`${shareText} ${siteUrl}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* e’tiborsiz */
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={t("result.share_title")} closeLabel={t("common.close")}>
      <div className="overflow-hidden rounded-card border border-line bg-panel">
        {url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={url} alt={t("result.share_title")} className="aspect-square w-full" />
        ) : (
          <div className="grid aspect-square place-items-center text-sm text-muted">
            <span className="inline-flex items-center gap-2">
              <Spinner /> {t("result.share_generating")}
            </span>
          </div>
        )}
      </div>
      <div className="mt-5 grid grid-cols-2 gap-2">
        {canNativeShare && (
          <Button className="col-span-2" onClick={nativeShare}>
            <Share size={17} /> {t("result.share_native")}
          </Button>
        )}
        <a
          href={telegramLink}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => {
            if (webApp?.openTelegramLink) {
              e.preventDefault();
              webApp.openTelegramLink(telegramLink);
            }
          }}
          className="focus-ring col-span-2 inline-flex h-11 items-center justify-center gap-2 rounded-btn bg-[#229ED9] px-5 text-[15px] font-semibold text-white transition hover:brightness-105"
        >
          <Send size={17} /> {t("result.share_telegram")}
        </a>
        {!webApp && (
        <a
          href={url ?? undefined}
          download="natija.png"
          aria-disabled={!url}
          className={`focus-ring inline-flex h-11 items-center justify-center gap-2 whitespace-nowrap rounded-btn border border-line bg-surface px-3 text-sm font-semibold transition hover:bg-surface-2 ${url ? "" : "pointer-events-none opacity-50"}`}
        >
          <Download size={16} /> {t("result.share_download")}
        </a>
        )}
        <Button variant="secondary" onClick={copy} className={`whitespace-nowrap !px-3 !text-sm ${webApp ? "col-span-2" : ""}`}>
          {copied ? <Check size={16} /> : <Link size={16} />} {copied ? t("result.share_copied") : t("result.share_copy")}
        </Button>
      </div>
    </Modal>
  );
}

function ResultSkeleton() {
  const { t } = useI18n();
  return (
    <>
      <Header />
      <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6" aria-busy="true" aria-label={t("common.loading")}>
        <Skeleton className="mx-auto h-4 w-32" />
        <Skeleton className="mx-auto mt-3 h-9 w-2/3" />
        <Skeleton className="mt-8 h-80 !rounded-[28px]" />
        <div className="mt-6 grid gap-6 md:grid-cols-[1.4fr_1fr]">
          <Skeleton className="h-64 !rounded-card" />
          <Skeleton className="h-64 !rounded-card" />
        </div>
      </div>
    </>
  );
}

