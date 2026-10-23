"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { LangSwitch, Logo, ThemeToggle } from "@/components/Header";
import { ArrowLeft, ArrowRight, Check, Clock, Cloud, CloudOff, Flag, Grid, Keyboard, Refresh, Spinner } from "@/components/icons";
import { OptionCard, QuestionMap, Timer } from "@/components/quiz";
import { Grid3 } from "@/components/shapes";
import { Button, ButtonLink, Modal, ProgressBar, Skeleton, StateView } from "@/components/ui";
import { useI18n } from "@/i18n";
import { ApiError, api, type AttemptQuestions } from "@/lib/api";
import { resolveAttemptToken } from "@/lib/attemptToken";
import { useAuth } from "@/lib/auth";
import { storage } from "@/lib/storage";
import { useTelegram } from "@/lib/telegram";

type LoadState = "loading" | "ready" | "not_found" | "error";
type SaveState = "idle" | "saving" | "saved" | "offline";

const LETTERS = ["A", "B", "C", "D", "E", "F"];

export default function TestPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { t, lang } = useI18n();
  const { haptic, setClosingConfirmation } = useTelegram();
  const reduce = useReducedMotion();
  const { status: authStatus } = useAuth();

  const [load, setLoad] = useState<LoadState>("loading");
  const [data, setData] = useState<AttemptQuestions | null>(null);
  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [offset, setOffset] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [finishOpen, setFinishOpen] = useState(false);
  const [mapOpen, setMapOpen] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [timeUp, setTimeUp] = useState(false);

  const tokenRef = useRef<string | null>(null);
  const pendingRef = useRef<Record<string, string | null>>({});
  const flushingRef = useRef(false);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryDelay = useRef(2000);
  const finishingRef = useRef(false);

  const questions = useMemo(() => data?.questions ?? [], [data]);
  const total = questions.length;
  const question = questions[index];
  const numbers = useMemo(() => questions.map((q) => q.number), [questions]);
  const answeredCount = numbers.filter((n) => answers[n]).length;
  const unanswered = numbers.map((n, i) => ({ n, i })).filter(({ n }) => !answers[n]);

  const goResult = useCallback(() => {
    storage.clearCurrent(id);
    router.replace(`/result/${id}`);
  }, [id, router]);

  // --- Yuklash ---------------------------------------------------------------
  const fetchData = useCallback(async () => {
    if (authStatus === "loading") return;
    const token = await resolveAttemptToken(id, authStatus === "authed", true);
    tokenRef.current = token;
    if (!token) {
      setLoad("not_found");
      return;
    }
    setLoad("loading");
    try {
      const d = await api.questions(id, token);
      if (d.status !== "in_progress") {
        goResult();
        return;
      }
      setOffset(new Date(d.server_time).getTime() - Date.now());
      // Serverdagi javoblar + hali yuborilmagan (oflayn) javoblar
      const pending = storage.pending(id);
      pendingRef.current = pending;
      setAnswers({ ...d.answers, ...pending });
      const pos = Math.min(storage.position(id), Math.max(d.questions.length - 1, 0));
      setIndex(pos);
      setData(d);
      setLoad("ready");
    } catch (err) {
      if (err instanceof ApiError && (err.status === 404 || err.status === 403)) setLoad("not_found");
      else setLoad("error");
    }
  }, [id, goResult, authStatus]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Telegram ichida test davomida yopishdan oldin tasdiq so‘raladi
  useEffect(() => {
    if (load !== "ready") return;
    setClosingConfirmation(true);
    return () => setClosingConfirmation(false);
  }, [load, setClosingConfirmation]);

  // --- Autosave navbati ------------------------------------------------------
  const flush = useCallback(async () => {
    const token = tokenRef.current;
    if (!token || flushingRef.current) return;
    flushingRef.current = true;
    if (retryRef.current) clearTimeout(retryRef.current);
    try {
      while (Object.keys(pendingRef.current).length) {
        const [num, letter] = Object.entries(pendingRef.current)[0];
        setSaveState("saving");
        try {
          await api.answer(id, token, Number(num), letter);
          if (pendingRef.current[num] === letter) delete pendingRef.current[num];
          storage.setPending(id, pendingRef.current);
          retryDelay.current = 2000;
        } catch (err) {
          if (err instanceof ApiError && err.status === 409) {
            pendingRef.current = {};
            storage.setPending(id, {});
            goResult();
            return;
          }
          if (err instanceof ApiError && err.status >= 400 && err.status < 500 && err.status !== 429) {
            delete pendingRef.current[num];
            storage.setPending(id, pendingRef.current);
            continue;
          }
          setSaveState("offline");
          retryRef.current = setTimeout(() => flush(), retryDelay.current);
          retryDelay.current = Math.min(retryDelay.current * 1.6, 15000);
          return;
        }
      }
      setSaveState("saved");
    } finally {
      flushingRef.current = false;
    }
  }, [id, goResult]);

  useEffect(() => {
    if (load !== "ready") return;
    if (Object.keys(pendingRef.current).length) flush();
    const onOnline = () => flush();
    window.addEventListener("online", onOnline);
    return () => {
      window.removeEventListener("online", onOnline);
      if (retryRef.current) clearTimeout(retryRef.current);
    };
  }, [load, flush]);

  const select = useCallback(
    (letter: string) => {
      if (!question || finishingRef.current) return;
      const num = String(question.number);
      setAnswers((prev) => ({ ...prev, [num]: letter }));
      pendingRef.current = { ...pendingRef.current, [num]: letter };
      storage.setPending(id, pendingRef.current);
      haptic("select");
      flush();
    },
    [question, id, flush, haptic],
  );

  // --- Navigatsiya -----------------------------------------------------------
  const go = useCallback(
    (next: number) => {
      if (next < 0 || next >= total) return;
      setDirection(next > index ? 1 : -1);
      setIndex(next);
      storage.setPosition(id, next);
    },
    [index, total, id],
  );

  // Keyingi savol rasmlarini oldindan yuklash
  useEffect(() => {
    [questions[index + 1], questions[index - 1]].forEach((q) => {
      if (!q) return;
      [q.figure, ...q.options.map((o) => o.image)].forEach((src) => {
        if (src) {
          const img = new Image();
          img.src = src;
        }
      });
    });
  }, [index, questions]);

  // --- Taymer ----------------------------------------------------------------
  useEffect(() => {
    if (load !== "ready") return;
    const timer = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(timer);
  }, [load]);

  const remaining = data ? (new Date(data.expires_at).getTime() - (now + offset)) / 1000 : 0;

  const finish = useCallback(async () => {
    const token = tokenRef.current;
    if (!token || finishingRef.current) return;
    finishingRef.current = true;
    setFinishing(true);
    // Avval saqlanmagan javoblarni yuborishga urinish
    for (let i = 0; i < 3 && Object.keys(pendingRef.current).length; i++) {
      flushingRef.current = false;
      await flush();
    }
    for (let attempt = 0; attempt < 5; attempt++) {
      try {
        await api.finish(id, token);
        haptic("success");
        goResult();
        return;
      } catch (err) {
        if (err instanceof ApiError && !err.isNetwork && err.status < 500) {
          goResult();
          return;
        }
        await new Promise((r) => setTimeout(r, 1500 * (attempt + 1)));
      }
    }
    finishingRef.current = false;
    setFinishing(false);
    setSaveState("offline");
  }, [id, flush, goResult, haptic]);

  useEffect(() => {
    if (load === "ready" && data && remaining <= 0 && !finishingRef.current) {
      setFinishOpen(false);
      setMapOpen(false);
      setTimeUp(true);
      finish();
    }
  }, [remaining, load, data, finish]);

  // --- Klaviatura ------------------------------------------------------------
  useEffect(() => {
    if (load !== "ready") return;
    const onKey = (e: KeyboardEvent) => {
      if (finishOpen || mapOpen || timeUp || e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement;
      if (target.closest("input, textarea, [contenteditable]")) return;
      let letter: string | null = null;
      const digit = /^(Digit|Numpad)([1-6])$/.exec(e.code);
      if (digit) letter = LETTERS[Number(digit[2]) - 1];
      const key = /^Key([A-F])$/.exec(e.code);
      if (key) letter = key[1];
      if (letter) {
        e.preventDefault();
        select(letter);
        return;
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        go(index + 1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        go(index - 1);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [load, finishOpen, mapOpen, timeUp, select, go, index]);

  // --- Holatlar ----------------------------------------------------------------
  if (load === "loading") return <TestSkeleton />;

  if (load === "not_found")
    return (
      <Shell>
        <StateView icon={<Grid3 size={48} filled={[0, 4]} accent={8} />} title={t("test.not_found_title")} text={t("test.not_found_text")}>
          <ButtonLink href="/start">{t("common.start")}</ButtonLink>
          <ButtonLink href="/" variant="secondary">
            {t("common.home")}
          </ButtonLink>
        </StateView>
      </Shell>
    );

  if (load === "error" || !question)
    return (
      <Shell>
        <StateView icon={<CloudOff size={40} />} title={t("test.load_error_title")} text={t("test.load_error_text")}>
          <Button onClick={fetchData}>
            <Refresh size={16} /> {t("common.retry")}
          </Button>
        </StateView>
      </Shell>
    );

  const selected = answers[question.number] ?? null;
  const isLast = index === total - 1;

  const sidebar = (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold">{t("test.answered_count", { n: answeredCount, total })}</span>
        <SaveIndicator state={saveState} />
      </div>
      <ProgressBar value={answeredCount} max={total} label={t("test.answered_count", { n: answeredCount, total })} />
      <QuestionMap
        numbers={numbers}
        answers={answers}
        currentIndex={index}
        onJump={(i) => {
          go(i);
          setMapOpen(false);
        }}
      />
    </div>
  );

  return (
    <div className="flex min-h-dvh flex-col">
      {/* Yuqori panel */}
      <header className="sticky top-0 z-40 border-b border-line/70 bg-page/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4 sm:px-6">
          <Logo compact />
          <div className="tabular text-sm font-semibold" aria-live="polite">
            <span className="text-ink">{index + 1}</span>
            <span className="text-muted"> / {total}</span>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Timer seconds={remaining} />
            <button
              onClick={() => setMapOpen(true)}
              className="focus-ring grid h-9 w-9 place-items-center rounded-full border border-line bg-surface lg:hidden"
              aria-label={t("test.map_open")}
            >
              <Grid size={17} />
            </button>
            <div className="hidden items-center gap-2 sm:flex">
              <LangSwitch />
              <ThemeToggle />
            </div>
          </div>
        </div>
        <ProgressBar value={index + 1} max={total} className="!h-[3px] !rounded-none" label={t("test.progress", { current: index + 1, total })} />
      </header>

      <main id="main" className="mx-auto grid w-full max-w-6xl flex-1 gap-8 px-4 pb-28 pt-6 sm:px-6 lg:grid-cols-[minmax(0,1fr)_300px] lg:pb-12 lg:pt-8">
        <section aria-live="polite">
          <AnimatePresence mode="wait" custom={direction} initial={false}>
            <motion.div
              key={question.number}
              custom={direction}
              initial={reduce ? { opacity: 0 } : { opacity: 0, x: direction * 48 }}
              animate={{ opacity: 1, x: 0 }}
              exit={reduce ? { opacity: 0 } : { opacity: 0, x: direction * -48 }}
              transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            >
              <div className="flex flex-wrap items-center gap-3">
                <span className="tabular inline-flex h-8 items-center rounded-full bg-ink px-3.5 text-sm font-bold text-page">
                  {t("test.question", { n: index + 1 })}
                </span>
              </div>
              <h1 className="mt-4 text-xl font-bold tracking-tight sm:text-2xl">{question.prompt[lang]}</h1>

              <div className="mt-5 rounded-panel bg-paper-panel p-4 shadow-[inset_0_0_0_1px_rgb(var(--paper-line)/0.6)] sm:p-6">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={question.figure}
                  alt={t("test.figure_alt", { n: index + 1 })}
                  className="mx-auto max-h-[36vh] w-auto max-w-full select-none object-contain sm:max-h-[300px] lg:max-h-[min(300px,34vh)]"
                  draggable={false}
                />
              </div>

              <div role="radiogroup" aria-label={question.prompt[lang]} className="mt-5 grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3">
                {question.options.map((o, i) => (
                  <OptionCard key={o.letter} option={o} index={i} type={question.type} selected={selected === o.letter} onSelect={select} />
                ))}
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Kompyuter navigatsiyasi */}
          <div className="mt-8 hidden items-center justify-between gap-3 sm:flex">
            <Button variant="secondary" onClick={() => go(index - 1)} disabled={index === 0}>
              <ArrowLeft size={18} /> {t("common.prev")}
            </Button>
            <span className="hidden items-center gap-2 text-xs text-muted md:inline-flex">
              <Keyboard size={15} /> {t("test.keyboard_hint")}
            </span>
            {isLast ? (
              <Button onClick={() => setFinishOpen(true)}>
                <Flag size={17} /> {t("test.finish")}
              </Button>
            ) : (
              <Button variant="dark" onClick={() => go(index + 1)}>
                {t("common.next")} <ArrowRight size={18} />
              </Button>
            )}
          </div>
        </section>

        {/* Yon panel (kompyuter) */}
        <aside className="hidden lg:block">
          <div className="sticky top-24 space-y-4">
            <div className="rounded-panel border border-line bg-surface p-5 shadow-soft">{sidebar}</div>
            <Button className="w-full" variant={answeredCount === total ? "primary" : "secondary"} onClick={() => setFinishOpen(true)}>
              <Flag size={17} /> {t("test.finish")}
            </Button>
          </div>
        </aside>
      </main>

      {/* Telefon navigatsiyasi */}
      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-line/70 bg-page/90 px-4 pb-[max(12px,env(safe-area-inset-bottom))] pt-3 backdrop-blur-xl sm:hidden">
        <div className="flex items-center gap-2">
          <Button variant="secondary" className="w-12 shrink-0 !px-0" onClick={() => go(index - 1)} disabled={index === 0} aria-label={t("common.prev")}>
            <ArrowLeft size={18} />
          </Button>
          {isLast ? (
            <Button className="flex-1" onClick={() => setFinishOpen(true)}>
              <Flag size={17} /> {t("test.finish")}
            </Button>
          ) : (
            <Button variant="dark" className="flex-1" onClick={() => go(index + 1)}>
              {t("common.next")} <ArrowRight size={18} />
            </Button>
          )}
        </div>
      </nav>

      {/* Savollar xaritasi (telefon/planshet) */}
      <Modal open={mapOpen} onClose={() => setMapOpen(false)} title={t("test.map")} closeLabel={t("common.close")}>
        {sidebar}
        <Button
          className="mt-6 w-full"
          variant={answeredCount === total ? "primary" : "secondary"}
          onClick={() => {
            setMapOpen(false);
            setFinishOpen(true);
          }}
        >
          <Flag size={17} /> {t("test.finish")}
        </Button>
      </Modal>

      {/* Yakunlash tasdig‘i */}
      <Modal open={finishOpen} onClose={() => !finishing && setFinishOpen(false)} title={t("test.finish_title")} closeLabel={t("common.close")} dismissible={!finishing}>
        {unanswered.length === 0 ? (
          <p className="text-muted">{t("test.finish_all")}</p>
        ) : (
          <>
            <p className="text-muted">{t("test.finish_unanswered", { n: unanswered.length })}</p>
            <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-muted">{t("test.finish_unanswered_list")}</p>
            <div className="mt-2 flex max-h-32 flex-wrap gap-1.5 overflow-y-auto">
              {unanswered.map(({ n, i }) => (
                <button
                  key={n}
                  onClick={() => {
                    go(i);
                    setFinishOpen(false);
                  }}
                  className="focus-ring tabular grid h-8 min-w-8 place-items-center rounded-full border border-line px-2 text-xs font-semibold hover:border-accent hover:text-accent"
                >
                  {i + 1}
                </button>
              ))}
            </div>
          </>
        )}
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={() => setFinishOpen(false)} disabled={finishing} data-autofocus>
            {t("test.finish_cancel")}
          </Button>
          <Button onClick={finish} disabled={finishing}>
            {finishing ? (
              <>
                <Spinner /> {t("test.finishing")}
              </>
            ) : (
              <>
                <Check size={17} strokeWidth={2.5} /> {t("test.finish_confirm")}
              </>
            )}
          </Button>
        </div>
      </Modal>

      {/* Vaqt tugadi */}
      <Modal open={timeUp} onClose={() => {}} title={t("test.timeup_title")} dismissible={false}>
        <div className="flex items-center gap-4">
          <span className="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-accent/10 text-accent">
            <Clock size={26} />
          </span>
          <p className="text-muted">{t("test.timeup_text")}</p>
        </div>
        <div className="mt-6 flex items-center gap-2 text-sm font-medium text-muted">
          <Spinner /> {t("test.finishing")}
        </div>
      </Modal>
    </div>
  );
}

function SaveIndicator({ state }: { state: SaveState }) {
  const { t } = useI18n();
  if (state === "idle") return null;
  const map = {
    saving: { icon: <Spinner size={14} />, text: t("test.saving"), cls: "text-muted" },
    saved: { icon: <Cloud size={15} />, text: t("test.saved"), cls: "text-teal" },
    offline: { icon: <CloudOff size={15} />, text: t("test.offline"), cls: "text-accent" },
  } as const;
  const s = map[state];
  return (
    <span role="status" className={`inline-flex items-center gap-1.5 text-xs font-medium ${s.cls}`} title={s.text}>
      {s.icon}
      <span className={state === "offline" ? "sr-only" : ""}>{s.text}</span>
    </span>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh">
      <header className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Logo />
        <div className="flex items-center gap-2">
          <LangSwitch />
          <ThemeToggle />
        </div>
      </header>
      <main id="main">{children}</main>
    </div>
  );
}

function TestSkeleton() {
  const { t } = useI18n();
  return (
    <div className="min-h-dvh" aria-busy="true" aria-label={t("common.loading")}>
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4 sm:px-6">
        <Skeleton className="h-9 w-9 !rounded-[10px]" />
        <Skeleton className="h-5 w-14" />
        <Skeleton className="ml-auto h-9 w-24 !rounded-full" />
      </div>
      <div className="mx-auto grid max-w-6xl gap-8 px-4 pt-6 sm:px-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div>
          <Skeleton className="h-8 w-24 !rounded-full" />
          <Skeleton className="mt-4 h-7 w-3/4" />
          <Skeleton className="mt-5 h-64 !rounded-panel sm:h-80" />
          <div className="mt-5 grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3">
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="aspect-[4/3] sm:aspect-[16/10] lg:aspect-[2/1]" />
            ))}
          </div>
        </div>
        <Skeleton className="hidden h-96 !rounded-panel lg:block" />
      </div>
    </div>
  );
}
