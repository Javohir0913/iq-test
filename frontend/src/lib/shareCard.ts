// Natija kartochkasini (1080×1080 PNG) canvas orqali chizish

import type { AttemptResult } from "./api";

export interface CardTexts {
  brand: string;
  headline: string;
  score: string;
  level: string;
  cta: string;
  url: string;
  categories: Array<{ name: string; percent: number }>;
}

const C = {
  ink: "#1B2A41",
  accent: "#E4572E",
  teal: "#2A7F8F",
  soft: "#9AB3C2",
  panel: "#F4F1EA",
  page: "#FBFAF7",
  line: "#D6D0C4",
  muted: "#7A8291",
};

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function star(ctx: CanvasRenderingContext2D, cx: number, cy: number, outer: number, inner: number, points: number) {
  ctx.beginPath();
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 === 0 ? outer : inner;
    const a = (Math.PI / points) * i - Math.PI / 2;
    const x = cx + r * Math.cos(a);
    const y = cy + r * Math.sin(a);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
}

function fitText(ctx: CanvasRenderingContext2D, text: string, weight: number, maxSize: number, maxWidth: number, family: string) {
  let size = maxSize;
  do {
    ctx.font = `${weight} ${size}px ${family}`;
    if (ctx.measureText(text).width <= maxWidth) break;
    size -= 2;
  } while (size > 20);
  return size;
}

export async function renderShareCard(result: AttemptResult, texts: CardTexts): Promise<Blob> {
  const S = 1080;
  const canvas = document.createElement("canvas");
  canvas.width = S;
  canvas.height = S;
  const ctx = canvas.getContext("2d")!;
  const family = getComputedStyle(document.body).fontFamily || "Inter, sans-serif";
  try {
    await document.fonts.ready;
  } catch {
    /* e’tiborsiz */
  }

  // Fon
  ctx.fillStyle = C.page;
  ctx.fillRect(0, 0, S, S);
  ctx.fillStyle = "rgba(27,42,65,0.08)";
  for (let x = 30; x < S; x += 36) for (let y = 30; y < S; y += 36) ctx.fillRect(x, y, 2.4, 2.4);

  // Asosiy panel
  roundRect(ctx, 60, 60, S - 120, S - 120, 44);
  ctx.fillStyle = "#FFFFFF";
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.line;
  ctx.stroke();

  // Bezaklar
  ctx.fillStyle = C.ink;
  star(ctx, S - 170, 175, 46, 17, 4);
  ctx.fill();
  ctx.fillStyle = C.soft;
  star(ctx, S - 110, 250, 26, 12, 5);
  ctx.fill();
  ctx.fillStyle = C.teal;
  ctx.beginPath();
  ctx.moveTo(S - 250, 238);
  ctx.lineTo(S - 276, 282);
  ctx.lineTo(S - 224, 282);
  ctx.closePath();
  ctx.fill();

  // Brend
  roundRect(ctx, 130, 130, 56, 56, 14);
  ctx.fillStyle = C.ink;
  ctx.fill();
  roundRect(ctx, 160, 160, 22, 22, 6);
  ctx.fillStyle = C.accent;
  ctx.fill();
  ctx.fillStyle = "#fff";
  star(ctx, 149, 149, 12, 4.5, 4);
  ctx.fill();
  ctx.fillStyle = C.ink;
  ctx.font = `700 26px ${family}`;
  ctx.textBaseline = "middle";
  ctx.fillText(texts.brand, 206, 159);

  // Sarlavha va ism
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = C.muted;
  ctx.font = `600 30px ${family}`;
  ctx.fillText(texts.headline, 130, 290);
  ctx.fillStyle = C.ink;
  fitText(ctx, result.full_name, 700, 58, S - 260, family);
  ctx.fillText(result.full_name, 130, 360);

  // Ball halqasi
  const cx = 300;
  const cy = 600;
  const r = 150;
  ctx.lineCap = "round";
  ctx.lineWidth = 30;
  ctx.strokeStyle = C.panel;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.stroke();
  const ratio = Math.max(0, Math.min(1, result.total_score / result.max_score));
  const grad = ctx.createLinearGradient(cx - r, cy - r, cx + r, cy + r);
  grad.addColorStop(0, C.accent);
  grad.addColorStop(1, "#F2A07B");
  ctx.strokeStyle = grad;
  ctx.beginPath();
  ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * ratio);
  ctx.stroke();
  ctx.textAlign = "center";
  ctx.fillStyle = C.ink;
  ctx.font = `800 92px ${family}`;
  ctx.fillText(String(result.total_score), cx, cy + 20);
  ctx.fillStyle = C.muted;
  ctx.font = `600 28px ${family}`;
  ctx.fillText(`/ ${result.max_score} ${texts.score}`, cx, cy + 66);
  ctx.textAlign = "left";

  // Daraja va foiz
  const lx = 520;
  ctx.font = `700 40px ${family}`;
  const levelW = Math.min(ctx.measureText(texts.level).width + 64, S - lx - 130);
  roundRect(ctx, lx, 470, levelW, 76, 38);
  ctx.fillStyle = C.accent;
  ctx.fill();
  ctx.fillStyle = "#fff";
  fitText(ctx, texts.level, 700, 40, levelW - 64, family);
  ctx.fillText(texts.level, lx + 32, 522);
  ctx.fillStyle = C.ink;
  ctx.font = `800 64px ${family}`;
  ctx.fillText(`${Math.round(result.percent)}%`, lx, 630);

  // Kategoriyalar
  let y = 700;
  texts.categories.forEach((c) => {
    ctx.fillStyle = C.ink;
    fitText(ctx, c.name, 600, 24, 300, family);
    ctx.fillText(c.name, lx, y);
    ctx.font = `700 24px ${family}`;
    ctx.textAlign = "right";
    ctx.fillText(`${Math.round(c.percent)}%`, S - 130, y);
    ctx.textAlign = "left";
    roundRect(ctx, lx, y + 14, S - 130 - lx, 12, 6);
    ctx.fillStyle = C.panel;
    ctx.fill();
    roundRect(ctx, lx, y + 14, Math.max(12, (S - 130 - lx) * (c.percent / 100)), 12, 6);
    ctx.fillStyle = C.teal;
    ctx.fill();
    y += 70;
  });

  // Pastki chiziq
  ctx.strokeStyle = C.line;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(130, S - 200);
  ctx.lineTo(S - 130, S - 200);
  ctx.stroke();
  ctx.fillStyle = C.ink;
  ctx.font = `700 30px ${family}`;
  ctx.fillText(texts.cta, 130, S - 135);
  ctx.fillStyle = C.accent;
  ctx.font = `600 28px ${family}`;
  ctx.textAlign = "right";
  ctx.fillText(texts.url.replace(/^https?:\/\//, ""), S - 130, S - 135);
  ctx.textAlign = "left";

  // 3×3 panjara bezagi
  const gx = S - 236;
  const gy = 330;
  for (let i = 0; i < 9; i++) {
    const x = gx + (i % 3) * 36;
    const yy = gy + Math.floor(i / 3) * 36;
    roundRect(ctx, x, yy, 30, 30, 7);
    if (i === 8) {
      ctx.fillStyle = C.accent;
      ctx.fill();
    } else if (i === 0 || i === 4) {
      ctx.fillStyle = C.ink;
      ctx.fill();
    } else {
      ctx.strokeStyle = C.line;
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }

  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("toBlob failed"))), "image/png"),
  );
}
