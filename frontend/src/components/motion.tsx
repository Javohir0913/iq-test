"use client";

// Silliq paydo bo‘lish / yo‘qolish uchun umumiy yordamchilar (framer-motion)
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

const EASE = [0.22, 1, 0.36, 1] as const;

/** Shartli blok (xato xabari, karta): balandligi silliq ochiladi va yopiladi. */
export function Collapse({ show, children, className = "" }: { show: boolean; children: React.ReactNode; className?: string }) {
  const reduce = useReducedMotion();
  const hidden = reduce ? { opacity: 0 } : { opacity: 0, height: 0 };
  return (
    <AnimatePresence initial={false}>
      {show && (
        <motion.div
          key="collapse"
          initial={hidden}
          animate={{ opacity: 1, height: "auto" }}
          exit={hidden}
          transition={{ duration: 0.28, ease: EASE }}
          style={{ overflow: "hidden" }}
          className={className}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/** Holat almashganda (yuklanmoqda → kontent) eski ko‘rinish so‘nib, yangisi silliq chiqadi. */
export function FadeSwap({ id, children, className }: { id: string; children: React.ReactNode; className?: string }) {
  const reduce = useReducedMotion();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={id}
        initial={{ opacity: 0, y: reduce ? 0 : 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: reduce ? 0 : -6 }}
        transition={{ duration: 0.22, ease: EASE }}
        className={className}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
