"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useId, useRef } from "react";
import { X } from "./icons";

export { Button, ButtonLink, buttonClass } from "./button";

// --- Card ---------------------------------------------------------------------

export function Card({ className = "", children, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`rounded-card border border-line bg-surface shadow-soft ${className}`} {...rest}>
      {children}
    </div>
  );
}

// --- ProgressBar --------------------------------------------------------------

export function ProgressBar({ value, max, label, className = "" }: { value: number; max: number; label?: string; className?: string }) {
  const pct = max ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value}
      aria-label={label}
      className={`h-1.5 w-full overflow-hidden rounded-full bg-ink/[0.08] ${className}`}
    >
      <motion.div
        className="h-full rounded-full bg-gradient-to-r from-accent to-[#F08A5D]"
        initial={false}
        animate={{ width: `${pct}%` }}
        transition={{ type: "spring", stiffness: 120, damping: 22 }}
      />
    </div>
  );
}

// --- Skeleton -----------------------------------------------------------------

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden rounded-card bg-ink/[0.06] ${className}`} aria-hidden>
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/40 to-transparent dark:via-white/[0.06]" />
    </div>
  );
}

// --- Modal --------------------------------------------------------------------

export function Modal({
  open,
  onClose,
  title,
  children,
  dismissible = true,
  closeLabel = "Close",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  dismissible?: boolean;
  closeLabel?: string;
}) {
  const id = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && dismissible) onClose();
      if (e.key === "Tab" && panelRef.current) {
        const focusables = panelRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), a[href], input, [tabindex]:not([tabindex="-1"])',
        );
        if (!focusables.length) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const t = setTimeout(() => {
      panelRef.current?.querySelector<HTMLElement>("[data-autofocus]")?.focus() ?? panelRef.current?.focus();
    }, 30);
    return () => {
      clearTimeout(t);
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      prev?.focus?.();
    };
  }, [open, dismissible, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-end justify-center p-3 sm:items-center sm:p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
        >
          <div
            className="absolute inset-0 bg-[#0b111c]/45 backdrop-blur-[3px]"
            onClick={() => dismissible && onClose()}
            aria-hidden
          />
          <motion.div
            ref={panelRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby={id}
            tabIndex={-1}
            className="relative w-full max-w-md rounded-panel border border-line bg-surface p-6 shadow-lift outline-none sm:p-7"
            initial={reduce ? { opacity: 0 } : { opacity: 0, y: 24, scale: 0.97 }}
            animate={reduce ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, y: 16, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 380, damping: 32 }}
          >
            {dismissible && (
              <button
                onClick={onClose}
                className="focus-ring absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full text-muted hover:bg-ink/[0.06] hover:text-ink"
                aria-label={closeLabel}
              >
                <X size={18} />
              </button>
            )}
            <h2 id={id} className="pr-8 text-xl font-bold tracking-tight">
              {title}
            </h2>
            <div className="mt-3">{children}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export { StateView } from "./state-view";
