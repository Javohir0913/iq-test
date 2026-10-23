"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { ArrowRight, Check, Keyboard, Refresh, Send, Spinner } from "@/components/icons";
import { Grid3, Star, Triangle } from "@/components/shapes";
import { Button, ButtonLink, Card, Skeleton } from "@/components/ui";
import { useI18n } from "@/i18n";
import { ApiError, api } from "@/lib/api";
import { formatPhone, isPhoneComplete, normalizePhone, phoneDigits } from "@/lib/phone";
import { storage, type StoredAttempt } from "@/lib/storage";
import { useAuth } from "@/lib/auth";
import { useTelegram } from "@/lib/telegram";
import { LoginCard } from "@/components/TelegramLogin";
import { useMeta } from "@/lib/useMeta";

export default function StartPage() {
  const { t, list, lang } = useI18n();
  const meta = useMeta();
  const router = useRouter();
  const { initData } = useTelegram();
  const { status, user, logout } = useAuth();

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [errors, setErrors] = useState<{ name?: string; phone?: string; form?: string }>({});
  const [submitting, setSubmitting] = useState(false);
  const [fromTelegram, setFromTelegram] = useState(false);
  const [resume, setResume] = useState<StoredAttempt | null>(null);

  // Tugallanmagan urinish bo‘lsa – davom ettirish taklifi
  useEffect(() => {
    const cur = storage.current();
    if (!cur) return;
    api
      .questions(cur.id, cur.token)
      .then((d) => (d.status === "in_progress" ? setResume(cur) : storage.clearCurrent(cur.id)))
      .catch(() => {});
  }, []);

  // Telegram akkauntidan ismni to‘ldirish (veb Login Widget yoki Mini App)
  useEffect(() => {
    if (status !== "authed" || !user?.full_name) return;
    setName((prev) => prev || user.full_name);
    setFromTelegram(true);
  }, [status, user]);

  // Kirish majburiy: veb'da Telegram Login, Mini App'da avtomatik
  const needsLogin = meta.auth_required !== false && status === "guest" && !initData;
  const authPending = status === "loading" || (status === "guest" && Boolean(initData));

  const validate = () => {
    const next: typeof errors = {};
    const trimmed = name.trim().replace(/\s+/g, " ");
    if (!trimmed) next.name = t("start.errors.name_required");
    else if (trimmed.length < 2) next.name = t("start.errors.name_short");
    if (phone && !isPhoneComplete(phone)) next.phone = t("start.errors.phone_invalid");
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting || !validate()) return;
    setSubmitting(true);
    try {
      const res = await api.createAttempt({
        full_name: name.trim().replace(/\s+/g, " "),
        phone: normalizePhone(phone),
        language: lang,
        telegram_init_data: initData || undefined,
      });
      storage.saveAttempt(res.attempt_id, res.token);
      router.push(`/test/${res.attempt_id}`);
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : null;
      if (apiErr?.status === 429) setErrors({ form: t("start.errors.rate_limited") });
      else if (apiErr?.status === 400 && apiErr.data.phone) setErrors({ phone: t("start.errors.phone_invalid") });
      else if (apiErr?.status === 400 && apiErr.data.full_name) setErrors({ name: t("start.errors.name_short") });
      else setErrors({ form: t("start.errors.generic") });
      setSubmitting(false);
    }
  };

  const rules = list("start.rules");
  const vars = { count: meta.question_count, minutes: meta.duration_minutes };

  return (
    <>
      <Header />
      <main id="main" className="relative isolate">
        <div className="dot-grid absolute inset-0 -z-10 [mask-image:linear-gradient(to_bottom,black,transparent_60%)]" />
        <div className="mx-auto grid max-w-5xl gap-6 px-4 py-8 sm:px-6 md:py-14 lg:grid-cols-[1.15fr_1fr] lg:gap-8">
          <motion.div initial={{ y: 16 }} animate={{ y: 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}>
            <AnimatePresence>
              {resume && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-4 overflow-hidden"
                >
                  <div className="flex flex-col gap-3 rounded-panel border border-teal/30 bg-teal/[0.08] p-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-semibold">{t("start.resume_title")}</p>
                      <p className="text-sm text-muted">{t("start.resume_text")}</p>
                    </div>
                    <ButtonLink href={`/test/${resume.id}`} variant="dark" size="sm" className="shrink-0">
                      <Refresh size={15} />
                      {t("start.resume_button")}
                    </ButtonLink>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {authPending ? (
              <Skeleton className="h-[420px] !rounded-panel" />
            ) : needsLogin ? (
              <LoginCard />
            ) : (
            <Card className="p-6 sm:p-8">
              <h1 className="text-3xl font-bold tracking-tight">{t("start.title")}</h1>
              <p className="mt-2 text-muted">{t("start.subtitle")}</p>

              <form onSubmit={submit} noValidate className="mt-8 space-y-5">
                <div>
                  <label htmlFor="full_name" className="mb-2 block text-sm font-semibold">
                    {t("start.name_label")}
                  </label>
                  <input
                    id="full_name"
                    name="full_name"
                    autoComplete="name"
                    value={name}
                    maxLength={120}
                    onChange={(e) => {
                      setName(e.target.value);
                      if (errors.name) setErrors((p) => ({ ...p, name: undefined }));
                    }}
                    placeholder={t("start.name_placeholder")}
                    aria-invalid={Boolean(errors.name)}
                    aria-describedby={errors.name ? "name-error" : fromTelegram ? "name-tg" : undefined}
                    className={`h-12 w-full rounded-btn border bg-surface px-4 text-base outline-none transition-[border,box-shadow] placeholder:text-muted/70 focus:border-accent focus:ring-4 focus:ring-accent/15 ${errors.name ? "border-accent" : "border-line"}`}
                  />
                  {errors.name && (
                    <p id="name-error" role="alert" className="mt-1.5 text-sm font-medium text-accent">
                      {errors.name}
                    </p>
                  )}
                  {!errors.name && fromTelegram && (
                    <p id="name-tg" className="mt-1.5 inline-flex items-center gap-1.5 text-sm text-teal">
                      <Send size={14} /> {t("start.telegram_filled")}
                    </p>
                  )}
                </div>

                <div>
                  <label htmlFor="phone" className="mb-2 flex items-baseline gap-2 text-sm font-semibold">
                    {t("start.phone_label")}
                    <span className="text-xs font-normal text-muted">({t("start.optional")})</span>
                  </label>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    inputMode="tel"
                    autoComplete="tel"
                    value={phone}
                    onFocus={() => !phone && setPhone("+998 (")}
                    onBlur={() => phone === "+998 (" && setPhone("")}
                    onChange={(e) => {
                      let raw = e.target.value;
                      // Ajratuvchi belgi o‘chirilsa, undan oldingi raqam ham o‘chiriladi
                      if (raw.length < phone.length && phoneDigits(raw) === phoneDigits(phone)) {
                        const d = phoneDigits(raw);
                        raw = "998" + d.slice(0, -1);
                      }
                      setPhone(phoneDigits(raw).length === 0 ? "+998 (" : formatPhone(raw));
                      if (errors.phone) setErrors((p) => ({ ...p, phone: undefined }));
                    }}
                    placeholder={t("start.phone_placeholder")}
                    aria-invalid={Boolean(errors.phone)}
                    aria-describedby={errors.phone ? "phone-error" : undefined}
                    className={`tabular h-12 w-full rounded-btn border bg-surface px-4 text-base outline-none transition-[border,box-shadow] placeholder:text-muted/70 focus:border-accent focus:ring-4 focus:ring-accent/15 ${errors.phone ? "border-accent" : "border-line"}`}
                  />
                  {errors.phone && (
                    <p id="phone-error" role="alert" className="mt-1.5 text-sm font-medium text-accent">
                      {errors.phone}
                    </p>
                  )}
                </div>

                {errors.form && (
                  <p role="alert" className="rounded-btn border border-accent/30 bg-accent/10 px-4 py-3 text-sm font-medium text-accent">
                    {errors.form}
                  </p>
                )}

                <Button type="submit" size="lg" className="group w-full" disabled={submitting}>
                  {submitting ? (
                    <>
                      <Spinner /> {t("start.submitting")}
                    </>
                  ) : (
                    <>
                      {t("start.submit")}
                      <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
                    </>
                  )}
                </Button>
              </form>
              {status === "authed" && user && !initData && (
                <p className="mt-5 flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-center text-sm text-muted">
                  <span>{t("auth.signed_in_as", { name: user.full_name || user.username })}</span>
                  <button type="button" onClick={logout} className="focus-ring rounded font-semibold text-ink underline-offset-4 hover:underline">
                    {t("auth.logout")}
                  </button>
                </p>
              )}
            </Card>
            )}
          </motion.div>

          <motion.aside
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="relative overflow-hidden rounded-panel border border-line bg-panel p-6 sm:p-8"
          >
            <div aria-hidden className="absolute -right-4 -top-4 flex gap-2 text-ink/[0.08]">
              <Star points={4} inner={0.4} size={70} />
            </div>
            <h2 className="text-lg font-bold tracking-tight">{t("start.rules_title")}</h2>
            <ul className="mt-5 space-y-3.5">
              {rules.map((_, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + i * 0.06 }}
                  className="flex gap-3 text-[15px] leading-relaxed"
                >
                  <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-ink text-page">
                    <Check size={13} strokeWidth={3} />
                  </span>
                  <span>{t(`start.rules.${i}`, vars)}</span>
                </motion.li>
              ))}
            </ul>
            <div className="mt-6 flex items-start gap-3 rounded-card border border-line bg-surface p-4 text-sm text-muted">
              <Keyboard size={18} className="mt-0.5 shrink-0 text-ink" />
              <span>{t("start.keyboard")}</span>
            </div>
            <div aria-hidden className="mt-6 flex items-center gap-3 text-ink/70">
              <Triangle size={22} className="text-teal" />
              <Grid3 size={26} filled={[4]} accent={8} />
              <Star points={5} size={22} className="text-soft" />
            </div>
          </motion.aside>
        </div>
      </main>
    </>
  );
}
