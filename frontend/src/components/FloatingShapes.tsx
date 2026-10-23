// Fondagi suzuvchi geometrik shakllar (faqat CSS animatsiya, JS yo‘q)
import { CurvedArrow, Diamond, Grid3, Ring, Star, Triangle } from "./shapes";

interface Item {
  el: React.ReactNode;
  className: string;
  x: string;
  y: string;
  drift: number;
  r1: number;
  dur: number;
  delay: number;
  spin?: boolean;
}

const ITEMS: Item[] = [
  { el: <Star points={4} inner={0.38} size={34} />, className: "text-ink/80", x: "6%", y: "18%", drift: -14, r1: 45, dur: 14, delay: 0 },
  { el: <Triangle size={26} />, className: "text-teal/70", x: "88%", y: "14%", drift: -18, r1: 30, dur: 18, delay: 1 },
  { el: <Grid3 size={54} filled={[0, 4, 8]} accent={2} />, className: "text-ink/25", x: "80%", y: "72%", drift: -10, r1: 0, dur: 20, delay: 2 },
  { el: <Ring size={30} />, className: "text-soft", x: "46%", y: "88%", drift: -16, r1: 0, dur: 16, delay: 0.5 },
  { el: <CurvedArrow size={32} />, className: "text-accent/80", x: "48%", y: "6%", drift: 0, r1: 0, dur: 30, delay: 0, spin: true },
  { el: <Star points={6} inner={0.55} size={22} />, className: "text-soft/80", x: "93%", y: "44%", drift: -12, r1: 60, dur: 15, delay: 3 },
  { el: <Diamond size={20} />, className: "text-ink/15", x: "3%", y: "50%", drift: -10, r1: 45, dur: 17, delay: 1.5 },
];

export function FloatingShapes({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}>
      {ITEMS.map((it, i) => (
        <div
          key={i}
          className="anim-pop absolute"
          style={{ left: it.x, top: it.y, ["--delay" as string]: `${0.2 + i * 0.08}s` }}
        >
          <div
            className={`${it.spin ? "anim-spin" : "anim-float"} ${it.className}`}
            style={{
              ["--drift" as string]: `${it.drift}px`,
              ["--r1" as string]: `${it.r1}deg`,
              ["--dur" as string]: `${it.dur}s`,
              ["--delay" as string]: `${it.delay}s`,
            }}
          >
            {it.el}
          </div>
        </div>
      ))}
    </div>
  );
}
