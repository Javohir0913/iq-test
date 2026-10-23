// Bosh sahifa – server komponenti: tez yuklanishi uchun animatsiyalar faqat CSS bilan.
import { cookies } from "next/headers";
import { FloatingShapes } from "@/components/FloatingShapes";
import { Header } from "@/components/Header";
import { HeroPuzzle } from "@/components/HeroPuzzle";
import { RevealScope } from "@/components/RevealScope";
import { ArrowRight, Clock, Flag, Grid } from "@/components/icons";
import { CurvedArrow, Grid3, Star } from "@/components/shapes";
import { ButtonLink } from "@/components/button";
import { LANG_COOKIE, translate, translateList, type Lang } from "@/i18n/core";
import { getServerMeta } from "@/lib/serverMeta";

export const dynamic = "force-dynamic";

const d = (s: number) => ({ ["--delay" as string]: `${s}s` });

export default async function HomePage() {
  const lang: Lang = (await cookies()).get(LANG_COOKIE)?.value === "ru" ? "ru" : "uz";
  const meta = await getServerMeta();
  const t = (key: string, vars?: Record<string, string | number>) => translate(lang, key, vars);
  const vars = { count: meta.question_count, minutes: meta.duration_minutes };
  const steps = translateList<{ title: string; text: string }>(lang, "home.steps");
  const stepIcons = [Grid, Clock, Flag];

  const categories = [
    { key: "numeric", icon: <span className="tabular text-xl font-bold">2·4·8</span>, tone: "bg-[#C9471F] text-white" },
    { key: "pattern", icon: <Grid3 size={34} filled={[0, 4, 8]} />, tone: "bg-ink text-page" },
    { key: "spatial", icon: <CurvedArrow size={34} />, tone: "bg-teal text-white" },
  ];

  return (
    <>
      <Header />
      <RevealScope />
      <main id="main">
        {/* Hero */}
        <section className="relative isolate overflow-hidden">
          <div className="dot-grid absolute inset-0 -z-10 [mask-image:radial-gradient(ellipse_at_top,black_30%,transparent_75%)]" />
          <FloatingShapes className="-z-10" />
          <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-16 pt-10 sm:px-6 md:pt-16 lg:grid-cols-[1.1fr_1fr] lg:gap-16 lg:pb-24">
            <div>
              <div className="anim-fade-up inline-flex items-center gap-2 rounded-full border border-line bg-surface/80 px-3 py-1.5 text-xs font-semibold text-muted shadow-soft backdrop-blur">
                <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                <span className="tabular">{t("home.badge", vars)}</span>
              </div>
              <h1 className="mt-5 text-[40px] font-bold leading-[1.05] tracking-[-0.03em] sm:text-6xl lg:text-[68px]">
                {t("home.title_1")}{" "}
                <span className="relative inline-block whitespace-nowrap text-accent">
                  {t("home.title_accent")}
                  <svg aria-hidden viewBox="0 0 300 16" preserveAspectRatio="none" className="absolute -bottom-2 left-0 h-3 w-full text-accent/35">
                    <path d="M3 11c60-8 140-10 294-4" pathLength={1} className="anim-draw" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" />
                  </svg>
                </span>{" "}
                {t("home.title_2")}
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted">{t("home.subtitle")}</p>
              <div className="anim-fade-up mt-8 flex flex-col gap-3 sm:flex-row" style={d(0.15)}>
                <ButtonLink href="/start" size="lg" className="group">
                  {t("home.cta")}
                  <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
                </ButtonLink>
                <ButtonLink href="#how" size="lg" variant="secondary">
                  {t("home.secondary")}
                </ButtonLink>
              </div>
              <dl className="anim-fade-up mt-10 grid max-w-lg grid-cols-3 gap-3" style={d(0.3)}>
                {[
                  { value: meta.question_count, label: t("home.stats.questions") },
                  { value: meta.duration_minutes, label: t("home.stats.minutes") },
                  { value: meta.options_per_question, label: t("home.stats.options") },
                ].map((s) => (
                  <div key={s.label} className="flex flex-col-reverse rounded-card border border-line bg-surface/70 px-4 py-3 backdrop-blur">
                    <dt className="text-xs leading-snug text-muted">{s.label}</dt>
                    <dd className="tabular text-2xl font-bold tracking-tight">{s.value}</dd>
                  </div>
                ))}
              </dl>
            </div>
            <div className="mx-auto w-full max-w-[440px]">
              <HeroPuzzle brand={t("common.brand")} total={meta.question_count} />
            </div>
          </div>
        </section>

        {/* Qanday ishlaydi */}
        <section id="how" className="scroll-mt-20 border-y border-line/70 bg-surface-2/60">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:py-24">
            <div className="reveal max-w-2xl">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{t("home.how_title")}</h2>
              <p className="mt-3 text-muted">{t("home.how_subtitle")}</p>
            </div>
            <ol className="mt-10 grid gap-4 md:grid-cols-3">
              {steps.map((step, i) => {
                const Icon = stepIcons[i] ?? Grid;
                return (
                  <li
                    key={i}
                    style={d(0.08 * (i + 1))}
                    className="reveal group relative overflow-hidden rounded-panel border border-line bg-surface p-6 shadow-soft transition-shadow hover:shadow-lift"
                  >
                    <div className="flex items-center justify-between">
                      <span className="grid h-11 w-11 place-items-center rounded-btn bg-panel text-ink">
                        <Icon size={20} />
                      </span>
                      <span aria-hidden className="tabular text-5xl font-bold text-ink/[0.07] transition-colors duration-300 group-hover:text-accent/20">
                        0{i + 1}
                      </span>
                    </div>
                    <h3 className="mt-5 text-lg font-bold tracking-tight">{t(`home.steps.${i}.title`, vars)}</h3>
                    <p className="mt-2 text-[15px] leading-relaxed text-muted">{step.text}</p>
                  </li>
                );
              })}
            </ol>
          </div>
        </section>

        {/* Kategoriyalar */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:py-24">
          <h2 className="reveal text-3xl font-bold tracking-tight sm:text-4xl">{t("home.categories_title")}</h2>
          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {categories.map((c, i) => (
              <div key={c.key} style={d(0.08 * (i + 1))} className="reveal flex gap-4 rounded-panel border border-line bg-surface p-5 shadow-soft">
                <span aria-hidden className={`grid h-16 w-16 shrink-0 place-items-center rounded-card ${c.tone}`}>
                  {c.icon}
                </span>
                <div>
                  <h3 className="font-bold tracking-tight">{t(`home.categories.${c.key}.title`)}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-muted">{t(`home.categories.${c.key}.text`)}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Yakuniy chaqiriq */}
        <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
          <div className="reveal relative isolate overflow-hidden rounded-[28px] bg-[#1B2A41] px-6 py-12 text-white sm:px-12 sm:py-16">
            <div aria-hidden className="anim-spin absolute -right-6 -top-8 -z-10 text-white/10" style={{ ["--dur" as string]: "60s" }}>
              <Star points={8} inner={0.5} size={220} />
            </div>
            <div aria-hidden className="absolute bottom-6 right-10 -z-10 hidden sm:block">
              <Grid3 size={70} filled={[]} accent={8} className="text-white/30" />
            </div>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{t("home.final_title")}</h2>
            <p className="mt-3 max-w-lg text-white/75">{t("home.final_text", vars)}</p>
            <ButtonLink href="/start" size="lg" className="group mt-8">
              {t("home.cta")}
              <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
            </ButtonLink>
          </div>
          <p className="mx-auto mt-10 max-w-2xl text-center text-sm leading-relaxed text-muted">{t("home.disclaimer")}</p>
        </section>
      </main>
      <footer className="border-t border-line/70">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-6 text-sm text-muted sm:px-6">
          <span>{t("home.footer", { year: new Date().getFullYear() })}</span>
          <span className="tabular">
            {meta.question_count} · {meta.duration_minutes} · A–F
          </span>
        </div>
      </footer>
    </>
  );
}
