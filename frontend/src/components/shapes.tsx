// Test uslubidagi geometrik shakllar (yulduz, uchburchak, panjara, strelka)

type ShapeProps = React.SVGProps<SVGSVGElement> & { size?: number };

function starPath(points: number, outer: number, inner: number, cx = 50, cy = 50) {
  const pts: string[] = [];
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 === 0 ? outer : inner;
    const a = (Math.PI / points) * i - Math.PI / 2;
    pts.push(`${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a)).toFixed(2)}`);
  }
  return `M${pts.join("L")}Z`;
}

export function Star({ points = 5, inner = 0.45, size = 48, ...rest }: Omit<ShapeProps, "points"> & { points?: number; inner?: number }) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} aria-hidden {...rest}>
      <path d={starPath(points, 46, 46 * inner)} fill="currentColor" />
    </svg>
  );
}

export function Triangle({ size = 48, ...rest }: ShapeProps) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} aria-hidden {...rest}>
      <path d="M50 8 94 88H6Z" fill="currentColor" />
    </svg>
  );
}

export function Ring({ size = 48, ...rest }: ShapeProps) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} aria-hidden {...rest}>
      <circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" strokeWidth="9" />
    </svg>
  );
}

export function Grid3({ size = 48, filled = [0, 4], accent, ...rest }: ShapeProps & { filled?: number[]; accent?: number }) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} aria-hidden {...rest}>
      {Array.from({ length: 9 }, (_, i) => {
        const x = 6 + (i % 3) * 30;
        const y = 6 + Math.floor(i / 3) * 30;
        const isAccent = accent === i;
        return (
          <rect
            key={i}
            x={x}
            y={y}
            width="28"
            height="28"
            rx="5"
            fill={isAccent ? "rgb(var(--accent))" : filled.includes(i) ? "currentColor" : "none"}
            stroke={isAccent ? "none" : "currentColor"}
            strokeWidth="3"
          />
        );
      })}
    </svg>
  );
}

export function CurvedArrow({ size = 48, ...rest }: ShapeProps) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} aria-hidden {...rest}>
      <path
        d="M78 52a28 28 0 1 1-9-21"
        fill="none"
        stroke="currentColor"
        strokeWidth="9"
        strokeLinecap="round"
      />
      <path d="M58 16l20 4-6 19z" fill="currentColor" />
    </svg>
  );
}

export function Diamond({ size = 48, ...rest }: ShapeProps) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} aria-hidden {...rest}>
      <path d="M50 6 94 50 50 94 6 50Z" fill="currentColor" />
    </svg>
  );
}
