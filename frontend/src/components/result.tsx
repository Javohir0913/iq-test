"use client";

import { animate, motion, useInView, useMotionValue, useReducedMotion, useTransform } from "framer-motion";
import { useEffect, useRef, useState } from "react";

// Sanab chiqadigan son
export function CountUp({ to, duration = 1.6, decimals = 0, className = "" }: { to: number; duration?: number; decimals?: number; className?: string }) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const mv = useMotionValue(0);
  const text = useTransform(mv, (v) => v.toFixed(decimals));
  const [display, setDisplay] = useState(reduce ? to.toFixed(decimals) : (0).toFixed(decimals));

  useEffect(() => text.on("change", setDisplay), [text]);
  useEffect(() => {
    if (!inView) return;
    if (reduce) {
      setDisplay(to.toFixed(decimals));
      return;
    }
    const controls = animate(mv, to, { duration, ease: [0.16, 1, 0.3, 1] });
    return () => controls.stop();
  }, [inView, to, duration, mv, reduce, decimals]);

  return (
    <span ref={ref} className={`tabular ${className}`}>
      {display}
    </span>
  );
}

// Ball halqasi
export function ScoreRing({ score, max, size = 260, children }: { score: number; max: number; size?: number; children?: React.ReactNode }) {
  const reduce = useReducedMotion();
  const stroke = 18;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const ratio = max ? Math.min(1, Math.max(0, score / max)) : 0;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90" aria-hidden>
        <defs>
          <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="rgb(var(--accent))" />
            <stop offset="100%" stopColor="#F2A07B" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgb(var(--ink) / 0.07)" strokeWidth={stroke} />
        {/* 60 ta nozik bo‘lak */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r - stroke - 6}
          fill="none"
          stroke="rgb(var(--ink) / 0.12)"
          strokeWidth={6}
          strokeDasharray={`1.5 ${(2 * Math.PI * (r - stroke - 6)) / 60 - 1.5}`}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="url(#ring-grad)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ * (1 - ratio) }}
          transition={reduce ? { duration: 0 } : { duration: 1.8, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">{children}</div>
    </div>
  );
}

export function CategoryBar({ name, percent, score, max, delay = 0, tone }: { name: string; percent: number; score: number; max: number; delay?: number; tone: string }) {
  const reduce = useReducedMotion();
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-semibold">{name}</span>
        <span className="tabular text-sm text-muted">
          {score} / {max} · <span className="font-bold text-ink">{Math.round(percent)}%</span>
        </span>
      </div>
      <div
        className="mt-2.5 h-3 overflow-hidden rounded-full bg-ink/[0.07]"
        role="progressbar"
        aria-label={name}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(percent)}
      >
        <motion.div
          className={`h-full rounded-full ${tone}`}
          initial={{ width: 0 }}
          whileInView={{ width: `${percent}%` }}
          viewport={{ once: true }}
          transition={reduce ? { duration: 0 } : { duration: 1.2, ease: [0.16, 1, 0.3, 1], delay }}
        />
      </div>
    </div>
  );
}
