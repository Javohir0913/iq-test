"use client";

import { motion, useReducedMotion } from "framer-motion";
import { memo } from "react";
import { useI18n } from "@/i18n";
import type { PublicOption } from "@/lib/api";
import { Check, Clock } from "./icons";

// --- OptionCard ---------------------------------------------------------------

export const OptionCard = memo(function OptionCard({
  option,
  index,
  selected,
  onSelect,
  type,
}: {
  option: PublicOption;
  index: number;
  selected: boolean;
  onSelect: (letter: string) => void;
  type: "number" | "image";
}) {
  const { t } = useI18n();
  const reduce = useReducedMotion();
  return (
    <motion.button
      type="button"
      role="radio"
      aria-checked={selected}
      aria-label={`${t("test.option", { letter: option.letter })}${option.value !== null ? `: ${option.value}` : ""}`}
      data-letter={option.letter}
      onClick={() => onSelect(option.letter)}
      initial={reduce ? false : { opacity: 0, y: 10 }}
      animate={reduce ? undefined : { opacity: 1, y: 0, scale: selected ? [1, 1.035, 1] : 1 }}
      transition={{
        opacity: { delay: 0.05 + index * 0.035, duration: 0.25 },
        y: { delay: 0.05 + index * 0.035, duration: 0.3, ease: [0.22, 1, 0.36, 1] },
        scale: { duration: 0.32, ease: "easeOut" },
      }}
      whileHover={reduce ? undefined : { y: -2 }}
      whileTap={reduce ? undefined : { scale: 0.97 }}
      className={`group relative flex aspect-[4/3] w-full items-center justify-center overflow-hidden rounded-card border-2 bg-paper text-paper-ink outline-none transition-[border-color,box-shadow] duration-200 focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-page sm:aspect-[16/10] lg:aspect-[2/1] ${
        selected
          ? "border-accent shadow-glow"
          : "border-paper-line shadow-soft hover:border-paper-ink/35"
      }`}
    >
      <span
        className={`absolute left-2.5 top-2.5 grid h-7 w-7 place-items-center rounded-full text-xs font-bold transition-colors duration-200 sm:left-3 sm:top-3 ${
          selected ? "bg-accent text-white" : "bg-paper-panel text-paper-ink"
        }`}
        aria-hidden
      >
        {option.letter}
      </span>
      {selected && (
        <motion.span
          initial={reduce ? false : { scale: 0, rotate: -45 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 500, damping: 22 }}
          className="absolute right-2.5 top-2.5 grid h-6 w-6 place-items-center rounded-full bg-accent text-white sm:right-3 sm:top-3"
          aria-hidden
        >
          <Check size={14} strokeWidth={3} />
        </motion.span>
      )}
      {type === "number" ? (
        <span className="tabular text-4xl font-bold tracking-tight sm:text-5xl">{option.value}</span>
      ) : option.image ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={option.image}
          alt={t("test.option_alt", { letter: option.letter })}
          className="h-[66%] w-[66%] object-contain lg:h-[72%] transition-transform duration-300 group-hover:scale-[1.03]"
          draggable={false}
        />
      ) : null}
    </motion.button>
  );
});

// --- Timer --------------------------------------------------------------------

export function Timer({ seconds }: { seconds: number }) {
  const { t } = useI18n();
  const s = Math.max(0, Math.floor(seconds));
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  const warn = s <= 300;
  const critical = s <= 60;
  return (
    <div
      role="timer"
      aria-label={t("test.time_left")}
      className={`tabular inline-flex h-9 items-center gap-1.5 rounded-full border px-3 text-sm font-semibold transition-colors ${
        critical
          ? "animate-pulse border-accent bg-accent text-white"
          : warn
            ? "border-accent/40 bg-accent/10 text-accent"
            : "border-line bg-surface text-ink"
      }`}
    >
      <Clock size={15} />
      <span>
        {mm}:{ss}
      </span>
    </div>
  );
}

// --- QuestionMap --------------------------------------------------------------

export function QuestionMap({
  numbers,
  answers,
  currentIndex,
  onJump,
}: {
  numbers: number[];
  answers: Record<string, string | null | undefined>;
  currentIndex: number;
  onJump: (index: number) => void;
}) {
  const { t } = useI18n();
  return (
    <div>
      <nav aria-label={t("test.map")} className="grid grid-cols-7 gap-2">
        {numbers.map((n, i) => {
          const answered = Boolean(answers[n]);
          const current = i === currentIndex;
          return (
            <button
              key={n}
              onClick={() => onJump(i)}
              aria-current={current ? "step" : undefined}
              aria-label={`${t("test.question", { n: i + 1 })} — ${answered ? t("test.answered") : t("test.unanswered")}`}
              className={`focus-ring tabular relative grid aspect-square place-items-center rounded-full text-xs font-semibold transition-all duration-200 ${
                current
                  ? "bg-accent text-white shadow-glow"
                  : answered
                    ? "bg-ink text-page hover:bg-ink/85"
                    : "border border-line bg-surface text-muted hover:border-ink/40 hover:text-ink"
              }`}
            >
              {i + 1}
            </button>
          );
        })}
      </nav>
      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-muted">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-ink" /> {t("test.answered")}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full border border-line bg-surface" /> {t("test.unanswered")}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-accent" /> {t("test.current")}
        </span>
      </div>
    </div>
  );
}
