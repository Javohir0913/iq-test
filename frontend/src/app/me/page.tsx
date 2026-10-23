"use client";

import NextLink from "next/link";
import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { ArrowRight, CloudOff, Refresh } from "@/components/icons";
import { Grid3 } from "@/components/shapes";
import { LoginCard } from "@/components/TelegramLogin";
import { Button, ButtonLink, Skeleton, StateView } from "@/components/ui";
import { useI18n } from "@/i18n";
import { authApi, type MyAttempt } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { storage } from "@/lib/storage";
import { useTelegram } from "@/lib/telegram";

type Load = "loading" | "ready" | "error";

export default function MyResultsPage() {
  const { t, lang } = useI18n();
  const { status, user, logout } = useAuth();
  const { initData } = useTelegram();
  const [load, setLoad] = useState<Load>("loading");
  const [data, setData] = useState<{ max_score: number; attempts: MyAttempt[] } | null>(null);

  const fetchData = () => {
    setLoad("loading");
    authApi
      .myAttempts()
      .then((d) => {
        d.attempts.forEach((a) => storage.remember(a.attempt_id, a.token));
        setData(d);
        setLoad("ready");
      })
      .catch(() => setLoad("error"));
  };

  useEffect(() => {
    if (status === "authed") fetchData();
  }, [status]);

  const dateFmt = new Intl.DateTimeFormat(lang === "ru" ? "ru-RU" : "uz-UZ", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  let body: React.ReactNode;
  if (status === "loading" || (status === "guest" && initData)) {
    body = <Skeleton className="h-64 !rounded-panel" />;
  } else if (status === "guest") {
    body = <LoginCard />;
  } else if (load === "loading") {
    body = (
      <div className="space-y-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-20 !rounded-card" />
        ))}
      </div>
    );
  } else if (load === "error" || !data) {
    body = (
      <StateView icon={<CloudOff size={40} />} title={t("errors.generic_title")} text={t("errors.generic_text")}>
        <Button onClick={fetchData}>
          <Refresh size={16} /> {t("common.retry")}
        </Button>
      </StateView>
    );
  } else if (data.attempts.length === 0) {
    body = (
      <StateView icon={<Grid3 size={48} filled={[0, 4]} accent={8} />} title={t("me.empty_title")} text={t("me.empty_text")}>
        <ButtonLink href="/start">{t("common.start")}</ButtonLink>
      </StateView>
    );
  } else {
    body = (
      <ul className="space-y-3">
        {data.attempts.map((a, i) => {
          const inProgress = a.status === "in_progress";
          const href = inProgress ? `/test/${a.attempt_id}` : `/result/${a.attempt_id}`;
          const level = a.level ? (lang === "ru" ? a.level.name_ru : a.level.name_uz) : "";
          return (
            <li key={a.attempt_id} className="anim-fade-up" style={{ ["--delay" as string]: `${i * 0.04}s` }}>
              <NextLink
                href={href}
                className="focus-ring group flex items-center gap-4 rounded-card border border-line bg-surface p-4 shadow-soft transition-shadow hover:shadow-lift sm:p-5"
              >
                <span
                  className={`tabular grid h-14 w-14 shrink-0 place-items-center rounded-card text-lg font-bold ${
                    inProgress ? "bg-teal/10 text-teal" : "bg-accent-strong text-white"
                  }`}
                >
                  {inProgress ? "…" : a.total_score}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-semibold">
                    {inProgress
                      ? t("me.in_progress")
                      : `${t("me.score", { score: a.total_score ?? 0, max: data.max_score })} · ${Math.round(a.percent ?? 0)}%`}
                    {level && <span className="ml-2 rounded-full bg-panel px-2 py-0.5 text-xs font-semibold text-ink">{level}</span>}
                    {a.status === "expired" && <span className="ml-2 text-xs font-medium text-muted">{t("me.expired")}</span>}
                  </span>
                  <span className="tabular mt-0.5 block text-sm text-muted">{dateFmt.format(new Date(a.finished_at ?? a.started_at))}</span>
                </span>
                <span className="hidden items-center gap-1 text-sm font-semibold text-ink sm:inline-flex">
                  {inProgress ? t("me.continue") : t("me.open")}
                </span>
                <ArrowRight size={18} className="shrink-0 text-muted transition-transform group-hover:translate-x-1" />
              </NextLink>
            </li>
          );
        })}
      </ul>
    );
  }

  return (
    <>
      <Header />
      <main id="main" className="mx-auto max-w-3xl px-4 py-8 sm:px-6 md:py-12">
        {status === "authed" && (
          <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{t("me.title")}</h1>
              <p className="mt-1 text-muted">{t("me.subtitle")}</p>
            </div>
            <div className="flex items-center gap-2">
              <ButtonLink href="/start" size="sm">
                {t("common.start")}
              </ButtonLink>
              {!initData && (
                <Button variant="secondary" size="sm" onClick={logout} title={user?.full_name}>
                  {t("auth.logout")}
                </Button>
              )}
            </div>
          </div>
        )}
        {body}
      </main>
    </>
  );
}
