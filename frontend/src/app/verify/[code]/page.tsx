// Sertifikatni tekshirish (QR kod shu sahifani ochadi). Ma’lumot serverdan – PDF’dan emas.
import type { Metadata } from "next";
import { Header } from "@/components/Header";
import { Check, CloudOff, Send, X } from "@/components/icons";
import { VerifyForm } from "@/components/VerifyForm";
import { LOCALES, localized, translate } from "@/i18n/core";
import { serverLang, verifyCertificate } from "@/lib/serverApi";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const lang = await serverLang();
  // Tekshiruv sahifalari qidiruv tizimlariga chiqmasin
  return { title: translate(lang, "verify.title"), robots: { index: false, follow: false } };
}

export default async function VerifyPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const lang = await serverLang();
  const t = (k: string, v?: Record<string, string | number>) => translate(lang, k, v);
  const data = await verifyCertificate(code);

  let content: React.ReactNode;
  if (data === "error") {
    content = (
      <div className="text-center">
        <span className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-ink/[0.06] text-muted">
          <CloudOff size={36} />
        </span>
        <h1 className="mt-5 text-2xl font-bold tracking-tight">{t("errors.generic_title")}</h1>
        <p className="mt-2 text-muted">{t("errors.generic_text")}</p>
      </div>
    );
  } else if (!data) {
    content = (
      <>
        <div className="text-center">
          <span className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-accent/10 text-accent">
            <X size={40} strokeWidth={2.5} />
          </span>
          <h1 className="mt-5 text-2xl font-bold tracking-tight sm:text-3xl">{t("verify.invalid")}</h1>
          <p className="mx-auto mt-2 max-w-md text-muted">{t("verify.invalid_text")}</p>
        </div>
        <div className="mt-8">
          <VerifyForm initial={code.toUpperCase()} />
        </div>
      </>
    );
  } else {
    const level = localized(data.level, "name", lang) || "—";
    const date = data.finished_at
      ? new Intl.DateTimeFormat(LOCALES[lang], {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
          timeZone: "Asia/Tashkent",
        }).format(new Date(data.finished_at))
      : "—";
    const rows: Array<[string, React.ReactNode]> = [
      [t("verify.score"), <span className="tabular">{`${data.total_score} / ${data.max_score}`}</span>],
      [t("verify.percent"), <span className="tabular">{`${Math.round(data.percent)}%`}</span>],
      [t("verify.level"), level],
      [t("verify.date"), <span className="tabular">{date}</span>],
      [t("verify.code"), <span className="tabular whitespace-nowrap tracking-wider">{data.code}</span>],
    ];
    content = (
      <>
        <div className="text-center">
          <span className="anim-pop mx-auto grid h-20 w-20 place-items-center rounded-full bg-teal text-white shadow-[0_0_0_8px_rgb(var(--teal)/0.15)]">
            <Check size={40} strokeWidth={3} />
          </span>
          <h1 className="mt-5 text-2xl font-bold tracking-tight text-teal sm:text-3xl">{t("verify.valid")}</h1>
        </div>
        <div className="mt-7 rounded-card border border-line bg-surface-2 p-5 text-center">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted">{t("verify.name")}</p>
          <p className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">{data.full_name}</p>
          {data.telegram_verified && (
            <p className="mt-2 flex items-center justify-center gap-1.5 text-sm font-medium text-teal">
              <Send size={14} /> {t("verify.telegram")}
            </p>
          )}
        </div>
        <dl className="mt-4 divide-y divide-line rounded-card border border-line">
          {rows.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between gap-4 px-5 py-3.5">
              <dt className="text-sm text-muted">{label}</dt>
              <dd className="text-right font-semibold">{value}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-5 rounded-card bg-accent/[0.08] px-4 py-3 text-sm leading-relaxed text-ink/80">{t("verify.valid_text")}</p>
      </>
    );
  }

  return (
    <>
      <Header />
      <main id="main" className="mx-auto max-w-xl px-4 py-8 sm:px-6 md:py-14">
        <div className="anim-fade-up rounded-panel border border-line bg-surface p-6 shadow-lift sm:p-8">{content}</div>
        {data && data !== "error" && (
          <div className="mt-8">
            <p className="mb-2 text-sm font-semibold text-muted">{t("verify.another")}</p>
            <VerifyForm />
          </div>
        )}
      </main>
    </>
  );
}
