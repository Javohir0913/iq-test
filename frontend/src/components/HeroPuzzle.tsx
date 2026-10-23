// Bosh sahifadagi bezak-jumboq: test uslubidagi 3×3 panel (haqiqiy test savoli emas). Faqat CSS animatsiya.
import { Grid3, Star, Triangle } from "./shapes";

const TILES: React.ReactNode[] = [
  <Triangle key="t0" size={44} />,
  <Triangle key="t1" size={44} className="rotate-90" />,
  <Triangle key="t2" size={44} className="rotate-180" />,
  <Star key="s4" points={4} inner={0.4} size={50} />,
  <Star key="s5" points={5} inner={0.45} size={50} />,
  <Star key="s6" points={6} inner={0.55} size={50} />,
  <Grid3 key="g1" size={48} filled={[0]} />,
  <Grid3 key="g2" size={48} filled={[0, 4]} />,
];

const delay = (s: number) => ({ ["--delay" as string]: `${s}s` });

export function HeroPuzzle({ brand, total }: { brand: string; total: number }) {
  return (
    <div className="relative">
      <div aria-hidden className="anim-glow absolute -inset-6 rounded-[32px] bg-gradient-to-br from-accent/20 via-transparent to-teal/20 blur-2xl" />
      <div
        className="anim-fade-up relative rounded-[24px] border border-paper-line bg-paper-panel p-5 shadow-lift sm:p-7"
        style={delay(0)}
        aria-hidden
      >
        <div className="mb-4 flex items-center justify-between text-[11px] font-semibold uppercase tracking-[0.14em] text-paper-ink/80">
          <span>{brand}</span>
          <span className="tabular">? / {total}</span>
        </div>
        <div className="grid grid-cols-3 gap-3 sm:gap-4">
          {TILES.map((tile, i) => (
            <div
              key={i}
              className="anim-pop grid aspect-square place-items-center rounded-card border border-paper-line bg-paper text-paper-ink"
              style={delay(0.1 + i * 0.04)}
            >
              <div
                className="anim-float"
                style={{ ["--drift" as string]: "-3px", ["--dur" as string]: `${3 + (i % 3)}s`, ["--delay" as string]: `${i * 0.2}s` }}
              >
                {tile}
              </div>
            </div>
          ))}
          <div className="anim-pop" style={delay(0.45)}>
            <div className="anim-pulse grid aspect-square place-items-center rounded-card bg-accent text-5xl font-bold text-white shadow-glow">
              ?
            </div>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-6 gap-2">
          {["A", "B", "C", "D", "E", "F"].map((l, i) => (
            <div
              key={l}
              className={`anim-fade-up grid h-9 place-items-center rounded-[10px] border text-xs font-bold ${
                i === 3 ? "border-accent bg-accent/10 text-[#B83A16]" : "border-paper-line bg-paper text-paper-ink/80"
              }`}
              style={delay(0.4 + i * 0.04)}
            >
              {l}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
